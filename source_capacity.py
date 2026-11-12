"""Shared, provider-aware source capacity profiles and fair task scheduling.

Capacity is measured in provider-native units (queries, pages, boards or feed
limits), not equal raw-job counts. Profiles never override access restrictions.
"""
from __future__ import annotations

from collections import deque

_PROFILES = {
    "maximum_safe": {
        "label": "Maximum configured",
        "ba_rotation_limit": 220,
        "ats_historical_board_cap": 420,
        "ats_discovery_per_family": {
            "personio": 32, "greenhouse": 16, "ashby": 16,
        },
        "workday_extra_page_budget": 16,
        "smartrecruiters_detail_budget": 50,
        "jobspy_results_per_query": 75,
        "linkedin_max_queries_per_run": 40,
        "linkedin_recovery_start_queries": 1,
        "linkedin_query_delay_seconds": 30,
        "max_source_workers": 15,
    },
    "balanced": {
        "label": "Balanced",
        "ba_rotation_limit": 44,
        "ats_historical_board_cap": 360,
        "ats_discovery_per_family": {
            "personio": 24, "greenhouse": 9, "ashby": 9,
        },
        "workday_extra_page_budget": 8,
        "smartrecruiters_detail_budget": 35,
        "jobspy_results_per_query": 60,
        "linkedin_max_queries_per_run": 32,
        "linkedin_recovery_start_queries": 1,
        "linkedin_query_delay_seconds": 30,
        "max_source_workers": 15,
    },
}


def _bounded(value, default, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return min(maximum, max(minimum, parsed))


def source_capacity_settings(profile="maximum_safe", env=None, depth="deep"):
    """Resolve one coherent profile while respecting stricter operator caps."""
    import os
    env = os.environ if env is None else env
    key = profile if profile in _PROFILES else "maximum_safe"
    result = dict(_PROFILES[key])
    result["ats_discovery_per_family"] = dict(result["ats_discovery_per_family"])
    result["profile"] = key
    if depth != "deep":
        result["linkedin_max_queries_per_run"] = min(
            result["linkedin_max_queries_per_run"], 8
        )
        result["linkedin_recovery_start_queries"] = min(
            result["linkedin_recovery_start_queries"], 8
        )
        result["workday_extra_page_budget"] = 0

    # An explicit JobSpy result setting remains an operator cap; the profile
    # can raise the default but cannot silently override a lower configured cap.
    configured_results = str(env.get("JOBSPY_RESULTS_PER_QUERY", "")).strip()
    if configured_results:
        result["jobspy_results_per_query"] = min(
            result["jobspy_results_per_query"],
            _bounded(configured_results, 50, 10, 75),
        )

    configured_linkedin = str(
        env.get("JOBSPY_LINKEDIN_MAX_QUERIES_PER_RUN", "")
    ).strip()
    if configured_linkedin:
        result["linkedin_max_queries_per_run"] = min(
            result["linkedin_max_queries_per_run"],
            _bounded(configured_linkedin, result["linkedin_max_queries_per_run"], 1, 40),
        )
    configured_delay = str(
        env.get("JOBSPY_LINKEDIN_QUERY_DELAY_SECONDS", "")
    ).strip()
    if configured_delay:
        # A slower operator-selected delay is retained; a shorter one cannot
        # lower the profile's safety pacing.
        result["linkedin_query_delay_seconds"] = max(
            result["linkedin_query_delay_seconds"],
            _bounded(configured_delay, result["linkedin_query_delay_seconds"], 0, 30),
        )
    return result


def interleave_sources_by_type(sources):
    """Round-robin source families while preserving order within each family."""
    groups = {}
    order = []
    for board in sources or []:
        if not isinstance(board, dict):
            continue
        kind = str(board.get("type") or "unknown")
        if kind not in groups:
            groups[kind] = deque()
            order.append(kind)
        groups[kind].append(board)

    result = []
    while order:
        remaining = []
        for kind in order:
            if groups[kind]:
                result.append(groups[kind].popleft())
            if groups[kind]:
                remaining.append(kind)
        order = remaining
    return result


def capacity_summary(profile, settings, sources, linkedin_queue=None):
    """Safe, public operational limits; contains no CV, credentials or secrets."""
    sources = sources or []
    counts = {}
    for board in sources:
        kind = str(board.get("type") or "unknown")
        counts[kind] = counts.get(kind, 0) + 1
    jobspy_queries = sum(
        len(board.get("queries") or [])
        for board in sources if str(board.get("type") or "").startswith("jobspy_")
    )
    queue = linkedin_queue if isinstance(linkedin_queue, dict) else {}
    return {
        "profile": profile,
        "label": settings["label"],
        "limits": {
            "bundesagentur_rotation_tasks": settings["ba_rotation_limit"],
            "historical_ats_board_cap": settings["ats_historical_board_cap"],
            "ats_directory_discovery_per_family": settings["ats_discovery_per_family"],
            "workday_extra_pages_per_board": settings["workday_extra_page_budget"],
            "smartrecruiters_detail_lookups_per_board": settings["smartrecruiters_detail_budget"],
            "jobspy_results_per_query": settings["jobspy_results_per_query"],
            "linkedin_max_queries_per_run": settings["linkedin_max_queries_per_run"],
            "linkedin_recovery_start_queries": settings["linkedin_recovery_start_queries"],
            "linkedin_query_delay_seconds": settings["linkedin_query_delay_seconds"],
            "source_workers": settings["max_source_workers"],
        },
        "planned": {
            "source_tasks": len(sources),
            "bundesagentur_tasks": counts.get("bundesagentur", 0),
            "ats_board_tasks": sum(counts.get(k, 0) for k in (
                "ashby", "greenhouse", "lever", "workday", "smartrecruiters",
                "workable", "personio", "pinpoint"
            )),
            "jobspy_platform_queries": jobspy_queries,
            "linkedin_queue_terms": int(queue.get("total_query_terms") or 0),
            "linkedin_batch_queries": int(queue.get("planned_queries") or 0),
        },
        "source_task_counts": counts,
        "policy": (
            "Provider-native limits differ by source. All selected tasks are "
            "scheduled fairly; provider blocks, permission gates and geography "
            "restrictions are never bypassed."
        ),
    }
