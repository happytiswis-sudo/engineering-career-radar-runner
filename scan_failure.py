"""Privacy-safe failure report for scans that return zero valid source URLs.

Never publish a blank replacement dashboard or infer that zero retrieved
records means the job market contains zero vacancies.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

def _category(reason):
    reason=str(reason or '').casefold()
    if '429' in reason or 'rate limit' in reason:
        return 'rate_limited'
    if '403' in reason or 'forbidden' in reason:
        return 'access_blocked'
    if 'no usable data' in reason or 'no job data' in reason:
        return 'no_usable_data'
    if 'timeout' in reason or 'timed out' in reason:
        return 'timeout'
    return 'other_source_error'

def build_empty_scan_report(source_failures,source_metrics,selected_sources,run_id=None):
    """Report source facts only: no credentials, URLs, CV, or job descriptions."""
    detailed=[]
    for failure in source_failures or []:
        if not isinstance(failure,dict):continue
        source=str(failure.get('source') or '')[:70]
        board=str(failure.get('board') or '')[:90]
        reason=_category(failure.get('error'))
        if board.startswith('optional-'):
            # A selected-but-disabled option is not a failed request.
            continue
        detailed.append({'source':source,'board':board,'category':reason})
    counts={}
    for item in detailed:counts[item['category']]=counts.get(item['category'],0)+1
    task_count=len(selected_sources or [])
    requested=[str(item.get('type') or '')[:70] for item in (selected_sources or [])
               if isinstance(item,dict)]
    source_stats={}
    for name,stats in (source_metrics or {}).items():
        if not isinstance(stats,dict):continue
        source_stats[str(name)[:70]]={
            key:stats[key] for key in (
                'boards','succeeded','errors','planned_queries','attempted_queries',
                'completed_queries','failed_queries','no_data_queries','provider_rows',
                'valid_postings','returned')
            if key in stats and isinstance(stats[key],(int,float))}
    is_linkedin_429=(any(x['source']=='jobspy_linkedin' and
                         x['category']=='rate_limited' for x in detailed))
    if is_linkedin_429:
        diagnosis=('LinkedIn JobSpy was rate-limited (HTTP 429). '
                   'The source stopped after the blocked response; no bypass was attempted.')
        advice=('Check permitted provider access and rate-limit terms before any future '
                'authorized test. Do not use proxies or immediate retries to evade the limit.')
    else:
        diagnosis='All selected sources failed or supplied no valid job URLs.'
        advice='Review individual source diagnostics and source availability before another scan.'
    return {
        'schema_version':1,
        'run_id':str(run_id or '')[:30],
        'status':'failed_no_usable_source_results',
        'result_snapshot_preserved':True,
        'no_vacancy_market_claim':True,
        'selected_source_tasks':task_count,
        'selected_source_types':requested[:30],
        'failed_board_count':len(detailed),
        'failure_categories':counts,
        'failed_boards':detailed[:80],
        'source_query_metrics':source_stats,
        'diagnosis':diagnosis,'next_action':advice
    }

def save_empty_scan_report(report,path='scan-failure.json',summary_path=None):
    """Create a GitHub Actions-only JSON artifact and an actionable step summary."""
    target=Path(path)
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',
                      encoding='utf-8')
    summary_path=summary_path if summary_path is not None else os.getenv('GITHUB_STEP_SUMMARY')
    if summary_path:
        with open(summary_path,'a',encoding='utf-8') as f:
            f.write('## Career Radar scan could not retrieve any vacancies\n\n')
            f.write('**Status:** failed; previous published snapshot preserved.\n\n')
            f.write(report['diagnosis']+'\n\n')
            f.write('**Source tasks selected:** '+str(report['selected_source_tasks'])+'\n\n')
            f.write('**Failure categories:** '+', '.join(k+': '+str(v)
                for k,v in report['failure_categories'].items())+'\n\n')
            f.write('**Next action:** '+report['next_action']+'\n\n')
            f.write('The JSON failure artifact contains source counts only, not CV content.\n')
    return target
