#!/usr/bin/env python3
"""Publish completed scan shortlist into private Supabase job history."""
from __future__ import annotations
import json, os, urllib.request, urllib.error
from pathlib import Path

def build_diagnostics(data,jobs):
    # Store bounded aggregate diagnostics so low-yield scans and provider fallback
    # failures can be investigated from Supabase without another scan. Never copy
    # job records, CV text, tokens, or full per-job examples into scan metadata.
    def bounded_rows(name, limit):
        value=data.get(name)
        if not isinstance(value,list):
            return []
        return [row for row in value[:limit] if isinstance(row,dict)]
    
    audit=data.get('discovery_audit') if isinstance(data.get('discovery_audit'),dict) else {}
    filter_summary={
        'rejection_counts':audit.get('rejection_counts') if isinstance(audit.get('rejection_counts'),dict) else {},
        'first_blocker_counts':audit.get('first_blocker_counts') if isinstance(audit.get('first_blocker_counts'),dict) else {},
        'multiple_rejections':int(audit.get('multiple_rejections',0) or 0),
    }
    diagnostics={
        'version':1,
        'target_vacancies':int(data.get('target_vacancies',0) or 0),
        'target_met':bool(data.get('target_met',False)),
        'search_request_summary':{
            'region':(data.get('search_request') or {}).get('region'),
            'min_score':(data.get('search_request') or {}).get('min_score'),
            'support':(data.get('search_request') or {}).get('support'),
            'freshness':(data.get('search_request') or {}).get('freshness'),
            'depth':(data.get('search_request') or {}).get('depth'),
            'capacity':(data.get('search_request') or {}).get('capacity'),
            'city_count':len((data.get('search_request') or {}).get('cities') or []),
            'role_count':len((data.get('search_request') or {}).get('roles') or []),
            'track_count':len((data.get('search_request') or {}).get('tracks') or []),
            'source_count':len((data.get('search_request') or {}).get('sources') or []),
        },
        'discovery_audit':{
            key:audit.get(key) for key in (
                'unique_collected','rule_screen_rejected','preliminary_score_rejected',
                'directory_non_germany_skipped','geography_rejected',
                'before_user_filters','after_user_filters')
            if isinstance(audit.get(key),(int,float))
        },
        'filter_diagnostics':filter_summary,
        'freshness_gate_diagnostics':data.get('freshness_gate_diagnostics') if isinstance(data.get('freshness_gate_diagnostics'),dict) else {},
        'shortlist_date_evidence':data.get('shortlist_date_evidence') if isinstance(data.get('shortlist_date_evidence'),dict) else {},
        'source_failure_counts':data.get('source_failure_counts') if isinstance(data.get('source_failure_counts'),dict) else {},
        'source_failures':bounded_rows('source_failures',50),
        'source_metrics':bounded_rows('source_metrics',100),
        'source_query_metrics':bounded_rows('source_query_metrics',100),
        'source_board_metrics':bounded_rows('source_board_metrics',100),
        'duplicate_suppression':{
            key:(data.get('duplicate_suppression') or {}).get(key)
            for key in ('registry_available','active','candidates_matching_registry',
                        'suppressed','ambiguous_kept','same_run_duplicates_merged','unverified_kept')
            if isinstance((data.get('duplicate_suppression') or {}).get(key),(bool,int,float))
        },
        'ai_provider_usage':data.get('ai_provider_usage') if isinstance(data.get('ai_provider_usage'),dict) else {},
        'ai_failure_counts':data.get('ai_failure_counts') if isinstance(data.get('ai_failure_counts'),dict) else {},
        'ai_error_details':(data.get('ai_error_details') if isinstance(data.get('ai_error_details'),list) else [])[:100],
        'ai_provider_health':data.get('ai_provider_health') if isinstance(data.get('ai_provider_health'),dict) else {},
        'ai_review_sample_size':int(data.get('ai_review_sample_size',0) or 0),
        'ai_review_jobs_attempted':int(data.get('ai_review_jobs_attempted',0) or 0),
        'ai_review_deadline_exhausted':bool(data.get('ai_review_deadline_exhausted',False)),
        'ai_review_coverage':float(data.get('ai_review_coverage',0) or 0),
        'runtime_metrics':data.get('runtime_metrics') if isinstance(data.get('runtime_metrics'),dict) else {},
        'sources_attempted':int(data.get('sources_attempted',0) or 0),
        'sources_succeeded':int(data.get('sources_succeeded',0) or 0),
        'sources_with_postings':int(data.get('sources_with_postings',0) or 0),
        'catalog_track_count':int(data.get('catalog_track_count',0) or 0),
        'tracks_with_results':len(set(
            str((job.get('career_track') or job.get('track') or ''))
            for job in jobs if isinstance(job,dict)
        )),
    }
    return diagnostics


def normalize_source_metrics(rows):
    """Normalize raw scanner metrics (provider-keyed dict or row list) for Supabase."""
    result = []
    if isinstance(rows, dict):
        # radar.py currently emits provider aggregates keyed by source type:
        # {"bundesagentur": {"boards": 12, "succeeded": 11, ...}}.
        # Convert to the list contract used by the source_metrics RPC.
        items = [
            {"provider": provider, **metrics}
            for provider, metrics in rows.items()
            if isinstance(provider, str) and isinstance(metrics, dict)
        ]
    elif isinstance(rows, list):
        items = rows
    else:
        items = []

    for row in items[:500]:
        if not isinstance(row, dict):
            continue

        def count(*keys):
            for key in keys:
                value = row.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    return max(0, int(value))
            return 0

        reserved = {"provider", "source", "engine", "queries_attempted", "attempted",
                    "successful_responses", "succeeded", "completed_queries", "boards_succeeded",
                    "boards", "jobs_found", "jobs", "returned", "raw_postings",
                    "failures", "errors", "failed_queries", "credits_used", "credits_remaining"}
        metric = {
            "provider": str(row.get("provider") or row.get("source") or "unknown")[:160],
            "engine": str(row.get("engine"))[:160] if row.get("engine") else None,
            "queries_attempted": count("queries_attempted", "attempted_queries", "planned_queries", "boards"),
            "successful_responses": count("successful_responses", "succeeded", "completed_queries", "boards_succeeded"),
            "jobs_found": count("jobs_found", "jobs", "returned", "raw_postings"),
            "failures": count("failures", "errors", "failed_queries"),
            "details": {k: v for k, v in row.items() if k not in reserved},
        }
        for key in ("credits_used", "credits_remaining"):
            value = row.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                metric[key] = value
        result.append(metric)
    return result


def rpc_post(base, key, function_name, payload):
    request = urllib.request.Request(
        base.rstrip("/") + "/rest/v1/rpc/" + function_name,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), method="POST",
        headers={"apikey": key, "Authorization": "Bearer " + key,
                 "Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "CareerRadar-SupabasePublisher/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        detail = exc.read(1600).decode("utf-8", errors="replace")
        raise RuntimeError(function_name + " failed HTTP " + str(exc.code) + ": " + detail) from exc


def main():
    base=os.environ.get('SUPABASE_URL','').rstrip('/')
    key=os.environ.get('SUPABASE_SERVICE_ROLE_KEY','')
    run_id=str(os.environ.get('GITHUB_RUN_ID',''))
    if not base or not key or not run_id:
        raise RuntimeError('Missing SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY or GITHUB_RUN_ID')
    data=json.loads(Path('public/jobs.json').read_text(encoding='utf-8'))
    dashboard_published=os.environ.get('DASHBOARD_PUBLISHED','false').lower()=='true'
    result_storage=os.environ.get('RESULT_STORAGE','supabase')
    archive_store=os.environ.get('ARCHIVE_STORE','artifact-only')
    jobs=data.get('jobs')
    if not isinstance(jobs,list):
        raise RuntimeError('public/jobs.json does not contain a jobs array')
    if str(data.get('run_id') or run_id)!=run_id:
        raise RuntimeError('jobs.json run_id differs from current GitHub run')
    endpoint=base+'/rest/v1/rpc/career_radar_upsert_scan_jobs'
    total=0
    for offset in range(0,len(jobs),100):
        batch=jobs[offset:offset+100]
        payload=json.dumps({'p_run_id':run_id,'p_jobs':batch},ensure_ascii=False).encode('utf-8')
        request=urllib.request.Request(endpoint,data=payload,method='POST',headers={
            'apikey':key,'Authorization':'Bearer '+key,
            'Content-Type':'application/json','Accept':'application/json',
            'User-Agent':'CareerRadar-SupabasePublisher/1.0'})
        try:
            with urllib.request.urlopen(request,timeout=40) as response:
                count=json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            body=exc.read(1600).decode('utf-8',errors='replace')
            raise RuntimeError('Supabase RPC returned HTTP '+str(exc.code)+': '+body) from exc
        if not isinstance(count,int):
            raise RuntimeError('Supabase RPC returned an unexpected batch result')
        total+=count
    completed_at=data.get('generated_at')
    collected=int(data.get('total_collected',len(jobs)) or 0)
    shortlisted=int(data.get('total_shortlisted',len(jobs)) or 0)
    west=int(data.get('west_germany_matches',sum(
        1 for job in jobs if isinstance(job,dict) and
        isinstance(job.get('market'),dict) and job['market'].get('west') is True
    )) or 0)
    diagnostics=build_diagnostics(data,jobs)
    source_metrics=normalize_source_metrics(data.get('source_metrics'))
    persisted=rpc_post(base,key,'career_radar_upsert_source_metrics',
                       {'p_run_id':run_id,'p_metrics':source_metrics})
    if persisted != len(source_metrics):
        raise RuntimeError('Supabase source telemetry count mismatch: expected '+
                           str(len(source_metrics))+' got '+str(persisted))
    finalize_endpoint=base+'/rest/v1/rpc/career_radar_finalize_scan_run'
    finalize_payload=json.dumps({
        'p_run_id':run_id,
        'p_collected_jobs':collected,
        'p_shortlisted_jobs':shortlisted,
        'p_western_germany_matches':west,
        'p_completed_at':completed_at,
        'p_history_metadata':{
            'event':os.environ.get('GITHUB_EVENT_NAME','workflow_dispatch'),
            'attempt':int(os.environ.get('GITHUB_RUN_ATTEMPT','1') or 1),
            'status':'completed',
            'conclusion':'success',
            'published':dashboard_published,
            'published_at':completed_at,
            'created_at':completed_at,
            'run_url':os.environ.get('GITHUB_SERVER_URL','https://github.com')+'/'+
                      os.environ.get('GITHUB_REPOSITORY','happytiswis-sudo/engineering-career-radar')+
                      '/actions/runs/'+run_id,
            'profile':data.get('search_request') if isinstance(data.get('search_request'),dict) else {},
            'search_mode':data.get('search_mode'),
            'job_count':len(jobs),
            'collected_count':collected,
            'ai_count':int(data.get('ai_evaluated',0) or 0),
            'hard_excluded':int(data.get('hard_excluded_count',0) or 0),
            'archive_file':'history/run-'+run_id+'.json',
            'storage':result_storage,
            'archive_store':archive_store
        },
        'p_diagnostics':diagnostics
    }).encode('utf-8')
    finalized=rpc_post(base,key,'career_radar_finalize_scan_run',json.loads(finalize_payload.decode('utf-8')))
    if finalized is not True:
        raise RuntimeError('Supabase did not finalize scan metadata for '+run_id)

    stored=rpc_post(base,key,'career_radar_get_scan_diagnostics',{'p_run_id':run_id})
    if not isinstance(stored,dict):
        raise RuntimeError('Supabase diagnostics verification returned an invalid response')
    if not isinstance(stored.get('history_index'),dict) or not isinstance(stored.get('diagnostics'),dict):
        raise RuntimeError('Supabase finalization reported success but metadata is missing')
    if stored['history_index'].get('run_id') not in (None,run_id):
        raise RuntimeError('Supabase history metadata belongs to a different run')
    if int(stored.get('source_metric_count',-1)) != len(source_metrics):
        raise RuntimeError('Supabase source metrics verification count mismatch')
    print('Supabase finalized and verified scan '+run_id+': collected='+str(collected)+
          ', shortlisted='+str(shortlisted)+', source_metrics='+str(len(source_metrics))+'.')
    if total!=len(jobs):
        raise RuntimeError('Supabase stored job count '+str(total)+' differs from shortlist '+str(len(jobs)))
if __name__=='__main__':main()
