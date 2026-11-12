"""Summarize novelty of shortlisted jobs by first-attributed source."""
from collections import defaultdict

def shortlist_novelty_by_source(jobs):
    grouped=defaultdict(lambda: {'shortlisted':0,'new_to_history':0,
      'previously_seen':0,'review_required':0,'unverified_identity':0,'new_within_7d':0,
      'new_within_30d':0,'new_unknown_date':0})
    for job in jobs:
        if not isinstance(job,dict):continue
        name=str(job.get('source_attribution') or job.get('source') or 'Unknown')[:100]
        row=grouped[name];row['shortlisted']+=1
        status=job.get('novelty_status')
        if status=='new_to_history':
            row['new_to_history']+=1
            age=(job.get('freshness') or {}).get('age_days')
            if type(age) in (int,float) and 0<=age<=7:row['new_within_7d']+=1
            if type(age) in (int,float) and 0<=age<=30:row['new_within_30d']+=1
            if age is None:row['new_unknown_date']+=1
        elif status=='previously_seen':row['previously_seen']+=1
        elif status=='review_required':row['review_required']+=1
        else:row['unverified_identity']+=1
    return dict(sorted(grouped.items(),key=lambda kv:(-kv[1]['new_to_history'],kv[0])))

def categorize_failure(reason):
    text=str(reason or '').lower()
    if '403' in text or 'forbidden' in text:return 'access_blocked'
    if '429' in text or 'rate limit' in text:return 'rate_limited'
    if '404' in text or 'not found' in text:return 'board_not_found'
    if any(x in text for x in ('500','502','503','504')):return 'upstream_server_error'
    if 'timeout' in text or 'timed out' in text:return 'timeout'
    if 'no usable data' in text:return 'no_results_available'
    if any(x in text for x in ('invalid','valueerror','jsondecodeerror')):
        return 'response_format'
    if 'authorization' in text or 'disabled' in text:return 'not_authorized'
    return 'other_or_unknown'

def classify_board_failures(failures):
    return [{**record,'category':categorize_failure(record.get('error'))}
            for record in (failures or []) if isinstance(record,dict)]
