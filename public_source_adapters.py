"""Keyless, bounded external vacancy adapters for Career Radar.

SmartRecruiters uses documented public company postings. Workday requests ONLY
selected employer-owned public career pages, never protected HCM resources.
Jobicy / Remotive / Himalayas are attributed remote listing sources.
No bypass of access controls, rate limits, or anti-bot policies.
"""
from __future__ import annotations
import datetime as dt
import html
import json
import os
import re
import time
import urllib.error
import http.client
import urllib.request
import xml.etree.ElementTree as ET
from industry_search import rotating_workday_terms
from urllib.parse import quote, urlencode, urlparse

AGENT='EngineeringCareerRadar/5.1 (personal job research)'
WORKDAY_HOST=re.compile(r'^[a-zA-Z0-9-]+\.wd[0-9]+\.myworkdayjobs\.com$')
VALID_ID=re.compile(r'^[A-Za-z0-9_-]{2,70}$')
ROLE_WORDS=re.compile(r'(engineer|ingenieur|techniker|fertig|production|manufactur|konstrukt|mechanic|'
                      r'project|projekt|quality|qualit|maintenan|instand|inspection|'
                      r'reliabil|technolog|industrial|assembly|avionics|supply|camo|'
                      r'arbeitsvorbereitung|systems|aerospace|luftfahrt|material|cad|'
                      r'planung|betriebs|airport|airside|ramp|cargo|baggage|ground.handling|turnaround|'
                      r'luftfracht|flughafen|vorfeld|bodenabfertigung|logisti|warehouse|lager|'
                      r'facility|terminal|rechenzentrum|gebaeude|gebäude)',re.I)
MAX_BYTES=6_000_000

def request_json(url,method='GET',body=None,timeout=22,retries=1):
    """Retry only transient server errors; obey Retry-After and stop on permissions errors."""
    data=json.dumps(body).encode('utf-8') if body is not None else None
    headers={'Accept':'application/json','User-Agent':AGENT}
    if data is not None:headers['Content-Type']='application/json'
    if urlparse(url).hostname=='himalayas.app' and os.environ.get('HIMALAYAS_API_KEY'):
        headers['Authorization']='Bearer '+os.environ['HIMALAYAS_API_KEY']
    req=urllib.request.Request(url,data=data,headers=headers,method=method)
    for attempt in range(retries+1):
        try:
            with urllib.request.urlopen(req,timeout=timeout) as response:
                raw=response.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES:raise ValueError('Response exceeds supported size')
            return json.loads(raw)
        except urllib.error.HTTPError as error:
            if error.code not in (429,500,502,503,504) or attempt>=retries:raise
            wait=error.headers.get('Retry-After','')
            try:seconds=min(5,max(1,int(wait)))
            except (TypeError,ValueError):seconds=2
            time.sleep(seconds)
        except (http.client.IncompleteRead, urllib.error.URLError, TimeoutError, ConnectionError) as error:
            # A flaky public feed must not abort the entire multi-source scan.
            # Retry this request once; if it still fails, propagate to the
            # per-board collector which records the source error and continues.
            if attempt>=retries:raise
            time.sleep(min(2,attempt+1))

def clean(value,limit=6000):
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',str(value or '')))).strip()[:limit]

def vacancy(company,title,location,url,description,source,date='',remote=False,**metadata):
    u=urlparse(str(url or ''))
    if u.scheme!='https' or not u.netloc or not title:return None
    return {'company':clean(company,150),'title':clean(title,190),'location':clean(location,180),
        'url':u.geturl(),'description':clean(description),'source':source,
        'published_at':str(date or '')[:50],'remote':bool(remote),**metadata}

def smartrecruiters(board):
    slug=board['slug']
    if not VALID_ID.fullmatch(slug):raise ValueError('Invalid SmartRecruiters company')
    base=f'https://api.smartrecruiters.com/v1/companies/{slug}/postings'
    results=[]
    try:detail_budget=max(0,min(75,int(board.get('detail_budget',35))))
    except (TypeError,ValueError):detail_budget=35
    for offset in (0,100,200):
        raw=request_json(base+'?'+urlencode({'limit':100,'offset':offset,
              **({'country':'de'} if board.get('germany_first',True) else {})}))
        postings=raw.get('content') or []
        if not isinstance(postings,list):raise ValueError('Invalid SmartRecruiters response')
        for listing in postings:
            name=listing.get('name') or listing.get('title')
            location=listing.get('location') or {}
            if not isinstance(location,dict):location={}
            place=', '.join(filter(None,[location.get('city'),location.get('region'),location.get('country')]))
            ident=str(listing.get('id') or listing.get('uuid') or '')
            # Public posting URLs, not application endpoints requiring login.
            # Do not manufacture an application URL from a numeric posting ID.
            # Use only a link actually supplied by the provider's public response.
            url=listing.get('postingUrl') or listing.get('applyUrl') or listing.get('url')
            description=listing.get('jobAd') or listing.get('description') or ''
            if isinstance(description,dict):description=' '.join(str(x) for x in description.values())
            if name and ROLE_WORDS.search(name) and detail_budget and VALID_ID.fullmatch(ident):
                try:
                    d=request_json(base+'/'+quote(ident))
                    parts=d.get('jobAd') or {}
                    if isinstance(parts,dict):
                        sections=parts.get('sections') or {}
                        if isinstance(sections,dict):
                            description=' '.join(str(v.get('text','')) for v in sections.values() if isinstance(v,dict))
                    url=d.get('postingUrl') or d.get('applyUrl') or url
                    detail_budget-=1
                except (urllib.error.HTTPError,urllib.error.URLError,ValueError,KeyError,TimeoutError):
                    detail_budget-=1
            x=vacancy(board['company'],name,place,url,description,'SmartRecruiters',
                      listing.get('releasedDate') or listing.get('createdOn') or '',location.get('remote') is True,
                      source_board='https://careers.smartrecruiters.com/'+slug,employer_posting_id=ident)
            if x:results.append(x)
        if offset+len(postings)>=int(raw.get('totalFound') or 0) or len(postings)<100:break
        time.sleep(.25)
    return results

def workday(board):
    """Bounded public CXS keyword rotation. A broken term must not lose prior jobs."""
    site=board.get('site','')
    host=board.get('host','')
    if not WORKDAY_HOST.fullmatch(host) or not VALID_ID.fullmatch(site):
        raise ValueError('Invalid Workday public career board URL')
    tenant=host.split('.',1)[0]
    root=f'https://{host}'
    endpoint=f'{root}/wday/cxs/{tenant}/{site}'
    results=[];seen=set();detail_budget=48;successful_queries=0;last_error=None
    extra_budget=max(0,min(20,int(board.get('workday_extra_page_budget') or 0)))
    board['workday_page_stats']={'extra_page_budget':extra_budget,
                                 'extra_pages_attempted':0,
                                 'extra_pages_succeeded':0}
    # Broad scans search every current career track. Use the first page when
    # many distinct tracks are requested to diversify instead of repeating a
    # small subset deeply; individual provider quotas are still respected.
    terms=board.get('queries') or rotating_workday_terms(board)
    offsets=(0,20) if len(terms)>12 and extra_budget else (
        (0,) if len(terms)>12 else (0,20,40))
    for term in terms:
        for offset in offsets:
            extra_page=offset>0 and len(terms)>12
            if extra_page and extra_budget<=0:break
            if extra_page:
                extra_budget-=1
                board['workday_page_stats']['extra_pages_attempted']+=1
            try:
                raw=request_json(endpoint+'/jobs','POST',{'appliedFacets':{},'limit':20,
                    'offset':offset,'searchText':term},timeout=24,retries=0)
                successful_queries+=1
                if extra_page:board['workday_page_stats']['extra_pages_succeeded']+=1
            except (urllib.error.HTTPError,urllib.error.URLError,ValueError,TimeoutError) as exc:
                last_error=exc
                break  # other terms may still work; never discard earlier results
            listings=raw.get('jobPostings') or []
            if not isinstance(listings,list):raise ValueError('Invalid Workday public board response')
            for listing in listings:
                path=str(listing.get('externalPath') or '')
                if not path.startswith('/job/') or len(path)>650:continue
                if path in seen:continue
                seen.add(path)
                title=listing.get('title') or ''
                if not ROLE_WORDS.search(title):continue
                description='';published='';expires='';req_id='';date_basis='workday_list_relative_age_only'
                loc=listing.get('locationsText') or listing.get('location') or ''
                if detail_budget:
                    detail_budget-=1
                    try:
                        more=request_json(endpoint+path,retries=0)
                        info=more.get('jobPostingInfo') or {}
                        description=info.get('jobDescription') or info.get('jobDescriptionHtml') or ''
                        loc=info.get('location') or loc
                        # These dates come from the employer's public detail,
                        # not guesses from list text such as 'Posted Today'.
                        start=info.get('startDate') or ''
                        precise=info.get('datePosted') or info.get('postingDate') or ''
                        end=info.get('endDate') or ''
                        if isinstance(precise,str) and re.match(r'^\d{4}-\d\d-\d\d',precise):
                            published=precise
                            date_basis='workday_employer_detail_explicit_posted_date'
                        elif isinstance(start,str) and re.match(r'^\d{4}-\d\d-\d\d',start):
                            published=start
                            date_basis='workday_employer_detail_start_date_not_verified_first_publication'
                        if isinstance(end,str) and re.match(r'^\d{4}-\d\d-\d\d',end):
                            expires=end
                        req_id=str(info.get('jobReqId') or '')[:90]
                    except (urllib.error.HTTPError,urllib.error.URLError,ValueError,TimeoutError):
                        pass
                public_url=root+'/'+site+path
                j=vacancy(board['company'],title,loc,public_url,description,'Workday',
                          published,False,source_board=root+'/'+site,
                          expires_at=expires,employer_posting_id=req_id,
                          posting_age_text=str(listing.get('postedOn') or '')[:45],
                          posting_date_basis=date_basis,
                          description_completeness=
                          'public Workday detail' if description else 'public Workday list only')
                if j:results.append(j)
            if offset+len(listings)>=int(raw.get('total') or 0) or len(listings)<20:break
            time.sleep(.2)
    if successful_queries==0 and last_error:raise last_error
    return results


def jobicy(board):
    # Current public v2 API: count is limited to 100; no cursor on this endpoint.
    # Query title categories rather than repeatedly downloading the identical global list.
    found=[];seen=set()
    tags=board.get('tags') or ['engineering','mechanical','manufacturing','quality','project']
    for tag in tags[:5]:
        params={'count':100,'tag':tag}
        raw=request_json('https://jobicy.com/api/v2/remote-jobs?'+urlencode(params))
        for item in raw.get('jobs',[]) or []:
            url=item.get('url')
            if url in seen:continue
            seen.add(url)
            j=vacancy(item.get('companyName'),item.get('jobTitle'),item.get('jobGeo') or 'Remote (geographic restrictions unknown)',
                      url,item.get('jobDescription') or item.get('jobExcerpt'),'Jobicy',
                      item.get('pubDate'),True,remote_location_restriction=item.get('jobGeo'))
            if j:found.append(j)
        time.sleep(.35)
    return found

def remotive(board):
    # Terms require attribution and linking directly to Remotive.
    # Its public API results are delayed by about 24h.
    raw=request_json('https://remotive.com/api/remote-jobs?limit=450',retries=0)
    found=[]
    for item in raw.get('jobs',[]) or []:
        j=vacancy(item.get('company_name'),item.get('title'),
                  item.get('candidate_required_location') or 'Remote (location unstated)',
                  item.get('url'),item.get('description'),'Remotive (24h delay)',
                  item.get('publication_date'),True,
                  remote_location_restriction=item.get('candidate_required_location') or '')
        if j:found.append(j)
    return found

def himalayas(board):
    # 24h data cache; up to 20 jobs per call. Keep requests bounded on free tier.
    found=[];seen=set()
    cursor=None
    for _ in range(2):
        # Two broad cursor pages plus ten targeted location-aware searches.
        params={'limit':20}
        if cursor:params['cursor']=cursor
        raw=request_json('https://himalayas.app/jobs/api?'+urlencode(params),retries=0)
        listings=raw.get('jobs') or []
        for item in listings:
            expiry=item.get('expiryDate')
            if expiry:
                try:
                    if isinstance(expiry,(int,float)) or (isinstance(expiry,str) and expiry.isdigit()):
                        when=dt.datetime.fromtimestamp(int(expiry),dt.timezone.utc)
                    else:
                        when=dt.datetime.fromisoformat(str(expiry).replace('Z','+00:00'))
                    if when.tzinfo and when<dt.datetime.now(dt.timezone.utc):continue
                except (TypeError,ValueError,OverflowError,OSError):pass
            url=item.get('applicationLink') or item.get('guid')
            if not url or url in seen:continue
            seen.add(url)
            restriction=item.get('locationRestrictions') or []
            place='Remote worldwide' if not restriction else 'Remote restricted: '+', '.join(str(v) for v in restriction[:7])
            published=item.get('pubDate')
            try:
                if isinstance(published,(int,float)) or (isinstance(published,str) and published.isdigit()):
                    published=dt.datetime.fromtimestamp(int(published),dt.timezone.utc).isoformat()
            except (ValueError,OverflowError,OSError,TypeError):published=''
            j=vacancy(item.get('companyName'),item.get('title'),place,url,
                      item.get('description') or item.get('excerpt'),'Himalayas',
                      published,True,remote_location_restriction=restriction,
                      original_application_link=item.get('applicationLink'),
                      source_url=item.get('guid'),source_attribution='Himalayas')
            if j:found.append(j)
        next_cursor=raw.get('nextCursor')
        if len(listings)<20 or not next_cursor or next_cursor==cursor:break
        cursor=next_cursor
        time.sleep(.35)
    # Spend fewer requests on broad, location-restricted remote postings.
    # The public search API documents worldwide=true and country=DE filters.
    filters=(
        ('engineering',{'worldwide':'true'}),
        ('manufacturing',{'worldwide':'true'}),
        ('quality',{'worldwide':'true'}),
        ('operations',{'worldwide':'true'}),
        ('cargo',{'worldwide':'true'}),
        ('airport',{'worldwide':'true'}),
        ('logistics',{'country':'DE'}),
        ('maintenance',{'country':'DE'}),
        ('mechanical',{'country':'DE'}),
        ('project coordinator',{'country':'DE'}),
    )
    custom=board.get('queries') or []
    if custom:
        filters=tuple((term,({'worldwide':'true'} if i%4==0 else {'country':'DE'}))
                      for i,term in enumerate(custom))
    for keyword,restriction in filters:
        params={'q':keyword,'page':1,'sort':'recent',**restriction}
        try:
            data=request_json('https://himalayas.app/jobs/api/search?'+urlencode(params),retries=0)
        except (urllib.error.URLError,ValueError,TimeoutError):
            continue  # A failed filtered term cannot discard previous results.
        posts=data.get('jobs') if isinstance(data,dict) else None
        if not isinstance(posts,list):continue
        for item in posts:
            if not isinstance(item,dict):continue
            url=item.get('applicationLink') or item.get('guid')
            if not url or url in seen:continue
            seen.add(url)
            expiry=item.get('expiryDate')
            if expiry:
                try:
                    when=dt.datetime.fromtimestamp(int(expiry),dt.timezone.utc) if str(expiry).isdigit() else dt.datetime.fromisoformat(str(expiry).replace('Z','+00:00'))
                    if when.tzinfo and when<dt.datetime.now(dt.timezone.utc):continue
                except (ValueError,TypeError,OSError,OverflowError):pass
            restrictions=item.get('locationRestrictions') or []
            place='Remote worldwide' if not restrictions else 'Remote restricted: '+', '.join(str(v) for v in restrictions[:6])
            pub=item.get('pubDate')
            if isinstance(pub,(int,float)) or (isinstance(pub,str) and pub.isdigit()):
                try:pub=dt.datetime.fromtimestamp(int(pub),dt.timezone.utc).isoformat()
                except (ValueError,OSError,OverflowError):pub=''
            j=vacancy(item.get('companyName'),item.get('title'),place,url,
                      item.get('description') or item.get('excerpt'),'Himalayas',pub,True,
                      source_url=item.get('guid'),source_attribution='Himalayas',
                      source_query=keyword,remote_location_restriction=restrictions,
                      remote_timezone_restriction=item.get('timezoneRestrictions') or [])
            if j:found.append(j)
        time.sleep(.35)
    return found

def workable(board):
    slug=board['slug']
    if not VALID_ID.fullmatch(slug):raise ValueError('Invalid Workable account slug')
    # This is Workable's public company posting widget, not its protected SPI API.
    raw=request_json(f'https://www.workable.com/api/accounts/{slug}?details=true',
                     timeout=23,retries=0)
    result=[]
    for item in (raw.get('jobs') or [])[:400]:
        place=', '.join(filter(None,[item.get('city'),item.get('state'),item.get('country')]))
        link=item.get('application_url') or item.get('url') or item.get('shortlink')
        j=vacancy(raw.get('name') or board['company'],item.get('title'),place,link,
                  item.get('description'),'Workable',
                  item.get('published_on') or item.get('created_at') or '',
                  item.get('telecommuting') is True or item.get('workplace_type')=='remote',
                  source_board='https://apply.workable.com/'+slug)
        if j:result.append(j)
    return result

def nomado24(board):
    """Nomado24 REST v2, no key, bounded cursor paging, visible attribution.

    The provider requires that subsequent requests carry ONLY cursor/limit
    and that hasNext cursors be followed even when an intermediate page is empty.
    Applicant eligibility is not inferred from an advertised location.
    """
    results=[];seen_urls=set()
    base='https://api.nomado24.de/api/public/v2/jobs'
    queries=board.get('queries') or ('Ingenieur','manufacturing','quality','project')
    # All selected catalog tracks get a request; avoid hiding all but the
    # first six user-added tracks. Keep page depth finite on large plans.
    for term in queries:
        params={'q':term,'limit':55}
        if board.get('country') in ('DE','AT','CH','FR','NL','BE'):
            params['country']=board['country']
        cursor_seen=set()
        for page in range(2 if len(queries)>6 else 5):
            raw=request_json(base+'?'+urlencode(params),retries=1)
            if not isinstance(raw,dict):raise ValueError('Nomado24 v2 response is not an object')
            listings=raw.get('data',raw.get('jobs'))
            if not isinstance(listings,list):raise ValueError('Nomado24 v2 listings must be an array')
            meta=raw.get('meta') if isinstance(raw.get('meta'),dict) else {}
            for item in listings:
                if not isinstance(item,dict):continue
                url=item.get('url') or item.get('canonicalUrl') or item.get('job_url')
                if not url or url in seen_urls:continue
                company=item.get('companyName') or item.get('company_name') or item.get('company')
                if isinstance(company,dict):company=company.get('name')
                place=item.get('location') or item.get('locationText') or item.get('country') or ''
                if isinstance(place,dict):place=place.get('name') or place.get('city') or ''
                restriction=item.get('applicantRegions') or item.get('applicant_regions') or item.get('locationRestrictions') or []
                if isinstance(restriction,str):restriction=[restriction]
                if not isinstance(restriction,list):restriction=[]
                published=item.get('publishedAt') or item.get('published_at') or item.get('created_at')
                expiry=item.get('expiresAt') or item.get('expires_at')
                description=item.get('description') or item.get('descriptionText') or item.get('description_text') or ''
                j=vacancy(company or 'Employer (Nomado24)',item.get('title'),place,url,description,
                          'Nomado24',published,
                          item.get('workArrangement',item.get('work_arrangement'))=='remote' or item.get('remote') is True,
                          source_board='https://www.nomado24.de',
                          source_attribution='Nomado24',
                          source_original=item.get('source') or '',
                          employer_posting_id=item.get('slug') or '',
                          expires_at=expiry or '',
                          remote_location_restriction=restriction,
                          applicant_region_unverified=True,
                          description_completeness='Nomado24 v2 excerpt' if description else 'Nomado24 v2 listing only')
                if j:seen_urls.add(url);results.append(j)
            has_more=raw.get('hasNext',meta.get('hasNext',False))
            cursor=raw.get('nextCursor',meta.get('nextCursor'))
            if not has_more:break
            if not isinstance(cursor,str) or not cursor or cursor in cursor_seen:
                raise ValueError('Nomado24 v2 cursor absent/repeated while hasNext=true')
            cursor_seen.add(cursor)
            params={'cursor':cursor,'limit':55}
            time.sleep(.3)
    return results



def personio(board):
    """Published employer XML, not the private Personio Recruiting API."""
    slug=board.get('slug','')
    domain=board.get('domain','de')
    if not VALID_ID.fullmatch(slug) or domain not in ('de','com'):
        raise ValueError('Invalid Personio employer feed')
    home=f'https://{slug}.jobs.personio.{domain}'
    url=home+'/xml?language=de'
    req=urllib.request.Request(url,headers={'Accept':'application/xml,text/xml','User-Agent':AGENT})
    with urllib.request.urlopen(req,timeout=18) as response:
        raw=response.read(4_000_001)
    if len(raw)>4_000_000:raise ValueError('Personio XML too large')
    if re.search(rb'<!DOCTYPE|<!ENTITY',raw,re.I):
        raise ValueError('XML DTD/entities not permitted')
    try:root=ET.fromstring(raw)
    except ET.ParseError as err:raise ValueError('Invalid Personio XML') from err
    found=[];seen=set()
    for item in root.findall('.//position')[:300]:
        ident=(item.findtext('id') or '').strip()
        if not ident.isdigit() or ident in seen:continue
        seen.add(ident)
        title=item.findtext('name') or ''
        office=item.findtext('office') or ''
        department=item.findtext('department') or ''
        sub=item.findtext('subcompany') or ''
        description=' '.join((v.findtext('value') or '') for v in item.findall('.//jobDescriptions/jobDescription'))
        created=item.findtext('createdAt') or ''
        supplied_url=item.findtext('url') or ''
        parsed=urlparse(supplied_url)
        # Never invent a per-job apply page that the XML does not supply.
        public_url=supplied_url if parsed.scheme=='https' and parsed.hostname==f'{slug}.jobs.personio.{domain}' else home
        j=vacancy(sub or board.get('company') or slug,title,office,public_url,
                  description+' '+department,'Personio',created,False,
                  source_board=home,employer_posting_id=ident,
                  posting_date_basis='personio_created_at_not_publish_date',
                  application_url_unverified=public_url==home,
                  description_completeness='Public Personio XML description')
        if j:found.append(j)
    return found


def pinpoint(board):
    """Official Pinpoint all-postings JSON, including optional employer date proof."""
    from concurrent.futures import ThreadPoolExecutor
    from date_evidence import public_pinpoint_date
    slug=board.get('slug','')
    if not VALID_ID.fullmatch(slug):raise ValueError('Invalid Pinpoint company slug')
    home=f'https://{slug}.pinpointhq.com'
    raw=request_json(home+'/postings.json',retries=0)
    rows=raw.get('data') if isinstance(raw,dict) else None
    if not isinstance(rows,list):raise ValueError('Invalid Pinpoint postings feed')
    result=[];seen=set()
    # Public Pinpoint postings.json has no standard publication date field.
    # Verify a bounded subset against the employer's JobPosting JSON-LD.
    # Enable explicitly in the GitHub scan workflow; test runs stay offline.
    verify_limit=max(0,min(24,int(os.environ.get('PINPOINT_DATE_VERIFY_LIMIT','0') or '0')))
    eligible=[i for i in rows[:350] if isinstance(i,dict)
              and isinstance(i.get('url'),str) and
              urlparse(i['url']).hostname==f'{slug}.pinpointhq.com']
    selected=sorted(eligible,key=lambda i:0 if ROLE_WORDS.search(str(i.get('title') or '')) else 1)[:verify_limit]
    date_proof={}
    if selected:
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures={pool.submit(public_pinpoint_date,item['url'],f'{slug}.pinpointhq.com'):
                     item['url'] for item in selected}
            for future,url in futures.items():
                try:date_proof[url]=future.result()
                except (ValueError,TypeError):date_proof[url]=''
    for item in rows[:350]:
        if not isinstance(item,dict):continue
        ident=str(item.get('id') or '')
        target=item.get('url')
        if ident in seen or not target:continue
        parsed=urlparse(str(target))
        if parsed.scheme!='https' or parsed.hostname!=f'{slug}.pinpointhq.com':
            continue
        seen.add(ident)
        location=item.get('location')
        if isinstance(location,dict):location=location.get('name')
        department=item.get('department')
        if isinstance(department,dict):department=department.get('name')
        description=' '.join(str(item.get(k) or '') for k in (
            'description','key_responsibilities','skills_knowledge_expertise'))
        employer_posted=date_proof.get(str(target)) or ''
        j=vacancy(board.get('company') or slug,item.get('title'),location or '',
                  target,description+' '+str(department or ''),'Pinpoint',employer_posted,
                  str(item.get('workplace_type') or '').lower()=='remote',
                  expires_at=item.get('deadline_at') or '',
                  employer_posting_id=ident,source_board=home,
                  workplace_type_original=str(item.get('workplace_type') or '')[:40],
                  employment_type_original=str(item.get('employment_type') or '')[:45],
                  posting_date_basis=('pinpoint_employer_jobposting_jsonld_datePosted'
                                     if employer_posted else
                                     'pinpoint_public_feed_no_publication_date'),
                  description_completeness='Official Pinpoint postings JSON')
        if j:result.append(j)
    return result



def serpapi_google_jobs(board):
    """Bounded Google Jobs discovery through the user's SerpApi key.

    Search results are normalized as aggregator-discovered vacancies. A Google
    Jobs result is not treated as an employer-confirmed sponsorship claim.
    """
    api_key=(os.environ.get('SERPAPI_API_KEY') or '').strip()
    if not api_key:
        raise ValueError('SerpApi requires SERPAPI_API_KEY')
    queries=board.get('queries') or ['mechanical engineer','project engineer',
        'quality engineer','manufacturing engineer']
    try:
        budget=max(1,min(12,int(board.get('query_budget',8))))
    except (TypeError,ValueError):
        budget=8
    queries=[str(q).strip() for q in queries if str(q).strip()][:budget]
    stats={'planned_queries':len(queries),'attempted_queries':0,
           'completed_queries':0,'failed_queries':0,'no_data_queries':0,
           'provider_rows':0,'valid_postings':0}
    board['serpapi_run_stats']=stats
    found=[];seen=set()
    location=str(board.get('location') or 'Germany')
    for term in queries:
        stats['attempted_queries']+=1
        params={'engine':'google_jobs','q':term,'location':location,
                'api_key':api_key,'hl':'en'}
        try:
            raw=request_json('https://serpapi.com/search.json?'+urlencode(params),retries=0)
            rows=raw.get('jobs_results') if isinstance(raw,dict) else None
            if not isinstance(rows,list):
                raise ValueError('SerpApi Google Jobs response has no jobs_results array')
            stats['completed_queries']+=1
            stats['provider_rows']+=len(rows)
            if not rows:stats['no_data_queries']+=1
            for item in rows:
                if not isinstance(item,dict):continue
                title=item.get('title') or ''
                company=item.get('company_name') or 'Employer not stated'
                place=item.get('location') or location
                extensions=item.get('detected_extensions') or {}
                if not isinstance(extensions,dict):extensions={}
                links=item.get('apply_options') or []
                target=''
                if isinstance(links,list):
                    target=next((x.get('link') for x in links
                                 if isinstance(x,dict) and str(x.get('link','')).startswith('https://')),'')
                target=target or item.get('share_link') or ''
                description=item.get('description') or ''
                j=vacancy(company,title,place,target,description,'SerpApi · Google Jobs',
                    extensions.get('posted_at') or '',
                    'remote' in str(extensions.get('work_from_home','')).casefold(),
                    source_attribution='Google Jobs via SerpApi',
                    source_original=item.get('via') or '',
                    serpapi_query=term,
                    description_completeness='Google Jobs description' if description else 'Google Jobs listing only',
                    application_url_unverified=not bool(links))
                if j:
                    identity=j['url'].split('#',1)[0]
                    if identity not in seen:
                        seen.add(identity);found.append(j);stats['valid_postings']+=1
        except (urllib.error.HTTPError,urllib.error.URLError,ValueError,TimeoutError,
                json.JSONDecodeError) as exc:
            stats['failed_queries']+=1
            # Do not retain request URLs or credential-bearing exception text.
            if isinstance(exc,urllib.error.HTTPError):
                board['serpapi_last_error']='HTTP '+str(exc.code)
            else:
                board['serpapi_last_error']=type(exc).__name__
    if stats['completed_queries']==0 and stats['failed_queries']:
        raise ValueError('SerpApi all query requests failed ('+str(board.get('serpapi_last_error') or 'provider error')+')')
    return found


def themuse(board):
    """The Muse registered public Jobs API. App key required beyond testing.

    Does not label Muse company editorial pages as employer-owned apply URLs.
    No unsupported applicant-country, date or sponsorship guarantees.
    """
    api_key=(os.environ.get('THE_MUSE_API_KEY') or '').strip()
    if not api_key:
        raise ValueError('The Muse requires registered API key for ongoing use')
    categories=board.get('categories') or [
        'Science and Engineering','Manufacturing and Warehouse',
        'Installation, Maintenance, and Repairs','Project Management',
        'Transportation and Logistics','Energy Generation and Mining']
    found=[];seen=set()
    for category in categories[:6]:
        for page in range(2):
            params={'page':page,'category':category,'api_key':api_key}
            raw=request_json('https://www.themuse.com/api/public/jobs?'+urlencode(params),retries=0)
            posts=raw.get('results') if isinstance(raw,dict) else None
            if not isinstance(posts,list):raise ValueError('The Muse results must be a list')
            for item in posts:
                if not isinstance(item,dict):continue
                refs=item.get('refs') or {}
                if not isinstance(refs,dict):refs={}
                url=refs.get('landing_page') or item.get('url')
                if not url or url in seen:continue
                employer=item.get('company') or {}
                if isinstance(employer,dict):employer=employer.get('name')
                places=item.get('locations') or []
                location=', '.join(str(v.get('name','')) for v in places[:4] if isinstance(v,dict))
                if not location:location='Location not stated'
                description=item.get('contents') or item.get('description') or ''
                j=vacancy(employer or 'Employer (The Muse)',item.get('name') or item.get('title'),
                          location,url,description,'The Muse',item.get('publication_date') or '',
                          any('remote' in str(v.get('name','')).casefold() for v in places if isinstance(v,dict)),
                          source_board='https://www.themuse.com/',
                          source_attribution='The Muse',
                          employer_posting_id=str(item.get('id') or ''),
                          description_completeness='The Muse description' if description else 'The Muse listing only',
                          application_url_unverified=True)
                if j:seen.add(url);found.append(j)
            if len(posts)<20:break
            time.sleep(.35)
    return found


ADAPTERS={'serpapi_google_jobs':serpapi_google_jobs,'nomado24':nomado24,'themuse':themuse,'personio':personio,'pinpoint':pinpoint,'workable':workable,'smartrecruiters':smartrecruiters,'workday':workday,
          'jobicy':jobicy,'remotive':remotive,'himalayas':himalayas}
def fetch_public_source(board):
    return ADAPTERS[board['type']](board)
