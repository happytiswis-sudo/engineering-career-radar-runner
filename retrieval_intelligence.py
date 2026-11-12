"""Privacy-safe retrieval telemetry, adaptive allocation, and source diagnostics.

This module intentionally has no CV, Roles, credentials, network, or storage access.
It measures collection quality independently from CV/job matching.
"""
from __future__ import annotations

from collections import defaultdict
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_TRACKING_KEYS = {
    "ref", "referrer", "source", "src", "trk", "tracking", "gh_src",
    "fbclid", "gclid", "mc_cid", "mc_eid", "campaign", "utm_campaign",
    "utm_medium", "utm_source", "utm_term", "utm_content",
}


def canonical_url(raw: object) -> str:
    """Normalize URL transport noise while preserving requisition identifiers."""
    parsed = urlparse(str(raw or "").strip())
    if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
        return ""
    host = parsed.hostname.lower().removeprefix("www.")
    port = parsed.port
    netloc = host if not port or (parsed.scheme.lower(), port) in (("http", 80), ("https", 443)) else f"{host}:{port}"
    query = sorted(
        (key.lower(), value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in _TRACKING_KEYS and not key.lower().startswith("utm_")
    )
    return urlunparse(("https", netloc, parsed.path.rstrip("/") or "/", "", urlencode(query), ""))


def _usable(job: object) -> bool:
    if not isinstance(job, dict):
        return False
    return bool(
        str(job.get("title") or "").strip()
        and str(job.get("company") or "").strip()
        and canonical_url(job.get("url"))
    )


def measure_source_outcomes(outcomes: list[dict], previously_seen: set[str] | None = None) -> dict:
    """Count each retrieval stage without conflating raw rows and vacancies.

    Each outcome may contain source, family, attempted_queries, completed_queries,
    failed_queries, raw_urls (or raw_rows), and postings. A posting is usable
    only when it has a title, employer, and valid HTTP(S) URL.
    """
    seen_before = {canonical_url(value) for value in (previously_seen or ()) if canonical_url(value)}
    totals = defaultdict(int)
    sources = {}
    all_unique = set()
    all_usable = set()
    all_new = set()
    for outcome in outcomes or []:
        if not isinstance(outcome, dict):
            continue
        source = str(outcome.get("source") or outcome.get("type") or "unknown")
        row = sources.setdefault(source, {
            "source": source, "family": str(outcome.get("family") or source),
            "attempted_queries": 0, "completed_queries": 0, "failed_queries": 0,
            "raw_urls_encountered": 0, "unique_canonical_urls": 0,
            "usable_postings": 0, "newly_discovered_vacancies": 0,
        })
        for key in ("attempted_queries", "completed_queries", "failed_queries"):
            row[key] += max(0, int(outcome.get(key) or 0))
        postings = outcome.get("postings") or []
        raw_urls = outcome.get("raw_urls")
        if raw_urls is None:
            raw_urls = [p.get("url") for p in postings if isinstance(p, dict)]
        row["raw_urls_encountered"] += len(raw_urls)
        local = set()
        for raw in raw_urls:
            url = canonical_url(raw)
            if url:
                local.add(url)
        row["unique_canonical_urls"] += len(local)
        all_unique.update(local)
        usable = set()
        for posting in postings:
            if _usable(posting):
                usable.add(canonical_url(posting["url"]))
        row["usable_postings"] += len(usable)
        all_usable.update(usable)
        new = usable - seen_before
        row["newly_discovered_vacancies"] += len(new)
        all_new.update(new)
    for row in sources.values():
        attempted = row["attempted_queries"]
        row["usable_per_query"] = round(row["usable_postings"] / attempted, 4) if attempted else 0.0
        row["unique_url_per_query"] = round(row["unique_canonical_urls"] / attempted, 4) if attempted else 0.0
    return {
        "sources": sources,
        "totals": {
            "raw_urls_encountered": sum(x["raw_urls_encountered"] for x in sources.values()),
            "unique_canonical_urls": len(all_unique),
            "usable_postings": len(all_usable),
            "newly_discovered_vacancies": len(all_new),
        },
    }


def allocate_query_capacity(sources: list[dict], total_budget: int,
                            family_floor: int = 1) -> dict:
    """Allocate bounded query capacity by observed yield with family fairness."""
    budget = max(0, int(total_budget))
    floor = max(0, int(family_floor))
    eligible = [dict(s) for s in (sources or []) if s.get("enabled", True)]
    result = {str(s.get("source") or s.get("family") or "unknown"): 0 for s in eligible}
    if not eligible or not budget:
        return {"allocations": result, "unused_budget": budget, "method": "no_eligible_sources"}
    by_family = defaultdict(list)
    for source in eligible:
        by_family[str(source.get("family") or source.get("source") or "unknown")].append(source)
    for family in sorted(by_family):
        if budget <= 0:
            break
        source = sorted(by_family[family], key=lambda x: str(x.get("source") or ""))[0]
        key = str(source.get("source") or family)
        grant = min(floor, max(0, int(source.get("max_queries", total_budget))), budget)
        result[key] += grant
        budget -= grant
    while budget:
        best = None
        for source in eligible:
            key = str(source.get("source") or source.get("family") or "unknown")
            remaining = max(0, int(source.get("max_queries", total_budget))) - result.get(key, 0)
            if remaining <= 0:
                continue
            attempted = max(0, int(source.get("attempted_queries") or 0))
            usable = max(0, int(source.get("usable_postings") or 0))
            observed_yield = (usable + 1.0) / (attempted + 2.0)
            score = observed_yield / (1 + result.get(key, 0))
            candidate = (score, key)
            if best is None or candidate[0] > best[0] or (candidate[0] == best[0] and candidate[1] < best[1]):
                best = candidate
        if best is None:
            break
        result[best[1]] += 1
        budget -= 1
    return {"allocations": result, "unused_budget": budget,
            "method": "family_floor_then_diminishing_smoothed_yield"}

def diagnose_sources(sources: list[dict], *, low_yield_per_query: float = 0.25,
                     stale_after_days: int = 14) -> list[dict]:
    """Produce actionable, deterministic source-family diagnostics.

    Expected fields include status, attempted_queries, usable_postings,
    last_success_days, credential_required, credential_present, error_code.
    """
    findings = []
    for source in sources or []:
        if not isinstance(source, dict):
            continue
        name = str(source.get("source") or source.get("family") or "unknown")
        family = str(source.get("family") or name)
        attempted = max(0, int(source.get("attempted_queries") or 0))
        usable = max(0, int(source.get("usable_postings") or 0))
        status = str(source.get("status") or "").lower()
        required = bool(source.get("credential_required"))
        present = bool(source.get("credential_present"))
        days = source.get("last_success_days")
        error = str(source.get("error_code") or "").upper()
        if required and not present:
            findings.append({"source": name, "family": family, "severity": "blocker",
                "signal": "missing_credential", "recommendation": "Configure the required provider credential in the trusted private workflow; never expose it to fork PRs."})
        if error in ("401", "403"):
            findings.append({"source": name, "family": family, "severity": "high",
                "signal": "provider_auth_or_permission_failure", "recommendation": "Verify credential scope and provider access; do not retry around a denial."})
        elif error == "429":
            findings.append({"source": name, "family": family, "severity": "high",
                "signal": "provider_rate_limited", "recommendation": "Honor Retry-After and reduce concurrency or request frequency."})
        elif error == "404":
            findings.append({"source": name, "family": family, "severity": "medium",
                "signal": "stale_or_invalid_board", "recommendation": "Revalidate the employer ATS board URL and remove or quarantine it if the board no longer exists."})
        if days is not None:
            try:
                stale = float(days) >= stale_after_days
            except (TypeError, ValueError):
                stale = False
            if stale:
                findings.append({"source": name, "family": family, "severity": "medium",
                    "signal": "stale_source", "recommendation": "Probe the public board endpoint and refresh its ATS metadata before allocating more capacity."})
        if attempted and usable / attempted < low_yield_per_query:
            findings.append({"source": name, "family": family, "severity": "low",
                "signal": "low_usable_yield", "recommendation": "Inspect query relevance, pagination, parsing and URL validity; keep the family fairness floor while shifting only its discretionary capacity."})
        if status in ("failed", "error", "unconfigured"):
            findings.append({"source": name, "family": family, "severity": "high" if status != "unconfigured" else "medium",
                "signal": "source_not_operational", "recommendation": "Resolve the recorded failure or credential/configuration state, then run a bounded health probe."})
    return findings
