"""Career Radar Mentor: aggregate-only strategy and quality review."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent


def build_mentor_review(snapshot, company_intel=None):
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    jobs = [x for x in snapshot.get("jobs", []) if isinstance(x, dict)]
    companies = company_intel if isinstance(company_intel, dict) else {}
    try:
        catalog = json.loads((ROOT / "role_catalog.json").read_text(encoding="utf-8")).get("roles", [])
    except (OSError, ValueError, TypeError):
        catalog = []
    tracks = sorted({str(x.get("track") or "").strip() for x in catalog if x.get("track")})
    job_counts = Counter(str(x.get("career_track") or "Unclassified") for x in jobs)
    # This telemetry is emitted by industry_search.py for Federal Employment
    # Agency (BA) queries only. Other ATS/job-board searches are not currently
    # attributable to a career track, so never present this as all-source coverage.
    query_by_track = {}
    for row in snapshot.get("source_query_metrics", []):
        if not isinstance(row, dict):
            continue
        track = str(row.get("industry_track") or "").strip()
        if not track:
            continue
        item = query_by_track.setdefault(track, {"queries": 0, "raw_postings": 0,
            "cv_matches": 0, "unseen_recent_cv_matches": 0})
        item["queries"] += 1
        for key in ("raw_postings", "cv_matches", "unseen_recent_cv_matches"):
            item[key] += int(row.get(key) or 0)
    track_report = []
    for track in tracks:
        q = query_by_track.get(track, {})
        raw, matches = int(q.get("raw_postings", 0)), int(job_counts.get(track, 0))
        state = ("results_found" if matches else "not_measured_this_run" if not q else
                 "source_returned_jobs_but_none_shortlisted" if raw else "searched_no_raw_results")
        track_report.append({"track": track, "shortlisted": matches,
            "queries": int(q.get("queries", 0)), "raw_postings": raw,
            "raw_postings_source": "Federal Employment Agency (BA) query telemetry only",
            "cv_matches_reported_by_query": int(q.get("cv_matches", 0)),
            "unseen_recent_cv_matches": int(q.get("unseen_recent_cv_matches", 0)),
            "status": state,
            "status_scope": "Shortlisted counts combine all sources; query/raw-posting status is BA-only"})
    track_report.sort(key=lambda x: (x["shortlisted"], x["raw_postings"], x["queries"], x["track"]))
    non_design = [x for x in track_report if not any(k in x["track"].casefold()
        for k in ("cad", "design", "simulation", "manufacturing & production", "project engineering & delivery"))]
    top = sorted(job_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_share = top[0][1] / max(1, len(jobs)) if top else 0
    failures = [x for x in snapshot.get("source_failures", []) if isinstance(x, dict)]
    source_metrics = snapshot.get("source_metrics") or {}
    source_recovery = []
    for name, metrics in source_metrics.items():
        if not isinstance(metrics, dict):
            continue
        attempted = int(metrics.get("boards", 0))
        errors = int(metrics.get("errors", 0))
        returned = int(metrics.get("returned", 0))
        if errors or (attempted and not returned):
            source_recovery.append({"source": name, "boards": attempted, "errors": errors, "returned": returned})
    ai_done = int(snapshot.get("ai_evaluated", 0) or 0)
    ai_jobs_attempted = int(snapshot.get("ai_review_jobs_attempted", 0) or 0)
    ai_queue = int(snapshot.get("ai_review_sample_size", 0) or 0)
    ai_health = snapshot.get("ai_provider_health") or {}
    raw_ai_failures = snapshot.get("ai_failure_counts") or {}
    ai_failure_reasons = [{"reason": str(k), "failures": int(v or 0)}
        for k, v in sorted(raw_ai_failures.items(), key=lambda item: int(item[1] or 0), reverse=True)
        if int(v or 0) > 0][:10] if isinstance(raw_ai_failures, dict) else []
    # Count actual provider calls, not jobs that had at least one provider call.
    # One job can generate multiple provider attempts through fallbacks.
    ai_attempts = sum(int(v.get("attempts", 0) or 0) for v in ai_health.values() if isinstance(v, dict))
    ai_valid = sum(int(v.get("success", 0) or 0) for v in ai_health.values() if isinstance(v, dict))
    ai_failed = sum(int(v.get("failed", 0) or 0) for v in ai_health.values() if isinstance(v, dict))
    ai_valid_rate = round(ai_valid / ai_attempts, 4) if ai_attempts else None
    quality = companies.get("quality_metrics") or {}
    recommendations = []
    if jobs and top_share >= 0.45:
        recommendations.append({"priority": "high", "area": "Role diversity",
            "finding": f"The largest track represents {top_share:.0%} of shortlisted results.",
            "action": "Protect more query capacity for operations, maintenance, quality, inspection, logistics, procurement, facilities and technical customer roles."})
    no_result = [x for x in non_design if x["status"] == "searched_no_raw_results"]
    screened = [x for x in non_design if x["status"] == "source_returned_jobs_but_none_shortlisted"]
    if no_result:
        recommendations.append({"priority": "high", "area": "BA discovery coverage",
            "finding": f"{len(no_result)} non-design tracks had BA queries but no raw postings.",
            "action": "Rotate additional German title synonyms and regional searches for these tracks; compare other source coverage separately."})
    if screened:
        recommendations.append({"priority": "high", "area": "Matching and scoring",
            "finding": f"{len(screened)} non-design tracks had BA raw postings but none were shortlisted.",
            "action": "Audit title matching, transferable-skill evidence and rejection reasons; do not lower mandatory qualification gates."})
    if failures:
        recommendations.append({"priority": "high", "area": "Source recovery",
            "finding": f"{len(failures)} source-level failures or cooldown notices were recorded.",
            "action": "Diagnose provider status and Retry-After; recover one source at a time without retrying 403/429 blocks."})
    if ai_queue and (ai_valid_rate is None or ai_valid_rate < 0.8 or ai_done < ai_queue):
        recommendations.append({"priority": "medium", "area": "AI review throughput",
            "finding": (f"{ai_valid}/{ai_attempts} valid provider responses ({ai_valid_rate:.0%}) across "
                        f"{ai_attempts} calls; {ai_done} jobs assessed from a queue of {ai_queue}.")
                       if ai_attempts else f"No valid provider response was recorded for a queue of {ai_queue} jobs.",
            "action": "Use the provider-specific failure reasons and latency below to isolate malformed output, quota, access and timeout failures; route the next batch to the best-performing available provider."})
    if companies and int(quality.get("verified_websites", 0)) < int(companies.get("national_company_count", 0)):
        recommendations.append({"priority": "medium", "area": "Employer evidence",
            "finding": "Some retained company leads still lack a verified official website.",
            "action": "Prioritise stale and unverified company records before expanding the search budget further."})
    if not recommendations:
        recommendations.append({"priority": "low", "area": "Next improvement",
            "finding": "No dominant operational failure was identified from the published aggregates.",
            "action": "Continue rotating underrepresented tracks and validate the next live source cycle."})
    return {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": snapshot.get("run_id"),
        "status": "needs_attention" if any(x["priority"] == "high" for x in recommendations) else "stable",
        "headline": "Career Radar Mentor: broaden opportunity coverage, protect source reliability and challenge weak evidence.",
        "summary": {"shortlisted_jobs": len(jobs), "catalog_tracks": len(tracks),
            "tracks_with_results": sum(1 for x in track_report if x["shortlisted"]),
            "tracks_measured_by_ba_queries": sum(1 for x in track_report if x["queries"]),
            "non_design_tracks_with_results": sum(1 for x in non_design if x["shortlisted"]),
            "largest_track_share": round(top_share, 3), "ai_valid_reviews": ai_done,
            "ai_queue": ai_queue, "ai_jobs_with_provider_attempts": ai_jobs_attempted,
            "ai_provider_attempts": ai_attempts, "ai_valid_provider_responses": ai_valid,
            "ai_failed_provider_responses": ai_failed, "ai_valid_response_rate": ai_valid_rate,
            "ai_failure_reason_count": sum(x["failures"] for x in ai_failure_reasons),
            "source_failure_records": len(failures),
            "verified_company_websites": int(quality.get("verified_websites", 0)),
            "verified_careers_pages": int(quality.get("verified_careers_pages", 0)),
            "public_vacancy_links": int(quality.get("public_vacancy_links", 0)),
            "contactable_hidden_opportunity_prospects": int(quality.get("contactable_hidden_opportunity_prospects", 0))},
        "track_coverage_scope": {"shortlisted_jobs": "All collected job sources after deduplication and filtering",
            "query_and_raw_posting_telemetry": "Federal Employment Agency (BA) industry queries only",
            "limitation": "ATS and other job-board results are included in shortlisted counts but are not yet attributed to every career track at query level."},
        "top_tracks": [{"track": k, "jobs": v} for k, v in top],
        "track_coverage": track_report, "source_recovery": source_recovery[:12],
        "ai_provider_health": ai_health, "ai_provider_failure_reasons": ai_failure_reasons,
        "recommendations": recommendations,
        "official_international_source": {"name": "Make it in Germany job listings",
            "url": "https://www.make-it-in-germany.com/en/working-in-germany/job-listings",
            "relationship": "The official portal states its vacancies come from the Federal Employment Agency and listed employers agree to receive applications from skilled workers abroad. This is not proof of visa sponsorship or work-permit eligibility."}}
