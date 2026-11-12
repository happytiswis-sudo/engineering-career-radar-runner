"""Conservative quality gates for vacancy freshness and geography.

The gates are transparent and evidence-based. They do not infer that an unknown
publication date is recent, and they preserve worldwide searches when requested.
"""
from __future__ import annotations
from datetime import datetime, timezone
from career_intelligence import published_on


def freshness_gate(job, now=None):
    """Return a freshness decision; only hard-expire evidence older than 90d.

    31-90 day postings require an active-source check; unknown dates remain
    review-only rather than receiving a recency bonus.
    """
    now = now or datetime.now(timezone.utc)
    evidence = published_on(job.get("published_at"), now=now)
    age = evidence.get("age_days")
    explicit_expiry = job.get("listing_status") == "expired_by_source_date"
    source_inactive = (job.get("source_verification") or {}).get("status") == "inactive"
    if explicit_expiry or source_inactive:
        action = "exclude"
        reason = "source_expiry_confirmed" if explicit_expiry else "source_page_inactive"
    elif age is None:
        action = "review"
        reason = "publication_date_unknown"
    elif age > 90 and job.get("source_active_verified") is not True:
        action = "exclude"
        reason = "older_than_90d_without_active_source_verification"
    elif age > 30 and job.get("source_active_verified") is not True:
        action = "verify"
        reason = "older_than_30d_requires_source_verification"
    else:
        action = "keep"
        reason = "fresh_or_source_verified"
    return {"action": action, "reason": reason, "age_days": age,
            "bucket": evidence.get("bucket"), "label": evidence.get("label")}


def geographic_gate(job, market, world_search=False):
    """Keep Germany jobs by default; world search explicitly relaxes this gate.

    Remote jobs pass only when Germany is named in their location evidence.
    """
    if world_search:
        return {"keep": True, "reason": "world_search_requested"}
    market = market if isinstance(market, dict) else {}
    if market.get("germany") is True:
        return {"keep": True, "reason": "germany_location_evidence"}
    location = " ".join(str(job.get("location") or "").casefold().split())
    restrictions = job.get("remote_location_restriction") or []
    if isinstance(restrictions, str):
        restrictions = [restrictions]
    restriction_text = " ".join(str(x).casefold() for x in restrictions)
    germany_tokens = ("germany", "deutschland", "de")
    explicit_germany_remote = bool(job.get("remote")) and any(
        token in location or token in restriction_text for token in germany_tokens)
    if explicit_germany_remote:
        return {"keep": True, "reason": "remote_germany_explicit"}
    return {"keep": False, "reason": "outside_or_unverified_germany"}


def employer_evidence_state(company):
    """Separate official-site evidence from discovery snippets."""
    company = company if isinstance(company, dict) else {}
    verified = company.get("verification_status") in (
        "website_verified", "website_and_careers_checked")
    careers_checked = company.get("career_status") in (
        "vacancies_found", "checked_no_openings", "careers_page_found_no_jobs")
    vacancy_links = company.get("career_status") == "vacancies_found" and bool(
        company.get("vacancy_urls"))
    return {"website_verified": verified, "careers_checked": careers_checked,
            "vacancy_links_verified": vacancy_links,
            "state": "vacancy_links_verified" if vacancy_links else
                     "careers_page_checked" if careers_checked else
                     "official_website_checked" if verified else "discovery_only"}


def record_http_cooldown(state, board, status, retry_after="", now=None):
    """Persist source-specific 429/404 recovery without retrying during cooldown."""
    from email.utils import parsedate_to_datetime
    from datetime import timedelta
    import datetime as dt
    if not isinstance(state, dict) or not isinstance(board, dict):
        return state
    now = now or datetime.now(timezone.utc)
    status = int(status)
    if status not in (404, 429):
        return state
    if status == 404:
        delay = 30 * 24 * 60 * 60
    else:
        delay = 60 * 60
        raw = str(retry_after or "").strip()
        try:
            delay = max(60, min(72 * 60 * 60, int(raw)))
        except (TypeError, ValueError):
            try:
                retry_at = parsedate_to_datetime(raw)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                delay = max(60, min(72 * 60 * 60, int((retry_at-now).total_seconds())))
            except (TypeError, ValueError, OverflowError):
                pass
    key = (str(board.get("type") or "") + "|" + str(board.get("slug") or "")).casefold()
    state[key] = {"type": str(board.get("type") or ""),
        "slug": str(board.get("slug") or "")[:100],
        "reason": "http_" + str(status),
        "last_failure_at": now.isoformat(timespec="seconds"),
        "retry_after": (now + timedelta(seconds=delay)).isoformat(timespec="seconds")}
    return state
