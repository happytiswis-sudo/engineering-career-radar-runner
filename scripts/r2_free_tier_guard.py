#
# Post-migration account-wide usage verification checkpoint: 2026-11-17.
#!/usr/bin/env python3
"""Fail-closed Cloudflare R2 Standard free-tier guardian.

Reads account-wide Cloudflare R2 analytics and account metrics, then publishes a
short-lived HMAC-authenticated admission report to the private Bridge. Unknown,
stale, incomplete, sampled/truncated or over-budget evidence denies admission.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

GB = 1_000_000_000
STORAGE_LIMIT_BYTES = 7 * GB          # 70% of the 10 GB-month free allowance
CLASS_A_LIMIT = 700_000               # 70% of the 1,000,000 monthly allowance
CLASS_B_LIMIT = 7_000_000             # 70% of the 10,000,000 monthly allowance
MAX_GROUPS = 10_000
MAX_SAMPLE_AGE_HOURS = 48

CLASS_A = {
    "ListBuckets", "PutBucket", "ListObjects", "PutObject", "CopyObject",
    "CompleteMultipartUpload", "CreateMultipartUpload",
    "LifecycleStorageTierTransition", "ListMultipartUploads", "UploadPart",
    "UploadPartCopy", "ListParts", "PutBucketEncryption", "PutBucketCors",
    "PutBucketLifecycleConfiguration",
}
CLASS_B = {
    "HeadBucket", "HeadObject", "GetObject", "UsageSummary",
    "GetBucketEncryption", "GetBucketLocation", "GetBucketCors",
    "GetBucketLifecycleConfiguration",
}
FREE = {"DeleteObject", "DeleteBucket", "AbortMultipartUpload"}


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def cloudflare_error_summary(payload: object) -> str:
    """Return bounded Cloudflare error codes/messages without request headers or secrets."""
    if not isinstance(payload, dict):
        return "non-JSON or unexpected response"
    errors = payload.get("errors")
    if not isinstance(errors, list) or not errors:
        return "Cloudflare returned success=false without structured errors"
    parts = []
    for item in errors[:5]:
        if not isinstance(item, dict):
            continue
        code = item.get("code")
        message = item.get("message")
        if isinstance(message, str):
            message = " ".join(message.split())[:180]
        else:
            message = "unspecified error"
        parts.append((("code " + str(code) + ": ") if code is not None else "") + message)
    return "; ".join(parts)[:700] or "Cloudflare returned an unspecified API error"


def cloudflare_request(url: str, token: str, method: str = "GET", body: dict | None = None,
                      graphql: bool = False) -> dict:
    raw = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    headers = {"Authorization": "Bearer " + token, "Accept": "application/json",
               "User-Agent": "CareerRadar-R2-Guardian/1.0"}
    if raw is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=raw, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            error_payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            error_payload = None
        raise RuntimeError("Cloudflare HTTP " + str(exc.code) + ": " + cloudflare_error_summary(error_payload)) from None
    except urllib.error.URLError as exc:
        raise RuntimeError("Cloudflare network request failed: " + type(exc.reason).__name__) from None
    if graphql:
        # Cloudflare's GraphQL Analytics API uses the GraphQL response shape
        # {data, errors}; unlike REST it does not return success: true.
        if not isinstance(payload, dict):
            raise RuntimeError("Cloudflare GraphQL returned a non-object response")
        errors = payload.get("errors")
        if errors:
            raise RuntimeError("Cloudflare GraphQL returned errors: " + cloudflare_error_summary({"errors": errors}))
        if payload.get("data") is None:
            raise RuntimeError("Cloudflare GraphQL response omitted data")
        return payload

    # Cloudflare REST endpoints use the standard {success, errors, result} envelope.
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise RuntimeError("Cloudflare API rejected request: " + cloudflare_error_summary(payload))
    return payload


def graphql_query(account_id: str, token: str, operations_start: dt.datetime,
                  storage_start: dt.datetime, end: dt.datetime) -> tuple[list, list]:
    endpoint = "https://api.cloudflare.com/client/v4/graphql"
    operations_start_s, storage_start_s, end_s = iso(operations_start), iso(storage_start), iso(end)
    query = """
    query {
      viewer {
        accounts(filter: {accountTag: "%s"}) {
          r2OperationsAdaptiveGroups(
            limit: 10000
            filter: {datetime_geq: "%s", datetime_leq: "%s"}
          ) {
            sum { requests }
            dimensions { actionType }
          }
          r2StorageAdaptiveGroups(
            limit: 10000
            filter: {datetime_geq: "%s", datetime_leq: "%s"}
            orderBy: [datetime_DESC]
          ) {
            max { payloadSize metadataSize objectCount uploadCount }
            dimensions { bucketName datetime }
          }
        }
      }
    }
    """ % (account_id, operations_start_s, end_s, storage_start_s, end_s)
    payload = cloudflare_request(endpoint, token, "POST", {"query": query}, graphql=True)
    if payload.get("errors"):
        raise RuntimeError("Cloudflare GraphQL returned errors")
    accounts = (((payload.get("data") or {}).get("viewer") or {}).get("accounts") or [])
    if len(accounts) != 1 or not isinstance(accounts[0], dict):
        raise RuntimeError("Cloudflare GraphQL did not return exactly one account")
    account = accounts[0]
    operations = account.get("r2OperationsAdaptiveGroups")
    storage = account.get("r2StorageAdaptiveGroups")
    if not isinstance(operations, list) or not isinstance(storage, list):
        raise RuntimeError("Cloudflare GraphQL omitted an R2 dataset")
    if not operations or not storage or len(operations) >= MAX_GROUPS or len(storage) >= MAX_GROUPS:
        raise RuntimeError("R2 metrics are empty or reached the 10,000-row safety cap")
    return operations, storage


def classify_operations(rows: list[dict]) -> tuple[int, int, list[str]]:
    class_a = class_b = 0
    unknown: set[str] = set()
    for row in rows:
        dimensions = row.get("dimensions") or {}
        action = dimensions.get("actionType")
        requests = (row.get("sum") or {}).get("requests")
        if not isinstance(action, str) or not isinstance(requests, (int, float)) or requests < 0:
            unknown.add("malformed_operation_group")
            continue
        count = int(requests)
        if action in CLASS_A:
            class_a += count
        elif action in CLASS_B:
            class_b += count
        elif action in FREE:
            continue
        else:
            unknown.add(action[:100])
    return class_a, class_b, sorted(unknown)


def storage_peak_bytes(rows: list[dict]) -> tuple[int, str, int]:
    by_bucket: dict[str, int] = {}
    latest_by_bucket: dict[str, dt.datetime] = {}
    for row in rows:
        dimensions = row.get("dimensions") or {}
        bucket = dimensions.get("bucketName")
        timestamp = dimensions.get("datetime")
        maximum = row.get("max") or {}
        payload = maximum.get("payloadSize")
        metadata = maximum.get("metadataSize")
        upload_count = maximum.get("uploadCount")
        object_count = maximum.get("objectCount")
        if not isinstance(bucket, str) or not bucket or not isinstance(timestamp, str):
            raise RuntimeError("Malformed R2 storage dimensions")
        if any(type(value) not in (int, float) or value < 0
               for value in (payload, metadata, upload_count, object_count)):
            raise RuntimeError("Incomplete R2 storage size or object metrics")
        if upload_count > 0:
            raise RuntimeError("Pending multipart uploads make account storage usage uncertain")
        try:
            parsed = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
        except ValueError as exc:
            raise RuntimeError("Invalid R2 storage timestamp") from exc
        latest_by_bucket[bucket] = max(latest_by_bucket.get(bucket, parsed), parsed)
        by_bucket[bucket] = max(by_bucket.get(bucket, 0), int(payload) + int(metadata))
    if not by_bucket:
        raise RuntimeError("No account-wide R2 storage samples were returned")
    now = utc_now()
    for bucket, latest in latest_by_bucket.items():
        age = now - latest
        if age > dt.timedelta(hours=MAX_SAMPLE_AGE_HOURS) or age < dt.timedelta(minutes=-5):
            raise RuntimeError("R2 storage metrics are stale or timestamped in the future for a bucket")
    latest = max(latest_by_bucket.values())
    # The maximum footprint observed for every bucket during the current month,
    # summed across buckets, is a conservative upper bound for GB-month usage.
    return sum(by_bucket.values()), iso(latest), len(by_bucket)


def current_account_storage(account_id: str, token: str) -> tuple[int, int]:
    url = "https://api.cloudflare.com/client/v4/accounts/" + urllib.parse.quote(account_id, safe="") + "/r2/metrics"
    payload = cloudflare_request(url, token)
    result = payload.get("result") or {}
    standard = result.get("standard") or {}
    infrequent = result.get("infrequentAccess") or {}
    def amount(section: dict, label: str) -> int:
        if not isinstance(section, dict):
            raise RuntimeError("Cloudflare account metrics omitted " + label + " storage class")
        total = 0
        for state in ("published", "uploaded"):
            value = section.get(state)
            if not isinstance(value, dict):
                raise RuntimeError("Cloudflare account metrics omitted " + label + "/" + state)
            for field in ("payloadSize", "metadataSize", "objects"):
                number = value.get(field)
                if type(number) not in (int, float) or number < 0:
                    raise RuntimeError("Cloudflare account metrics omitted " + label + "/" + state + "/" + field)
                total += int(number) if field != "objects" else 0
        return total
    standard_bytes = amount(standard, "standard")
    infrequent_bytes = amount(infrequent, "infrequentAccess")
    if standard_bytes <= 0 and infrequent_bytes <= 0:
        raise RuntimeError("Cloudflare account metrics returned no storage totals")
    return standard_bytes, infrequent_bytes


def evaluate(report: dict) -> bool:
    try:
        if report.get("metrics_complete") is not True or report.get("admitted") is not True:
            return False
        if report.get("unknown_operations") != [] or report.get("storage_class") != "standard_only":
            return False
        values = (
            report["storage_peak_bytes"],
            report["class_a_operations_month_to_date"],
            report["class_b_operations_month_to_date"],
        )
        if any(type(value) is not int or value < 0 for value in values):
            return False
        return (
            report["storage_peak_bytes"] < STORAGE_LIMIT_BYTES
            and report["class_a_operations_month_to_date"] < CLASS_A_LIMIT
            and report["class_b_operations_month_to_date"] < CLASS_B_LIMIT
        )
    except (KeyError, TypeError):
        return False


def publish_report(bridge: str, ci_token: str, dashboard_key: str, report: dict) -> None:
    canonical = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(ci_token.encode(), canonical, hashlib.sha256).hexdigest()
    body = json.dumps({"report": report, "signature": signature}, separators=(",", ":")).encode()
    request = urllib.request.Request(
        bridge.rstrip("/") + "/archives/guardian",
        data=body,
        headers={
            "X-Archive-CI-Token": ci_token,
            "X-Dashboard-Key": dashboard_key,
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "User-Agent": "CareerRadar-R2-Guardian/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("stored") or result.get("schema_version") != 1:
        raise RuntimeError("Bridge did not confirm storage of the signed R2 guardian report")


def main() -> int:
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    report_account_id = account_id or "02e8abc1853165520174d6a71b3a8b2d"
    api_token = os.environ.get("R2_GUARD_API_TOKEN", "").strip()
    ci_token = os.environ.get("ARCHIVE_CI_TOKEN", "").strip()
    dashboard_key = os.environ.get("DASHBOARD_API_KEY", "").strip()
    bridge = os.environ.get("BRIDGE_URL", "https://career-radar-bridge.happytiswis.workers.dev").strip()
    now = utc_now()
    # R2 free-tier operation quotas reset monthly. Query month-to-date in UTC;
    # the storage peak over the same period is a conservative GB-month upper bound.
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    operations_start = month_start
    storage_start = month_start
    report = {
        "schema_version": 1,
        "account_id": report_account_id,
        "observed_at": iso(now),
        "metrics_complete": False,
        "admitted": False,
        "storage_class": "unknown",
        "storage_peak_bytes": None,
        "class_a_operations_month_to_date": None,
        "class_b_operations_month_to_date": None,
        "unknown_operations": ["metrics_unavailable"],
        "latest_storage_sample_at": None,
        "account_bucket_count": 0,
        "guardian_error": None,
    }
    try:
        if not account_id or not ci_token or not dashboard_key:
            raise RuntimeError("CLOUDFLARE_ACCOUNT_ID, ARCHIVE_CI_TOKEN and DASHBOARD_API_KEY are required")
        if not api_token:
            raise RuntimeError("R2_GUARD_API_TOKEN is missing; create a dedicated Cloudflare token with Account Analytics:Read and Workers R2 Storage Read")
        operations, storage = graphql_query(account_id, api_token, operations_start, storage_start, now)
        class_a, class_b, unknown = classify_operations(operations)
        peak, latest, bucket_count = storage_peak_bytes(storage)
        current_standard, current_infrequent = current_account_storage(account_id, api_token)
        if current_infrequent > 0:
            raise RuntimeError("Infrequent Access storage is present; its usage is not covered by the Standard free tier")
        if current_standard > peak:
            raise RuntimeError("Current account storage exceeds the historical GraphQL peak; metrics are incomplete")
        report.update({
            "metrics_complete": not unknown,
            "admitted": not unknown and peak < STORAGE_LIMIT_BYTES and class_a < CLASS_A_LIMIT and class_b < CLASS_B_LIMIT,
            "storage_class": "standard_only" if current_infrequent == 0 else "mixed",
            "storage_peak_bytes": peak,
            "class_a_operations_month_to_date": class_a,
            "class_b_operations_month_to_date": class_b,
            "unknown_operations": unknown,
            "latest_storage_sample_at": latest,
            "account_bucket_count": bucket_count,
        })
    except Exception as exc:
        # Publish a bounded diagnostic with any configured credentials redacted.
        diagnostic = (str(exc) or type(exc).__name__)[:500]
        for secret in (api_token, ci_token, dashboard_key):
            if secret:
                diagnostic = diagnostic.replace(secret, "[redacted]")
        report["guardian_error"] = diagnostic
        report["unknown_operations"] = ["guardian_error:" + type(exc).__name__]
        print("R2 guardian denied admission: " + diagnostic, file=sys.stderr)

    if not ci_token:
        raise SystemExit("ARCHIVE_CI_TOKEN is required to publish the fail-closed guardian report")
    try:
        publish_report(bridge, ci_token, dashboard_key, report)
    except Exception as exc:
        raise SystemExit("Could not publish the signed R2 guardian report: " + type(exc).__name__) from exc

    admitted = evaluate(report)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as stream:
            stream.write("r2_write_admitted=" + ("true" if admitted else "false") + "\n")
    print(json.dumps({
        "admitted": admitted,
        "metrics_complete": report["metrics_complete"],
        "storage_peak_gb_upper_bound": round((report["storage_peak_bytes"] or 0) / GB, 6),
        "class_a_operations_month_to_date": report["class_a_operations_month_to_date"],
        "class_b_operations_month_to_date": report["class_b_operations_month_to_date"],
        "unknown_operation_count": len(report["unknown_operations"]),
        "guardian_error": report["guardian_error"],
        "account_bucket_count": report["account_bucket_count"],
        "observed_at": report["observed_at"],
    }, sort_keys=True))
    return 0 if admitted else 1


if __name__ == "__main__":
    raise SystemExit(main())
