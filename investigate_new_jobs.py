"""Inspect public vacancy evidence in a private HF archive.

Never print private CV, application notes, GitHub/HF credentials or hidden job descriptions.
"""
import json
import re
import sys
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from career_intelligence import published_on

AIRPORT=re.compile(r'airport|airside|ground.handling|ramp|cargo|baggage|airfreight|air.f[r]eight|'
                   r'flughafen|vorfeld|bodenabfertig|luftfracht|aircraft.turnaround|gse|'
                   r'gepäck|airline|terminal',re.I)

def summarize(snapshot,expected_run=None):
    if expected_run and str(snapshot.get('run_id')) != str(expected_run):
        raise ValueError('Archive run ID does not match requested historical scan')
    jobs=snapshot.get('jobs')
    if not isinstance(jobs,list):raise ValueError('Missing archived vacancy list')
    fresh=[j for j in jobs if isinstance(j,dict) and j.get('novelty_status')=='new_to_history']
    if len(fresh)!=int((snapshot.get('novelty_summary') or {}).get('new_to_history',len(fresh))):
        raise ValueError('New-job classification does not reconcile to summary')
    now=datetime.fromisoformat(str(snapshot.get('generated_at') or '').replace('Z','+00:00'))
    if now.tzinfo is None:now=now.replace(tzinfo=timezone.utc)
    source_counts=Counter(str(j.get('source') or 'Unspecified') for j in fresh)
    buckets=Counter();sector=Counter();support=Counter();by_source=defaultdict(lambda:Counter())
    listing=[]
    for j in fresh:
        age=published_on(j.get('published_at'),now=now)['age_days']
        age_bucket=('unknown' if age is None else '24h' if age<=1 else
                    '7d' if age<=7 else '30d' if age<=30 else '>30d')
        source=str(j.get('source') or 'Unspecified')
        buckets[age_bucket]+=1;by_source[source][age_bucket]+=1
        related=bool(AIRPORT.search(str(j.get('title') or '')+' '+str(j.get('career_track') or '')))
        sector['Airport, ground or cargo' if related else 'Other industries']+=1
        tier=str((j.get('immigration_opportunity') or {}).get('tier') or 'not_available')
        support[tier]+=1
        listing.append({
           'source':source,'title':str(j.get('title') or '')[:140],
           'company':str(j.get('company') or '')[:120],
           'location':str(j.get('location') or '')[:110],
           'published_at':str(j.get('published_at') or '')[:45],
           'date_age_bucket':age_bucket,'score':j.get('score'),
           'track':str(j.get('career_track') or '')[:90],
           'airport_related_by_title':related,
           'sponsorship_evidence_tier':tier,
           'listing_status':str(j.get('listing_status') or 'not_verified'),
           'url':str(j.get('url') or '')[:500]
        })
    order={'24h':0,'7d':1,'30d':2,'unknown':3,'>30d':4}
    listing.sort(key=lambda j:(order.get(j['date_age_bucket'],5),-float(j['score'] or 0),
                               j['source'],j['company']))
    all_counts=Counter(str(j.get('source') or 'Unspecified') for j in jobs if isinstance(j,dict))
    return {'run_id':str(snapshot.get('run_id') or ''),'total_jobs':len(jobs),
       'new_jobs':len(fresh),'sources_new':dict(source_counts.most_common()),
       'sources_all':dict(all_counts.most_common()),
       'date_buckets_new':dict(buckets),'industry_family_new':dict(sector),
       'sponsorship_evidence_new':dict(support),
       'by_source_new_and_date':{k:dict(v) for k,v in sorted(by_source.items())},
       'source_metrics':snapshot.get('source_metrics') or {},
       'source_failures':snapshot.get('source_failure_counts') or {},
       'shortlist_date_evidence':snapshot.get('shortlist_date_evidence') or {},
       'new_listings':listing}

def main():
    if len(sys.argv)!=3:raise SystemExit('Usage: investigate_new_jobs.py archived.json RUN_ID')
    path=Path(sys.argv[1]);result=summarize(json.loads(path.read_text(encoding='utf8')),sys.argv[2])
    print('PUBLIC-VACANCY AUDIT JSON START')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print('PUBLIC-VACANCY AUDIT JSON END')
    return result

if __name__=='__main__':main()
