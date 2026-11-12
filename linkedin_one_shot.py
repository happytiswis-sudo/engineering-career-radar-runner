"""One authorized JobSpy LinkedIn query; no retries, proxies or browser access.

Run only via explicit GitHub workflow_dispatch. This pilot never replaces the
normal Career Radar vacancy snapshot; it writes a separate small public-job
metadata report for the private dashboard and an Actions artifact.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import re
import time
from pathlib import Path

from jobspy_optional import authorized_sites, jobspy_for_board
from radar import load, evaluate_rule

ROOT=Path(__file__).resolve().parent
ROLE_PATTERN=re.compile(r"^[\wÀ-ÿ][\wÀ-ÿ()&/.+, -]{2,80}$",re.UNICODE)
PLACE_PATTERN=re.compile(r"^[\wÀ-ÿ][\wÀ-ÿ()&/.+, -]{2,80}$",re.UNICODE)

def validate_pilot_inputs(role,location):
    role=str(role or '').strip()
    location=str(location or '').strip()
    if not ROLE_PATTERN.fullmatch(role) or not PLACE_PATTERN.fullmatch(location):
        raise ValueError('Pilot requires one plain role and one plain location (3–81 characters)')
    return role,location

def _status(error):
    message=str(error).casefold()
    if '429' in message or 'rate limit' in message:
        return 'rate_limited'
    if '403' in message or 'forbidden' in message or 'blocked' in message:
        return 'access_denied'
    if 'no usable data' in message or 'no job data' in message:
        return 'no_usable_data'
    return 'provider_error'

def single_linkedin_pilot(role='Quality Engineer',location='Germany',output_path=None):
    role,location=validate_pilot_inputs(role,location)
    started=time.monotonic()
    report={
        'schema_version':1,'mode':'one_query_live_jobspy',
        'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'run_id':os.environ.get('GITHUB_RUN_ID',''),
        'source':'JobSpy / LinkedIn','role_query':role,'location':location,
        'requested_queries':1,'requested_results':10,'status':'not_authorized',
        'provider_queries_attempted':0,'provider_queries_completed':0,
        'provider_rows':0,'valid_postings':0,'cv_evaluated':0,
        'cv_preliminary_matches':0,'cv_qualified_matches':0,
        'jobs':[],'diagnosis':'',
        'note':('This experiment does not use proxies, retry a 403/429, or prove '
                'any employer vacancy is still active. Never interpret 0 jobs '
                'as proof LinkedIn has no openings.')
    }
    # Explicitly enforce the existing independent permission and live-mode
    # requirements. Do not import or contact the provider before this check.
    if 'linkedin' not in authorized_sites():
        report['diagnosis']='Live LinkedIn JobSpy retrieval is not enabled by all separate authorization settings.'
    else:
        board={'type':'jobspy_linkedin','slug':'one-shot-linkedin',
               'company':'JobSpy / LinkedIn','queries':[role],
               'country':'Germany','location':location}
        # JobSpy respects the default 10-per-query minimum and never retries
        # access denials. This temporary per-process setting cannot affect
        # other source scans.
        previous=os.environ.get('JOBSPY_RESULTS_PER_QUERY')
        os.environ['JOBSPY_RESULTS_PER_QUERY']='10'
        try:
            items=jobspy_for_board(board)
            stats=board.get('jobspy_run_stats') or {}
            report['provider_queries_attempted']=stats.get('attempted_queries',0)
            report['provider_queries_completed']=stats.get('completed_queries',0)
            report['provider_rows']=stats.get('provider_rows',0)
            report['valid_postings']=len(items)
            if items:
                settings,cv=load()
                catalog=json.loads((ROOT/'role_catalog.json').read_text(encoding='utf8'))
                settings['catalog_roles']=catalog['roles']
                qualified=0
                for job in items[:10]:
                    match=evaluate_rule(job,settings,cv)
                    if match is None:continue
                    report['cv_preliminary_matches']+=1
                    if (match.get('qualification') or {}).get('status')=='excluded':
                        continue
                    qualified+=1
                    report['jobs'].append({
                        'title':match['title'],'company':match['company'],
                        'location':match['location'],'url':match['url'],
                        'score':match['score'],
                        'verdict':match.get('verdict','Review'),
                        'qualification_status':(match.get('qualification') or {}).get('status','unknown'),
                        'published_at':match.get('published_at') or '',
                        'description_present':bool(job.get('description')),
                        'application_link_unverified':bool(job.get('application_url_unverified'))
                    })
                report['cv_qualified_matches']=qualified
                report['cv_evaluated']=len(items[:10])
                report['status']='retrieved'
                report['diagnosis']='JobSpy returned valid LinkedIn job records. CV filtering may reduce the displayed list.'
            else:
                report['status']='no_usable_data'
                report['diagnosis']='JobSpy returned no usable records for this one query; not proof of an empty job market.'
        except (ValueError,KeyError,TypeError,TimeoutError,OSError) as exc:
            stats=board.get('jobspy_run_stats') or {}
            report['provider_queries_attempted']=stats.get('attempted_queries',0)
            report['provider_queries_completed']=stats.get('completed_queries',0)
            report['provider_rows']=stats.get('provider_rows',0)
            report['status']=_status(str(exc))
            # Only fixed category text, no exceptions, cookies or user secrets.
            report['diagnosis']={
                'rate_limited':'LinkedIn returned HTTP 429. The single trial stopped immediately; no bypass attempted.',
                'access_denied':'LinkedIn denied the request (HTTP 403 or other blocking). No bypass attempted.',
                'no_usable_data':'LinkedIn/JobSpy returned no usable records for this query.',
                'provider_error':'JobSpy encountered a provider error; inspect authorized provider access and safe source logs.'
            }[report['status']]
        finally:
            if previous is None:os.environ.pop('JOBSPY_RESULTS_PER_QUERY',None)
            else:os.environ['JOBSPY_RESULTS_PER_QUERY']=previous
    report['elapsed_seconds']=round(time.monotonic()-started,2)
    target=Path(output_path or ROOT/'public'/'linkedin-pilot.json')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return report

if __name__=='__main__':
    role=os.getenv('LINKEDIN_PILOT_ROLE','Quality Engineer')
    location=os.getenv('LINKEDIN_PILOT_LOCATION','Germany')
    result=single_linkedin_pilot(role,location)
    print('LinkedIn JobSpy one-query status:',result['status'],flush=True)
    print('Requested 1 query / 10 jobs; actual queries attempted:',
          result['provider_queries_attempted'],'rows:',result['provider_rows'],
          'valid:',result['valid_postings'],'CV-qualified:',result['cv_qualified_matches'],flush=True)
    print(result['diagnosis'],flush=True)
    summary=os.getenv('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a',encoding='utf8') as f:
            f.write('## LinkedIn JobSpy single-query experiment\n\n')
            f.write('**Outcome:** '+result['status']+'  \n')
            f.write('**Requested:** '+result['role_query']+' in '+result['location']+
                    ' (one query, up to 10 records)  \n')
            f.write('**Attempted queries:** '+str(result['provider_queries_attempted'])+
                    '  | **Provider rows:** '+str(result['provider_rows'])+
                    '  | **Valid jobs:** '+str(result['valid_postings'])+
                    '  | **CV-qualified:** '+str(result['cv_qualified_matches'])+'  \n\n')
            f.write(result['diagnosis']+'\n\n')
            f.write('No previous Career Radar jobs were overwritten.\n')
