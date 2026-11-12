"""Compare like-for-like published source coverage without inventing vacancies."""
from __future__ import annotations

def comparable_source_health(previous,current):
    if not isinstance(previous,dict) or not isinstance(current,dict):
        return {'comparable':False,'alerts':[]}
    if previous.get('search_mode') != current.get('search_mode') or (
        previous.get('search_request') or {}) != (current.get('search_request') or {}):
        return {'comparable':False,'reason':'Search mode/profile changed','alerts':[]}
    before=previous.get('source_metrics') or {}
    after=current.get('source_metrics') or {}
    if not isinstance(before,dict) or not isinstance(after,dict):
        return {'comparable':False,'alerts':[]}
    alerts=[]
    for name in sorted(set(before)&set(after)):
        prior=before.get(name) or {}
        now=after.get(name) or {}
        prior_raw=int(prior.get('returned') or 0)
        new_raw=int(now.get('returned') or 0)
        prior_success=int(prior.get('succeeded') or 0)
        new_success=int(now.get('succeeded') or 0)
        if prior_success>=3 and new_success==0:
            alerts.append({'source':name,'signal':'source_unavailable',
                'previous_successes':prior_success,'current_successes':new_success})
        elif prior_raw>=20 and new_raw < prior_raw * 0.3:
            alerts.append({'source':name,'signal':'raw_yield_down_over_70pct',
                'previous_returned':prior_raw,'current_returned':new_raw})
    return {'comparable':True,'previous_run_id':str(previous.get('run_id') or ''),
            'alerts':alerts[:25],
            'note':'Warnings compare like-for-like search profiles, not proof of API outages or fewer market vacancies.'}
