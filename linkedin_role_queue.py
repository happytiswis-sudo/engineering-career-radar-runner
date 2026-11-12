"""Persistent, fair-coverage LinkedIn role query queue.

This module only plans local query strings and persists counters. It does not
contact LinkedIn, retry provider blocks, or use proxies.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import os

from industry_search import TRACK_TERMS

DEFAULT_MAX_QUERIES_PER_RUN = 40
DEFAULT_QUERY_DELAY_SECONDS = 30
DEFAULT_RECOVERY_START_QUERIES = 1
DEFAULT_RATE_LIMIT_COOLDOWN_HOURS = 48


def _bounded_int(env, key, default, minimum, maximum):
    try:
        value = int(env.get(key, default))
    except (TypeError, ValueError):
        value = default
    return min(maximum, max(minimum, value))


def linkedin_capacity_settings(env=None, depth="deep"):
    env = os.environ if env is None else env
    default_budget = DEFAULT_MAX_QUERIES_PER_RUN if depth == "deep" else 8
    return {
        "max_queries_per_run": _bounded_int(
            env, "JOBSPY_LINKEDIN_MAX_QUERIES_PER_RUN", default_budget, 1, 40
        ),
        "query_delay_seconds": _bounded_int(
            env, "JOBSPY_LINKEDIN_QUERY_DELAY_SECONDS",
            DEFAULT_QUERY_DELAY_SECONDS, 0, 30
        ),
        "recovery_start_queries": _bounded_int(
            env, "JOBSPY_LINKEDIN_RECOVERY_START_QUERIES",
            DEFAULT_RECOVERY_START_QUERIES if depth == "deep" else 8, 1, 40
        ),
        "rate_limit_cooldown_hours": _bounded_int(
            env, "JOBSPY_LINKEDIN_RATE_LIMIT_COOLDOWN_HOURS",
            DEFAULT_RATE_LIMIT_COOLDOWN_HOURS, 1, 168
        ),
        "reset_access_pause": str(
            env.get("JOBSPY_LINKEDIN_RESET_PAUSE", "")
        ).strip().lower() == "yes",
    }


def build_linkedin_role_queue(catalog_roles, requested_roles=None,
                              requested_tracks=None):
    """Interleave all titles and track synonyms so every batch spans industries."""
    explicit = list(dict.fromkeys(
        str(x).strip()[:85] for x in (requested_roles or [])
        if isinstance(x, str) and 2 <= len(x.strip()) <= 85
    ))
    if explicit:
        return explicit

    selected = set(requested_tracks or [])
    track_queries = {}
    for record in catalog_roles or []:
        if not isinstance(record, dict):
            continue
        title = str(record.get("title") or "").strip()
        track = str(record.get("track") or "").strip()
        if not title or not track or len(title) > 85:
            continue
        if selected and track not in selected:
            continue
        track_queries.setdefault(track, [])
    # Preserve catalogue title order within each track.
    for record in catalog_roles or []:
        if not isinstance(record, dict):
            continue
        title = str(record.get("title") or "").strip()
        track = str(record.get("track") or "").strip()
        if track in track_queries and title and title not in track_queries[track]:
            track_queries[track].append(title)

    # Start each track with a real catalogue title, then interleave its
    # multilingual aliases among the remaining titles. The first batch therefore
    # reaches many industries immediately instead of spending a whole cycle on
    # generic synonyms before any exact job titles are queried.
    for track, titles in list(track_queries.items()):
        aliases = [str(x).strip() for x in TRACK_TERMS.get(track, [])
                   if isinstance(x, str) and x.strip()]
        terms = []
        for index, title in enumerate(titles):
            terms.append(title)
            if index < len(aliases):
                terms.append(aliases[index])
        track_queries[track] = list(dict.fromkeys(terms))

    queue = []
    seen = set()
    tracks = sorted(track_queries)
    depth = 0
    while tracks:
        remaining = []
        for track in tracks:
            terms = track_queries[track]
            if depth < len(terms):
                term = terms[depth]
                key = term.casefold()
                if key not in seen:
                    seen.add(key)
                    queue.append(term)
            if depth + 1 < len(terms):
                remaining.append(track)
        tracks = remaining
        depth += 1
    return queue


def _as_utc(value=None):
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        parsed = value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _empty_state(queue_key, total, catalog_roles, catalog_tracks):
    return {
        "schema_version": 1,
        "queue_key": queue_key,
        "total_query_terms": total,
        "catalog_role_count": catalog_roles,
        "catalog_track_count": catalog_tracks,
        "cursor": 0,
        "cycles_completed": 0,
        "total_attempted_queries": 0,
        "total_completed_queries": 0,
        "total_provider_rows": 0,
        "total_valid_postings": 0,
        "rate_limit_count": 0,
        "clean_batches_since_rate_limit": 0,
        "blocked_until": "",
        "paused": False,
        "status": "ready",
        "last_run_id": "",
        "last_attempted_queries": 0,
        "last_completed_queries": 0,
        "last_provider_rows": 0,
        "last_valid_postings": 0,
        "last_stop_reason": "",
    }


def prepare_linkedin_batch(catalog_roles, prior_state=None,
                           requested_roles=None, requested_tracks=None,
                           env=None, depth="deep", now=None):
    """Return one bounded batch, or no batch during a provider cooldown/pause."""
    env = os.environ if env is None else env
    now = _as_utc(now)
    settings = linkedin_capacity_settings(env, depth)
    queue = build_linkedin_role_queue(
        catalog_roles, requested_roles=requested_roles,
        requested_tracks=requested_tracks
    )
    queue_key = sha256("\n".join(queue).encode("utf-8")).hexdigest()
    catalog_role_count = len({
        str(r.get("title") or "").strip().casefold()
        for r in (catalog_roles or []) if isinstance(r, dict) and r.get("title")
    })
    catalog_track_count = len({
        str(r.get("track") or "").strip()
        for r in (catalog_roles or []) if isinstance(r, dict) and r.get("track")
    })
    explicit_scope = list(dict.fromkeys(
        str(x).strip().casefold() for x in (requested_roles or [])
        if isinstance(x, str) and x.strip()
    ))
    scoped_records = [
        r for r in (catalog_roles or []) if isinstance(r, dict)
        and (not requested_tracks or r.get("track") in set(requested_tracks))
    ]
    scope_role_count = (
        len(explicit_scope) if explicit_scope
        else len({str(r.get("title") or "").strip().casefold()
                  for r in scoped_records if r.get("title")})
    )
    scope_track_count = (
        len({str(r.get("track") or "").strip() for r in scoped_records if r.get("track")})
        if not explicit_scope else
        len({str(r.get("track") or "").strip() for r in catalog_roles or []
             if isinstance(r, dict) and str(r.get("title") or "").strip().casefold() in explicit_scope
             and r.get("track")})
    )
    old = prior_state if isinstance(prior_state, dict) else {}
    if old.get("queue_key") != queue_key:
        state = _empty_state(queue_key, len(queue), catalog_role_count,
                             catalog_track_count)
    else:
        state = {**_empty_state(queue_key, len(queue), catalog_role_count,
                                catalog_track_count), **old}
    state["total_query_terms"] = len(queue)
    state["catalog_role_count"] = catalog_role_count
    state["catalog_track_count"] = catalog_track_count
    # The scan immediately before this persistent queue was introduced hit
    # HTTP 429. Seed that known cooldown once because the prior jobs.json has
    # no queue state to carry it forward. The resulting state is published and
    # reused by subsequent scans; an expired seed never blocks a later run.
    initial_block = str(
        env.get("JOBSPY_LINKEDIN_INITIAL_COOLDOWN_UNTIL", "")
    ).strip()
    if initial_block:
        try:
            seeded_until = _as_utc(initial_block)
        except (TypeError, ValueError):
            seeded_until = None
        if seeded_until and seeded_until > now:
            current_block = str(state.get("blocked_until") or "").strip()
            try:
                current_until = _as_utc(current_block) if current_block else None
            except (TypeError, ValueError):
                current_until = None
            if current_until is None or current_until < seeded_until:
                state["blocked_until"] = seeded_until.isoformat(timespec="seconds")
                state["rate_limit_count"] = max(
                    1, int(state.get("rate_limit_count") or 0)
                )
                state["status"] = "rate_limited"
                state["last_stop_reason"] = (
                    state.get("last_stop_reason")
                    or "Prior live scan HTTP 429; initial cooldown carried forward"
                )
    # Explicit reset only clears an HTTP 403 operator pause. It must never
    # shorten or bypass a provider 429 cooldown.
    if settings["reset_access_pause"] and state.get("paused"):
        state["paused"] = False
        state["status"] = "ready"
        state["last_stop_reason"] = ""

    effective_max = settings["max_queries_per_run"]
    if int(state.get("rate_limit_count") or 0) > 0:
        clean_batches = max(0, int(state.get("clean_batches_since_rate_limit") or 0))
        effective_max = min(
            settings["max_queries_per_run"],
            settings["recovery_start_queries"] * (2 ** clean_batches),
        )

    if not queue:
        status = "no_queries"
        terms = []
    elif state.get("paused"):
        status = "paused_access_denied"
        terms = []
    else:
        blocked = str(state.get("blocked_until") or "")
        try:
            blocked_until = _as_utc(blocked) if blocked else None
        except (TypeError, ValueError):
            blocked_until = None
        if blocked_until and blocked_until > now:
            status = "cooldown_active"
            terms = []
        else:
            state["blocked_until"] = ""
            status = "ready"
            cursor = int(state.get("cursor") or 0) % len(queue)
            count = min(effective_max, len(queue))
            terms = [queue[(cursor + offset) % len(queue)]
                     for offset in range(count)]
            state["cursor"] = cursor

    cursor = int(state.get("cursor") or 0)
    return {
        "queries": terms,
        "state": state,
        "plan": {
            "queue_key": queue_key,
            "queue_total": len(queue),
            "start_cursor": cursor,
            "cursor": cursor,
            "batch_size": len(terms),
            "catalog_role_count": catalog_role_count,
            "catalog_track_count": catalog_track_count,
            "scope_role_count": scope_role_count,
            "scope_track_count": scope_track_count,
            "max_queries_per_run": effective_max,
            "configured_max_queries_per_run": settings["max_queries_per_run"],
            "recovery_start_queries": settings["recovery_start_queries"],
            "query_delay_seconds": settings["query_delay_seconds"],
            "rate_limit_cooldown_hours": settings["rate_limit_cooldown_hours"],
            "status": status,
            "blocked_until": str(state.get("blocked_until") or ""),
            "paused": bool(state.get("paused")),
            "cycles_completed": int(state.get("cycles_completed") or 0),
            "coverage_percent": round(100 * cursor / max(1, len(queue)), 1),
            "queries_remaining": max(0, len(queue) - cursor),
        },
    }


def complete_linkedin_batch(state, plan, stats, env=None, now=None,
                            run_id=""):
    """Advance only past attempted terms; never consume the query that got 429."""
    env = os.environ if env is None else env
    now = _as_utc(now)
    settings = linkedin_capacity_settings(env)
    state = dict(state or {})
    stats = stats if isinstance(stats, dict) else {}
    total = max(1, int(plan.get("queue_total") or state.get("total_query_terms") or 1))
    start = int(plan.get("start_cursor") or 0)
    batch_size = max(0, int(plan.get("batch_size") or 0))
    advance = min(batch_size, max(0, int(stats.get("cursor_advance_count") or 0)))
    absolute = start + advance
    state["cycles_completed"] = int(state.get("cycles_completed") or 0) + absolute // total
    state["cursor"] = absolute % total
    state["total_query_terms"] = total
    attempted = max(0, int(stats.get("attempted_queries") or 0))
    completed = max(0, int(stats.get("completed_queries") or 0))
    rows = max(0, int(stats.get("provider_rows") or 0))
    valid = max(0, int(stats.get("valid_postings") or 0))
    stop = str(stats.get("stop_reason") or "")
    state["total_attempted_queries"] = int(state.get("total_attempted_queries") or 0) + attempted
    state["total_completed_queries"] = int(state.get("total_completed_queries") or 0) + completed
    state["total_provider_rows"] = int(state.get("total_provider_rows") or 0) + rows
    state["total_valid_postings"] = int(state.get("total_valid_postings") or 0) + valid
    state["last_run_id"] = str(run_id or "")
    state["last_attempted_queries"] = attempted
    state["last_completed_queries"] = completed
    state["last_provider_rows"] = rows
    state["last_valid_postings"] = valid
    state["last_stop_reason"] = stop

    if "429" in stop or "rate limit" in stop.casefold():
        state["rate_limit_count"] = int(state.get("rate_limit_count") or 0) + 1
        state["clean_batches_since_rate_limit"] = 0
        state["blocked_until"] = (
            now + timedelta(hours=settings["rate_limit_cooldown_hours"])
        ).isoformat(timespec="seconds")
        state["paused"] = False
        state["status"] = "rate_limited"
    elif "403" in stop or "forbidden" in stop.casefold():
        state["blocked_until"] = ""
        state["paused"] = True
        state["status"] = "paused_access_denied"
    else:
        state["blocked_until"] = ""
        state["paused"] = False
        if (batch_size > 0 and advance == batch_size and attempted == batch_size
                and not stop and int(stats.get("failed_queries") or 0) == 0):
            state["clean_batches_since_rate_limit"] = (
                int(state.get("clean_batches_since_rate_limit") or 0) + 1
            )
        state["status"] = (
            "batch_complete" if advance == batch_size and batch_size > 0
            else "partial" if batch_size else "ready"
        )
    return state


def linkedin_queue_progress(plan, state, stats=None):
    stats = stats if isinstance(stats, dict) else {}
    total = max(0, int(plan.get("queue_total") or state.get("total_query_terms") or 0))
    cursor = int(state.get("cursor") or 0)
    return {
        "status": plan.get("status") if not plan.get("batch_size") else state.get("status"),
        "catalog_role_count": int(plan.get("catalog_role_count") or 0),
        "catalog_track_count": int(plan.get("catalog_track_count") or 0),
        "scope_role_count": int(plan.get("scope_role_count") or 0),
        "scope_track_count": int(plan.get("scope_track_count") or 0),
        "total_query_terms": total,
        "cursor": cursor,
        "cycles_completed": int(state.get("cycles_completed") or 0),
        "queries_remaining": max(0, total - cursor),
        "coverage_percent": round(100 * cursor / max(1, total), 1),
        "batch_limit": int(plan.get("max_queries_per_run") or 0),
        "configured_batch_limit": int(plan.get("configured_max_queries_per_run") or plan.get("max_queries_per_run") or 0),
        "recovery_start_queries": int(plan.get("recovery_start_queries") or 0),
        "clean_batches_since_rate_limit": int(state.get("clean_batches_since_rate_limit") or 0),
        "rate_limit_count": int(state.get("rate_limit_count") or 0),
        "recovery_ramp_active": int(state.get("rate_limit_count") or 0) > 0,
        "planned_queries": int(plan.get("batch_size") or 0),
        "attempted_queries": int(stats.get("attempted_queries") or 0),
        "completed_queries": int(stats.get("completed_queries") or 0),
        "provider_rows": int(stats.get("provider_rows") or 0),
        "valid_postings": int(stats.get("valid_postings") or 0),
        "description_present": int(stats.get("description_present") or 0),
        "direct_apply_links": int(stats.get("direct_apply_links") or 0),
        "last_stop_reason": str(state.get("last_stop_reason") or ""),
        "blocked_until": str(state.get("blocked_until") or ""),
        "paused": bool(state.get("paused")),
        "query_delay_seconds": int(plan.get("query_delay_seconds") or 0),
        "rate_limit_cooldown_hours": int(plan.get("rate_limit_cooldown_hours") or 0),
        "total_attempted_queries": int(state.get("total_attempted_queries") or 0),
        "total_completed_queries": int(state.get("total_completed_queries") or 0),
        "total_provider_rows": int(state.get("total_provider_rows") or 0),
        "total_valid_postings": int(state.get("total_valid_postings") or 0),
        "rate_limit_count": int(state.get("rate_limit_count") or 0),
    }
