"""Bounded SerpApi Google Jobs adapter with pagination and safe telemetry."""
from __future__ import annotations
import os
from urllib.parse import urlencode
from retrieval_intelligence import canonical_url

def fetch_google_jobs(board, request_json):
    """Fetch a bounded page window for each query; never log credential-bearing URLs.

    request_json is injected so tests remain offline. SerpApi returns up to ten
    results per page and exposes the continuation token in serpapi_pagination.
    """
    key = str(os.environ.get("SERPAPI_API_KEY") or "").strip()
    if not key:
        raise ValueError("SerpApi requires SERPAPI_API_KEY")
    queries = [str(q).strip() for q in (board.get("queries") or []) if str(q).strip()]
    query_budget = max(1, min(12, int(board.get("query_budget", 8))))
    page_budget = max(1, min(5, int(board.get("pages_per_query", 3))))
    queries = queries[:query_budget]
    location = str(board.get("location") or "Germany")
    gl = str(board.get("gl") or ("de" if "germany" in location.casefold() else ""))
    hl = str(board.get("hl") or "en")
    stats = {"planned_queries": len(queries), "attempted_queries": 0,
             "completed_queries": 0, "failed_queries": 0, "pages_requested": 0,
             "provider_rows": 0, "unique_canonical_urls": 0, "valid_postings": 0,
             "no_data_queries": 0, "pagination_pages": 0}
    board["serpapi_run_stats"] = stats
    found, seen = [], set()
    for term in queries:
        stats["attempted_queries"] += 1
        token = None
        query_rows = 0
        for page_index in range(page_budget):
            params = {"engine": "google_jobs", "q": term, "location": location,
                      "api_key": key, "hl": hl}
            if gl:
                params["gl"] = gl
            if token:
                params["next_page_token"] = token
            try:
                payload = request_json("https://serpapi.com/search.json?" + urlencode(params), retries=0)
                if not isinstance(payload, dict):
                    raise ValueError("SerpApi response is not a JSON object")
                metadata = payload.get("search_metadata") or {}
                if metadata.get("status") == "Error":
                    raise ValueError("SerpApi reported an error response")
                rows = payload.get("jobs_results")
                if not isinstance(rows, list):
                    raise ValueError("SerpApi response missing jobs_results")
            except Exception as exc:
                stats["failed_queries"] += 1
                board["serpapi_last_error"] = ("HTTP " + str(exc.code)
                    if getattr(exc, "code", None) else type(exc).__name__)
                break
            stats["pages_requested"] += 1
            if page_index:
                stats["pagination_pages"] += 1
            stats["provider_rows"] += len(rows)
            query_rows += len(rows)
            for item in rows:
                if not isinstance(item, dict):
                    continue
                options = item.get("apply_options") or []
                target = next((x.get("link") for x in options
                    if isinstance(x, dict) and str(x.get("link") or "").startswith("https://")), "")
                target = target or item.get("share_link") or ""
                identity = canonical_url(target)
                if not identity or identity in seen:
                    continue
                title = str(item.get("title") or "").strip()
                company = str(item.get("company_name") or "").strip()
                if not title or not company:
                    continue
                extensions = item.get("detected_extensions") or {}
                if not isinstance(extensions, dict):
                    extensions = {}
                found.append({"title": title, "company": company,
                    "location": str(item.get("location") or location), "url": target,
                    "description": str(item.get("description") or ""),
                    "source": "SerpApi / Google Jobs", "source_attribution": "Google Jobs via SerpApi",
                    "source_original": str(item.get("via") or ""), "serpapi_query": term,
                    "published_at": str(extensions.get("posted_at") or ""),
                    "application_url_unverified": not bool(options)})
                seen.add(identity)
            pagination = payload.get("serpapi_pagination") or {}
            token = pagination.get("next_page_token") if isinstance(pagination, dict) else None
            if not token or not rows:
                break
        else:
            token = None
        if query_rows == 0:
            stats["no_data_queries"] += 1
        if query_rows or stats["failed_queries"] == 0:
            stats["completed_queries"] += 1
    stats["unique_canonical_urls"] = len(seen)
    stats["valid_postings"] = len(found)
    if stats["completed_queries"] == 0 and stats["failed_queries"]:
        raise ValueError("SerpApi Google Jobs: all query requests failed")
    return found