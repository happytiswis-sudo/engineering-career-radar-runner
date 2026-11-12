#!/usr/bin/env python3
"""Read-only audit of URL collisions in one immutable Career Radar archive.

The Supabase persistence RPC currently keys rows by lower(trim(job_url)).
This script uses that exact key to reveal when multiple shortlisted records
would occupy one Supabase row. It never uploads, edits or deletes data.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit



def _clean(value: object) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _url_host(raw_url: str) -> str:
    try:
        parsed = urlsplit(raw_url)
        return (parsed.hostname or "").lower()
    except ValueError:
        return "[unparseable host]"


def audit_url_collisions(jobs: list[dict]) -> dict:
    groups: dict[str, list[dict]] = {}
    missing_url = 0
    for job in jobs:
        if not isinstance(job, dict):
            continue
        raw_url = str(job.get("url") or "").strip()
        if not raw_url:
            missing_url += 1
            continue
        # Match the current database conflict expression exactly.
        key = raw_url.lower()
        groups.setdefault(key, []).append(job)

    duplicates = []
    for key, rows in groups.items():
        if len(rows) < 2:
            continue
        companies = sorted({_clean(row.get("company")) for row in rows if _clean(row.get("company"))})
        titles = sorted({_clean(row.get("title")) for row in rows if _clean(row.get("title"))})
        locations = sorted({_clean(row.get("location")) for row in rows if _clean(row.get("location"))})
        posting_ids = sorted({
            str(row.get("employer_posting_id") or "").strip()
            for row in rows if str(row.get("employer_posting_id") or "").strip()
        })
        signatures = {
            (
                _clean(row.get("company")),
                _clean(row.get("title")),
                _clean(row.get("location")),
                str(row.get("employer_posting_id") or "").strip(),
            )
            for row in rows
        }
        sources = sorted({
            str(row.get("source") or "Unknown").strip()[:100]
            for row in rows
        })
        duplicates.append({
            "url_fingerprint": hashlib.sha256(key.encode("utf-8")).hexdigest()[:16],
            "url_host": _url_host(key),
            "record_count": len(rows),
            "distinct_vacancy_signatures": len(signatures),
            "companies": companies,
            "titles": titles,
            "locations": locations,
            "posting_ids": posting_ids,
            "sources": sources,
            "records": [
                {
                    "company": str(row.get("company") or "")[:120],
                    "title": str(row.get("title") or "")[:180],
                    "location": str(row.get("location") or "")[:120],
                    "source": str(row.get("source") or "Unknown")[:100],
                    "employer_posting_id": str(row.get("employer_posting_id") or "")[:100],
                }
                for row in rows
            ],
        })

    duplicates.sort(
        key=lambda row: (
            -row["distinct_vacancy_signatures"],
            -row["record_count"],
            row["url_fingerprint"],
        )
    )
    duplicate_records = sum(row["record_count"] for row in duplicates)
    excess_records = sum(row["record_count"] - 1 for row in duplicates)
    return {
        "input_records": len(jobs),
        "url_key_groups": len(groups),
        "missing_url_records": missing_url,
        "duplicate_url_groups": len(duplicates),
        "records_in_duplicate_groups": duplicate_records,
        "excess_records_collapsed_by_url_key": excess_records,
        "groups_with_multiple_vacancy_signatures": sum(
            row["distinct_vacancy_signatures"] > 1 for row in duplicates
        ),
        "groups_with_multiple_companies": sum(len(row["companies"]) > 1 for row in duplicates),
        "groups_with_multiple_titles": sum(len(row["titles"]) > 1 for row in duplicates),
        "groups_with_multiple_locations": sum(len(row["locations"]) > 1 for row in duplicates),
        "groups_with_multiple_posting_ids": sum(len(row["posting_ids"]) > 1 for row in duplicates),
        "collisions": duplicates,
    }


def main() -> None:
    request_path = os.environ.get("AUDIT_REQUEST_FILE", "")
    token = os.environ.get("HF_TOKEN", "")
    space = os.environ.get("HF_SPACE_ID", "")
    if not request_path or not token or not space:
        raise RuntimeError("AUDIT_REQUEST_FILE, HF_TOKEN and HF_SPACE_ID are required")

    from huggingface_hub import hf_hub_download

    request = json.loads(Path(request_path).read_text(encoding="utf-8"))
    run_id = str(request.get("expected_run_id") or "")
    if not run_id.isdigit():
        raise ValueError("Request must contain a numeric expected_run_id")
    expected_count = int(request.get("expected_shortlisted_jobs") or 0)
    expected_db_rows = int(request.get("observed_supabase_rows") or 0)

    archive_name = "history/run-" + run_id + ".json"
    archive_path = hf_hub_download(
        repo_id=space,
        filename=archive_name,
        repo_type="space",
        token=token,
    )
    archive_bytes = Path(archive_path).read_bytes()
    archive = json.loads(archive_bytes.decode("utf-8"))
    if not isinstance(archive, dict) or str(archive.get("run_id") or "") != run_id:
        raise RuntimeError("Archived run ID does not match the audit request")
    jobs = archive.get("jobs")
    if not isinstance(jobs, list):
        raise RuntimeError("Archive has no jobs list")
    if expected_count and len(jobs) != expected_count:
        raise RuntimeError(
            "Archive count mismatch: expected "
            + str(expected_count) + ", found " + str(len(jobs))
        )

    result = audit_url_collisions(jobs)
    compressed_bytes = len(gzip.compress(archive_bytes, compresslevel=6, mtime=0))
    result["archive_bytes"] = len(archive_bytes)
    result["gzip_estimate_bytes"] = compressed_bytes
    result["gzip_estimated_reduction_percent"] = round(
        (1 - compressed_bytes / max(1, len(archive_bytes))) * 100, 1
    )
    result["run_id"] = run_id
    result["archive_file"] = archive_name
    result["observed_supabase_rows"] = expected_db_rows
    result["published_minus_supabase_rows"] = len(jobs) - expected_db_rows
    result["database_count_matches_unique_url_groups"] = (
        not expected_db_rows or expected_db_rows == result["url_key_groups"]
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        summary = [
            "## Read-only URL collision audit",
            "",
            "| Metric | Result |",
            "|---|---:|",
            "| Archive records | " + str(result["input_records"]) + " |",
            "| URL-key groups | " + str(result["url_key_groups"]) + " |",
            "| Archive size | " + str(result["archive_bytes"]) + " bytes |",
            "| Gzip estimate (not uploaded) | " + str(result["gzip_estimate_bytes"]) + " bytes |",
            "| Estimated gzip reduction | " + str(result["gzip_estimated_reduction_percent"]) + "% |",
            "| Duplicate URL groups | " + str(result["duplicate_url_groups"]) + " |",
            "| Excess records sharing a URL key | " + str(result["excess_records_collapsed_by_url_key"]) + " |",
            "| Groups with multiple vacancy signatures | " + str(result["groups_with_multiple_vacancy_signatures"]) + " |",
            "| Groups with multiple locations | " + str(result["groups_with_multiple_locations"]) + " |",
            "| Supabase rows observed | " + str(expected_db_rows) + " |",
            "| Published minus Supabase rows | " + str(result["published_minus_supabase_rows"]) + " |",
            "",
            "Gzip is a measurement only; no archive is rewritten. Full collision detail is in this workflow's log. URL query values are not printed.",
            "",
        ]
        with Path(summary_path).open("a", encoding="utf-8") as handle:
            handle.write("\n".join(summary))


if __name__ == "__main__":
    main()
