"""Bounded public ATS directory discovery. No arbitrary URL probes.

Directory data from a publicly offered GitHub CSV is treated as untrusted;
only known vendor hostnames and validated slugs may produce requests.
No applicant CV, credentials, social-network scraping or private APIs.
"""
from __future__ import annotations
import csv
import datetime as dt
import io
import re
import urllib.request
import urllib.error
from urllib.parse import urlparse

DIRECTORY='https://raw.githubusercontent.com/kalebconfer-sys/job-board-directory/main/'
ALLOWED={'personio','greenhouse','ashby'}
TOK=re.compile(r'^[A-Za-z0-9_-]{2,70}$')
KEYWORDS=('airport','cargo','aviation','aero','aircraft','industrial','logist','quality',
          'manufactur','robot','engineer','machin','energy','solar','wind','rail',
          'medical','health','laboratory','automotiv','electric','material','construction',
          'facility','production','maintenance','technik','technolog','transport','factory')

def parse_directory(text,provider):
    if provider not in ALLOWED:raise ValueError('Unsupported directory family')
    reader=csv.DictReader(io.StringIO(text))
    if not set(('platform','token','board_url','api_url')).issubset(reader.fieldnames or ()):
        raise ValueError('Unexpected job board directory CSV schema')
    out=[];seen=set()
    for row in reader:
        slug=(row.get('token') or '').strip()
        url=urlparse((row.get('board_url') or '').strip())
        api=urlparse((row.get('api_url') or '').strip())
        if not TOK.fullmatch(slug) or (provider,slug.lower()) in seen:continue
        if url.scheme!='https' or api.scheme!='https':continue
        if (row.get('platform') or '').lower()!=provider:continue
        if provider=='personio':
            if url.hostname not in (f'{slug}.jobs.personio.de',f'{slug}.jobs.personio.com'):
                continue
            if api.hostname!=url.hostname or api.path!='/xml':continue
            item={'type':'personio','slug':slug,'domain':url.hostname.rsplit('.',1)[-1],
                  'company':(row.get('company') or slug)[:140],
                  'careers_url':url.geturl()}
        elif provider=='greenhouse':
            if url.hostname not in ('boards.greenhouse.io','job-boards.greenhouse.io'):continue
            if api.hostname!='boards-api.greenhouse.io' or not api.path.endswith('/'+slug+'/jobs'):continue
            item={'type':'greenhouse','slug':slug,'company':(row.get('company') or slug)[:140]}
        else:
            if url.hostname!='jobs.ashbyhq.com' or api.hostname!='api.ashbyhq.com':continue
            if not api.path.endswith('/'+slug):continue
            item={'type':'ashby','slug':slug,'company':(row.get('company') or slug)[:140]}
        try:item['directory_open_roles']=int(row.get('open_roles') or 0)
        except (TypeError,ValueError):item['directory_open_roles']=0
        seen.add((provider,slug.lower()));out.append(item)
        if len(out)>=6000:break
    return out

def choose_directory(existing,when=None,per_family=None):
    """Select a bounded set of fresh public boards using the active capacity profile."""
    quotas=per_family or {'personio':24,'greenhouse':9,'ashby':9}
    date=when or dt.datetime.now(dt.timezone.utc).date()
    prior={(b.get('type'),str(b.get('slug') or '').lower()) for b in existing}
    selected=[];diagnostics={}
    for kind,limit in quotas.items():
        try:
            request=urllib.request.Request(DIRECTORY+kind+'.csv',headers={
                'User-Agent':'EngineeringCareerRadar/5.2 (public employer feed research)',
                'Accept':'text/csv'})
            with urllib.request.urlopen(request,timeout=18) as response:
                raw=response.read(1_500_001)
            if len(raw)>1_500_000:raise ValueError('Directory too large')
            rows=parse_directory(raw.decode('utf-8-sig'),kind)
        except (OSError,UnicodeError,ValueError,urllib.error.URLError) as exc:
            diagnostics[kind]={'status':'unavailable','reason':type(exc).__name__}
            continue
        fresh=[x for x in rows if (kind,x['slug'].lower()) not in prior]
        relevant=[x for x in fresh if any(k in (x['slug']+' '+x['company']).lower() for k in KEYWORDS)]
        relevant.sort(key=lambda x:(-x['directory_open_roles'],x['slug']))
        other=[x for x in fresh if x not in relevant]
        if other:
            ix=(date.toordinal()*37)%len(other)
            other=other[ix:]+other[:ix]
        count=min(limit,len(fresh))
        # 2/3 sector-related companies, remaining seats diverse exploration.
        picks=relevant[:max(1,2*count//3)]
        picks.extend(other[:count-len(picks)])
        if len(picks)<count:picks.extend(relevant[len(picks):count])
        for item in picks:
            item['directory_discovered']=True
            item['directory_source']='kalebconfer-sys/job-board-directory'
        selected.extend(picks)
        diagnostics[kind]={'status':'available','directory_rows':len(rows),
                           'new_boards_selected':len(picks)}
    return selected,diagnostics
