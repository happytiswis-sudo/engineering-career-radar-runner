"""Persistent, private Space search history: summary index and replayable snapshots.

A successful GitHub Actions scan publishes one immutable snapshot keyed by run ID.
Only job-level public fields and CV-relative match evidence are persisted, never
the private CV, API keys, passwords, application notes, or internal credentials.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
import re
from pathlib import Path

MAX_INDEX_ENTRIES=120
MAX_DESCRIPTION_CHARS=2400
KEEP_FIELDS=(
 'company','title','location','url','description','source','published_at',
 'remote','score','rule_score','assessment_type','market','hiring_support',
 'career_track','matched_skills','missing_skills','check_requirements',
 'verdict','why_fit','qualification','ai_assessment','agent_review',
 'source_board','description_completeness','reference','search_city',
 'search_radius_km','remote_location_restriction','employer_career_page',
 'role_priority','freshness','capability','immigration_opportunity','application_path','visa_sponsorship_feed','source_attribution','applicant_region_unverified','also_seen_on','listing_status','expires_at','employer_posting_id','application_url_unverified','source_original','posting_date_basis','discovery_query','discovery_city','novelty_status','first_seen_run','previous_run_count','novelty_review_reasons','imported_from_user_alert','alert_imported_at','jobspy_site','jobspy_aggregator_listing_url','jobspy_direct_employer_link'
)
METRIC_FIELDS=(
 'total_collected','total_shortlisted','sources_attempted','sources_succeeded',
 'sources_with_postings','source_metrics','source_failure_counts','source_failures','discovery_audit','germany_matches','west_germany_matches',
 'small_city_matches','hard_excluded_count','ai_evaluated','ai_provider_usage',
 'specialist_agents_count','specialist_agents_analyzed','visa_review_opportunities','unknown_posting_dates','source_expired_count','ai_failure_counts','ai_review_coverage','ba_details_attempted','ba_details_received','optional_source_status','source_health_comparison','novelty_summary','source_query_metrics','source_board_metrics','shortlist_date_evidence','prior_history_hints_loaded','ai_review_sample_size','linkedin_alert_inbox','linkedin_jobspy_experiment','runtime_metrics','slow_source_boards',
 'ai_provider_health','ai_review_jobs_attempted','ai_review_deadline_exhausted',
 'shortlist_novelty_by_source','classified_failed_boards','duplicate_suppression',
 'linkedin_query_state','source_capacity','board_failure_state'
)

def run_identifier(run_id):
    value=str(run_id or '')
    if not re.fullmatch(r'[0-9]{7,15}',value):
        raise ValueError('Run history requires an authentic GitHub Actions run ID')
    return value

def compact_job(job):
    obj={k:job[k] for k in KEEP_FIELDS if k in job}
    if 'description' in obj:
        obj['description']=str(obj['description'] or '')[:MAX_DESCRIPTION_CHARS]
    review=obj.get('agent_review')
    if isinstance(review,dict):
        obj['agent_review']={k:review[k] for k in
            ('specialists_executed','teams','priority','degree_gate','key_findings')
            if k in review}
    return obj

def create_snapshot(output,run_id,event='workflow_dispatch',attempt='1'):
    ident=run_identifier(run_id)
    jobs=output.get('jobs') or []
    if not isinstance(jobs,list):raise ValueError('Published vacancies must be a list')
    summary={
        'run_id':ident,
        'run_url':f'https://github.com/happytiswis-sudo/engineering-career-radar/actions/runs/{ident}',
        'event':event if event in ('workflow_dispatch','schedule','push') else 'unknown',
        'attempt':str(attempt),
        'status':'completed','conclusion':'success',
        'published':True,
        'published_at':output.get('generated_at') or datetime.now(timezone.utc).isoformat(),
        'search_mode':output.get('search_mode','scheduled'),
        'profile':output.get('search_request') or {},
        'job_count':len(jobs),
        'collected_count':int(output.get('total_collected') or 0),
        'ai_count':int(output.get('ai_evaluated') or 0),
        'hard_excluded':int(output.get('hard_excluded_count') or 0),
        'archive_file':f'history/run-{ident}.json'
    }
    snapshot={
        'schema_version':1,'archive':True,'run_id':ident,
        'generated_at':summary['published_at'],
        'search_request':summary['profile'],
        'search_mode':summary['search_mode'],
        'total_shortlisted':summary['job_count'],
        **{key:output[key] for key in METRIC_FIELDS if key in output},
        'jobs':[compact_job(j) for j in jobs]
    }
    return summary,snapshot

def legacy_snapshot(output):
    """Preserve the last pre-history published result when first enabling archiving."""
    when=str(output.get('generated_at') or '')
    digits=''.join(c for c in when if c.isdigit())[:14]
    if len(digits)!=14:raise ValueError('Legacy snapshot has no valid publication date')
    ident='legacy-'+digits
    jobs=output.get('jobs') or []
    if not isinstance(jobs,list):raise ValueError('Invalid legacy vacancy array')
    profile=output.get('search_request') or {}
    summary={'run_id':ident,'event':'legacy','attempt':'1','status':'completed',
        'conclusion':'success','published':True,
        'published_at':output['generated_at'],
        'search_mode':output.get('search_mode','legacy'),
        'profile':profile,'job_count':len(jobs),
        'collected_count':int(output.get('total_collected') or 0),
        'ai_count':int(output.get('ai_evaluated') or 0),
        'hard_excluded':int(output.get('hard_excluded_count') or 0),
        'archive_file':f'history/{ident}.json'}
    snapshot={'schema_version':1,'archive':True,'run_id':ident,
        'generated_at':summary['published_at'],'search_request':profile,
        'search_mode':summary['search_mode'],
        **{key:output[key] for key in METRIC_FIELDS if key in output},
        'jobs':[compact_job(j) for j in jobs]}
    return summary,snapshot

def merge_index(existing,new_entry):
    rows=existing.get('runs') if isinstance(existing,dict) else []
    if not isinstance(rows,list):rows=[]
    rows=[r for r in rows if isinstance(r,dict) and
         str(r.get('run_id'))!=new_entry['run_id']]
    rows.insert(0,new_entry)
    rows.sort(key=lambda x:x.get('published_at') or '',reverse=True)
    return {'schema_version':1,'updated_at':datetime.now(timezone.utc).isoformat(),
            'retained_summaries':min(len(rows),MAX_INDEX_ENTRIES),
            'notice':'Successful published scan summaries; running, cancelled and failed executions are obtained separately from GitHub.',
            'runs':rows[:MAX_INDEX_ENTRIES]}

def write_history(output,run_id,event,attempt,prior,public_dir):
    entry,snapshot=create_snapshot(output,run_id,event,attempt)
    index=merge_index(prior,entry)
    root=Path(public_dir)
    archive=root/entry['archive_file']
    archive.parent.mkdir(parents=True,exist_ok=True)
    archive.write_text(json.dumps(snapshot,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    (root/'search-history.json').write_text(
        json.dumps(index,ensure_ascii=False,indent=2),encoding='utf8')
    return entry,index
