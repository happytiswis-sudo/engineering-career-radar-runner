"""Bounded Cloro Google SERP discovery adapter for public job postings.

Cloro provides Google organic result data, not a jobs API. Results are only
accepted when the title/snippet/url indicates a job listing. API key is read
from CLORO_API_KEY_1 / CLORO_API_KEY_2; no credentials are embedded in source or logs.
"""
from __future__ import annotations
import json
import os
import re
import urllib.error
import urllib.request
from urllib.parse import urlparse

ENDPOINT = "https://api.cloro.dev/v1/monitor/google"
MAX_QUERIES = 8
MAX_RESULTS_PER_QUERY = 20
USER_AGENT = "EngineeringCareerRadar/5.3 (public job discovery)"


def _clean(value, cap=7000):
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", value).strip()[:cap]


def _is_job_result(item):
    title = _clean(item.get("title"), 240).casefold()
    snippet = _clean(item.get("snippet"), 1400).casefold()
    url = str(item.get("link") or item.get("url") or "").strip()
    host = urlparse(url).hostname or ""
    if urlparse(url).scheme != "https" or not host:
        return False
    # Prefer recognizable job detail pages; don't turn generic search results
    # into vacancies merely because the page mentions hiring.
    path = urlparse(url).path.casefold()
    job_path = any(token in path for token in (
        "/jobs/", "/job/", "/stellenangebote", "/stellenanzeige",
        "/karriere/", "/career/", "/vacancies/", "/positions/"
    ))
    job_words = re.search(r"\b(job|jobs|stellenangebot|stellenanzeige|vacancy|vacancies|position|career)\b", title)
    context = re.search(r"\b(apply|bewerben|requirements|anforderungen|job description|stellenbeschreibung)\b", snippet)
    return bool(job_path or (job_words and context))


def _organic(response):
    if not isinstance(response, dict):
        return []
    if isinstance(response.get("result"), dict):
        response = response["result"]
    for key in ("organicResults", "organic_results", "results"):
        value = response.get(key)
        if isinstance(value, list):
            return value
    data = response.get("data")
    if isinstance(data, dict):
        for key in ("organicResults", "organic_results", "results"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def fetch_cloro_jobs(board):
    """Fetch one Google SERP query with tight timeout and result bounds."""
    tokens = [os.environ.get(name, "").strip() for name in ("CLORO_API_KEY_1", "CLORO_API_KEY_2")]
    tokens = [token for token in tokens if token]
    # Legacy single-key support remains for older environments.
    if not tokens:
        legacy = os.environ.get("CLORO_API_KEY", "").strip()
        if legacy:
            tokens = [legacy]
    if not tokens:
        raise RuntimeError("cloro_api_keys_missing")
    query = _clean(board.get("query"), 180)
    if not query:
        raise ValueError("Cloro board query is empty")
    payload = json.dumps({
        "query": query,
        "country": board.get("country", "de"),
        "language": board.get("language", "de"),
        "num": min(MAX_RESULTS_PER_QUERY, max(5, int(board.get("num", 15))))
    }).encode("utf-8")
    # Rotate account preference across queries; retry the second account only on
    # authentication rejection or account quota exhaustion.
    match = re.search(r"(\d+)$", str(board.get("slug", "")))
    preferred = int(match.group(1)) - 1 if match else 0
    offset = preferred % len(tokens)
    ordered_tokens = tokens[offset:] + tokens[:offset]
    last_error = None
    raw = None
    for token in ordered_tokens:
        request = urllib.request.Request(ENDPOINT, data=payload, method="POST", headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT
        })
        try:
            with urllib.request.urlopen(request, timeout=18) as response:
                raw = json.load(response)
            break
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403, 429):
                last_error = exc
                continue
            raise RuntimeError("cloro_http_" + str(exc.code)) from exc
    if raw is None:
        if last_error and last_error.code in (401, 403):
            raise RuntimeError("cloro_auth_rejected") from last_error
        if last_error and last_error.code == 429:
            raise RuntimeError("cloro_rate_limited") from last_error
        raise RuntimeError("cloro_request_failed")
    rows = _organic(raw)[:MAX_RESULTS_PER_QUERY]
    found, seen = [], set()
    for item in rows:
        if not isinstance(item, dict) or not _is_job_result(item):
            continue
        url = str(item.get("link") or item.get("url") or "").strip()
        if url in seen:
            continue
        seen.add(url)
        title = _clean(item.get("title"), 180)
        snippet = _clean(item.get("snippet"), 1800)
        host = urlparse(url).hostname or ""
        company = _clean(item.get("employer") or host.removeprefix("www."), 150)
        location = _clean(item.get("location") or "Germany (location in listing to verify)", 150)
        found.append({
            "company": company, "title": title, "location": location,
            "url": url, "description": snippet,
            "source": "Cloro Google organic search",
            "published_at": str(item.get("date") or ""),
            "remote": False, "employer_site_verified": False,
            "description_completeness": "Google SERP excerpt; employer page verification required",
            "cloro_query": query, "cloro_rank": item.get("position")
        })
    return found
