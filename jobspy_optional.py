"""Optional permission-gated JobSpy jobs from multiple job-board platforms.

No scraping is performed without an explicit per-site authorization configuration.
This project does NOT provide permission to scrape a site's content. Check each
site's current policies or obtain its written authorization before enabling it.
No login, proxy, CAPTCHA bypass or retry-on-blocking is used.
"""
from __future__ import annotations
import os
import re
import logging
import time
from datetime import datetime, date, timezone
from urllib.parse import urlparse
from public_source_adapters import vacancy
from industry_search import TRACK_TERMS

SITES=('linkedin','indeed','glassdoor','zip_recruiter','google',
       'bayt','naukri','bdjobs','hellowork')
SITE_TYPES=tuple('jobspy_'+site for site in SITES)
# The search plan is built from the live user-editable role catalog, not a
# static list of two preferred industries. One broad query and one rotating
# real catalog title per track make every track searchable on each deep scan
# and rotate *every* title in that track across subsequent runs.
RESULTS_PER_QUERY=50

def requested_results_per_query(env=None,override=None):
    """Provider result target, bounded by the operator setting and adapter profile."""
    env=os.environ if env is None else env
    configured=str(env.get('JOBSPY_RESULTS_PER_QUERY') or '').strip()
    try:value=int(configured) if configured else int(override or RESULTS_PER_QUERY)
    except (ValueError,TypeError):value=RESULTS_PER_QUERY
    return min(75,max(10,value))

def catalog_search_terms(site,catalog_roles,requested_roles=None,requested_tracks=None,
                         depth='deep',when=None,run_rotation=0):
    """Plan inclusive per-source searches; provider failures are tracked separately.

    User-entered roles are never truncated to two; without roles, all selected
    catalog tracks are considered. The second title changes daily so less
    common/newly added titles are not permanently skipped. Explicit one-off
    run rotation avoids repeat searches for identical terms on the same day.
    """
    when=when or datetime.now(timezone.utc).date()
    rotation=max(0,int(run_rotation or 0))
    explicit=list(dict.fromkeys(str(x).strip() for x in (requested_roles or [])
                            if isinstance(x,str) and x.strip()))
    if explicit:return explicit
    tracks={}
    for record in catalog_roles:
        if not isinstance(record,dict):continue
        title=str(record.get('title') or '').strip()
        track=str(record.get('track') or '').strip()
        if not title or not track:continue
        if requested_tracks and track not in requested_tracks:continue
        tracks.setdefault(track,[]).append(title)
    terms=[]
    for track in sorted(tracks):
        titles=list(dict.fromkeys(tracks[track]))
        aliases=TRACK_TERMS.get(track) or []
        if aliases:
            terms.append(aliases[(when.toordinal()+rotation+SITES.index(site))%len(aliases)])
        else:
            terms.append(titles[0])
        if depth=='deep' and len(titles)>1:
            # Exclude the already-selected broad query from the rotation pool.
            # Skipping it after modulo can otherwise produce the same term on
            # consecutive scans (offset 0 -> next title, offset 1 -> same title).
            candidates=[title for title in titles if title!=terms[-1]]
            offset=(when.toordinal()+rotation+SITES.index(site)*7+
                    sum(ord(c) for c in track))%len(candidates)
            terms.append(candidates[offset])
    return list(dict.fromkeys(terms))

# Supplement the nationwide search on productive Indeed with a small,
# country-qualified rotating city sweep. Never use it on blocked platforms.
CITY_SWEEP_GERMANY=(
    'Frankfurt am Main','Leipzig','Stuttgart','Hamburg','Düsseldorf',
    'Hannover','Bremen','Dresden','Dortmund','Nürnberg','Köln',
    'Erfurt','Magdeburg','Kassel','Münster','Rostock')
CITY_SWEEP_WEST=(
    'Frankfurt am Main','Stuttgart','Düsseldorf','Hannover','Bremen',
    'Dortmund','Köln','Münster','Kassel','Essen','Duisburg','Mainz')
CITY_SWEEP_ROLES=(
    'airport ground handling','air cargo operations','ground support equipment technician',
    'airport facilities technician','industrial maintenance technician',
    'supplier quality engineer','production planning technician',
    'manufacturing process engineer','warehouse logistics coordinator',
    'technical project coordinator','industrial inspection technician',
    'aircraft turnaround coordinator')

def indeed_city_sweep(profile=None,run_rotation=0):
    """Two small city-specific, country-qualified probes per Deep German scan.

    These supplement, never replace, one broad query per career track on the
    main Indeed board. The city and role group rotate per run to expand
    geographic reach without growing the total query count unboundedly.
    """
    profile=profile or {'region':'germany','depth':'deep','cities':[],'roles':[]}
    if profile.get('depth')!='deep' or profile.get('region') not in ('germany','west'):
        return []
    if profile.get('roles'):return []
    specified=[str(c).strip() for c in (profile.get('cities') or []) if str(c).strip()]
    cities=list(dict.fromkeys(specified)) if specified else list(
        CITY_SWEEP_GERMANY if profile.get('region')=='germany' else CITY_SWEEP_WEST)
    if not cities:return []
    rotation=max(0,int(run_rotation or 0))
    offset=rotation%len(cities)
    chosen=[cities[(offset+i)%len(cities)] for i in range(min(2,len(cities)))]
    output=[]
    for index,city in enumerate(chosen):
        first=(rotation+index*5)%len(CITY_SWEEP_ROLES)
        terms=[CITY_SWEEP_ROLES[(first+step)%len(CITY_SWEEP_ROLES)]
               for step in range(4)]
        output.append({'city':city,'queries':terms})
    return output

def tidy_provider_description(value):
    """Undo a JobSpy Markdown conversion artifact like **I****n****s****i****d****e**."""
    if not isinstance(value,str):return ''
    return re.sub(r'(?:\*\*[^\W_]\*\*){4,}',
                  lambda match:match.group().replace('**',''),value)


def linkedin_experiment_mode(env=None):
    """Two-step operator consent for LinkedIn; defaults to no network access."""
    env=os.environ if env is None else env
    return ('live' if str(env.get('JOBSPY_LINKEDIN_MODE','')).strip().lower()=='live'
            else 'offline')


def authorized_sites(env=None):
    env=os.environ if env is None else env
    names={s.strip().lower() for s in env.get('JOBSPY_AUTHORIZED_SITES','').split(',') if s.strip()}
    sites=names.intersection(SITES)
    # Three distinct operator choices: platform selected, independent written
    # authorization confirmed, AND live experiment deliberately activated.
    # Default mode is offline. No LinkedIn requests merely from a checkbox.
    if (env.get('LINKEDIN_RETRIEVAL_AUTHORIZED')!='yes'
            or linkedin_experiment_mode(env)!='live'):
        sites.discard('linkedin')
    return sites

def site_for_type(value):
    site=str(value or '').removeprefix('jobspy_')
    if site not in SITES or value!='jobspy_'+site:
        raise ValueError('Unsupported JobSpy source platform')
    return site

def zip_location_country(profile):
    """Only explicitly country-qualified US/Canadian cities, never a German guess."""
    if not isinstance(profile,dict) or profile.get('region')!='world':
        return ''
    cities=profile.get('cities') or []
    if not isinstance(cities,list) or not cities:return ''
    city=str(cities[0]).lower()
    if re.search(r'\b(?:canada)\b',city):return 'Canada'
    if re.search(r'\b(?:usa|u\.s\.a\.|united states)\b',city):return 'USA'
    return ''

def jobspy_board_status(source_type,env=None,profile=None):
    """Explain configuration and provider geography separately.

    A GitHub variable is a requested source configuration, NOT independent
    proof of website permission, success or available vacancies.
    """
    site=site_for_type(source_type)
    if site=='google':
        return 'unsupported_provider'
    env=os.environ if env is None else env
    requested={v.strip().lower() for v in env.get('JOBSPY_AUTHORIZED_SITES','').split(',')}
    if site=='linkedin' and site in requested:
        if linkedin_experiment_mode(env)!='live':
            return 'offline_test_ready'
        if env.get('LINKEDIN_RETRIEVAL_AUTHORIZED')!='yes':
            return 'requires_independent_authorization'
    if site not in authorized_sites(env):
        return 'disabled_permission_required'
    if site=='zip_recruiter' and not zip_location_country(profile):
        return 'unsupported_geography'
    return 'configured_unverified'

def jobspy_for_board(board):
    site=site_for_type(board.get('type'))
    if site=='google':
        raise ValueError('JobSpy Google Jobs is unsupported; configure SERPAPI_API_KEY and select the SerpApi Google Jobs source instead')
    if site not in authorized_sites():
        raise ValueError('JobSpy '+site+' disabled: site-specific authorization not configured')
    # ZipRecruiter is US/Canada-only in JobSpy; do not silently reinterpret
    # a Germany search as a US query or return inapplicable locations.
    country=(board.get('country') or 'Germany')
    if site=='zip_recruiter' and country not in ('USA','Canada'):
        raise ValueError('JobSpy ZipRecruiter supports USA/Canada only; incompatible search country')
    try:
        from jobspy import scrape_jobs
    except ImportError as exc:
        raise ValueError('python-jobspy not installed for an authorized site') from exc
    location=str(board.get('location') or 'Germany')[:90]
    phrases=board.get('queries') or []
    if not isinstance(phrases,list):phrases=[]
    phrases=list(dict.fromkeys(x.strip()[:85] for x in phrases
                              if isinstance(x,str) and x.strip()))
    # Every selected query is attempted unless the provider explicitly blocks
    # or rate-limits the source. No silent first-two-query truncation.
    wanted=requested_results_per_query(override=board.get('results_per_query'))
    try:
        query_delay=min(30,max(0,int(board.get('linkedin_query_delay_seconds',0))))
    except (TypeError,ValueError):
        query_delay=0
    stats={'planned_queries':len(phrases),'results_requested_per_query':wanted,'attempted_queries':0,
           'completed_queries':0,'failed_queries':0,'no_data_queries':0,'stop_reason':'',
           'cursor_advance_count':0,'query_delay_seconds':query_delay if site=='linkedin' else 0,
           'provider_rows':0,'valid_postings':0,'invalid_rows':0,
           'duplicate_rows':0,'description_present':0,'direct_apply_links':0}
    board['jobspy_run_stats']=stats
    seen=set()
    output=[]
    # Some JobSpy adapters log HTTP 403 and return an empty DataFrame instead of
    # throwing; capture that provider's own diagnostic without scraping around
    # the restriction, so the remaining catalog queries aren't requested blindly.
    class ErrorSignal(logging.Handler):
        def __init__(self):
            super().__init__(level=logging.ERROR)
            self.messages=[]
        def emit(self,record):
            try:
                msg=record.getMessage().lower()
                if '403' in msg or '429' in msg or 'no job data returned' in msg:
                    self.messages.append(msg[:160])
            except Exception:
                pass
    provider_logger=logging.getLogger('jobspy.'+site)
    for query_index,phrase in enumerate(phrases):
        if site=='linkedin' and query_index and query_delay:
            time.sleep(query_delay)
        stats['attempted_queries']+=1
        args={'site_name':[site],'search_term':phrase,'location':location,
              'results_wanted':wanted,'hours_old':168,
              'fetch_description':(site=='linkedin' and
                   os.environ.get('JOBSPY_LINKEDIN_FETCH_DESCRIPTION')=='yes'),
              'proxies':None,'verbose':0}
        if site in ('indeed','glassdoor'):
            args['country_indeed']=country
        if site=='google':
            args['google_search_term']=phrase+' jobs in '+location
        signal=ErrorSignal()
        provider_logger.addHandler(signal)
        try:
            frame=scrape_jobs(**args)
        except Exception as exc:
            # Expose bounded, safe failure categories without URLs, cookies or
            # exception traces in the published public source audit.
            detail=str(exc).lower()
            if re.search(r'(?<!\d)403(?!\d)|forbidden|blocked',detail):
                reason='HTTP 403 / source blocked (no bypass attempted)'
            elif re.search(r'(?<!\d)429(?!\d)|rate limit',detail):
                reason='HTTP 429 / rate limited (no bypass attempted)'
            elif 'no job data returned' in detail:
                reason='provider returned no job data'
            else:
                reason=type(exc).__name__
            stats['failed_queries']+=1
            if reason.startswith(('HTTP 403','HTTP 429')):
                stats['stop_reason']=reason
                stats['provider_blocked']=True
                # Never retry or bypass explicit access restrictions. Preserve
                # already gathered jobs and disclose partial coverage.
                if not output:raise ValueError('JobSpy '+site+': '+reason) from None
                break
            # Non-blocking errors consume this term so the queue cannot stall.
            stats['cursor_advance_count']+=1
            # A single empty/unavailable search must not cancel the other
            # career tracks for an otherwise accessible source.
            continue
        finally:
            provider_logger.removeHandler(signal)
        if any('403' in message or '429' in message for message in signal.messages):
            reason=('HTTP 403 / source blocked (provider logged)' if
                    any('403' in message for message in signal.messages) else
                    'HTTP 429 / rate limited (provider logged)')
            stats['failed_queries']+=1
            stats['stop_reason']=reason
            stats['provider_blocked']=True
            if not output:raise ValueError('JobSpy '+site+': '+reason)
            break
        if any('no job data returned' in message for message in signal.messages):
            # JobSpy Google can log an unavailable/no-data provider response
            # without raising, despite having no usable listing result. Never
            # mislabel these 68 attempts as 68 successful queries.
            stats['no_data_queries']+=1
            stats['cursor_advance_count']+=1
            continue
        stats['completed_queries']+=1
        stats['cursor_advance_count']+=1
        for item in frame.to_dict('records')[:wanted]:
            stats['provider_rows']+=1
            if not isinstance(item,dict):
                stats['invalid_rows']+=1
                continue
            direct=item.get('job_url_direct')
            if not isinstance(direct,str) or not direct.startswith('https://'):
                direct=''
            listing=item.get('job_url')
            link=direct or listing
            if not isinstance(link,str) or not link.startswith(('https://','http://')):
                stats['invalid_rows']+=1
                continue
            if link in seen:
                stats['duplicate_rows']+=1
                continue
            seen.add(link)
            original_date=item.get('date_posted')
            posted=(original_date if isinstance(original_date,str)
                    else original_date.isoformat() if isinstance(original_date,(datetime,date))
                    else '')
            description=tidy_provider_description(item.get('description'))
            record=vacancy(item.get('company'),item.get('title'),item.get('location'),
                link,description,'JobSpy / '+site,posted,item.get('is_remote') is True,
                source_attribution='JobSpy / '+site,
                jobspy_site=site,
                jobspy_aggregator_listing_url=(listing if isinstance(listing,str) and
                    listing.startswith('https://') else ''),
                jobspy_direct_employer_link=bool(direct),
                application_url_unverified=not bool(direct),
                description_completeness='JobSpy feed text' if description else 'No job description supplied',
                posting_date_basis='jobspy_aggregator_reported_date',
                source_board='https://'+site.replace('_','')+'.com')
            if record:
                stats['valid_postings']+=1
                if description:stats['description_present']+=1
                if direct:stats['direct_apply_links']+=1
                output.append(record)
            else:
                stats['invalid_rows']+=1
    if stats['completed_queries']==0 and not output and (
            stats['failed_queries'] or stats['no_data_queries']):
        reason=('provider returned no usable data for '+str(stats['no_data_queries'])+
                ' searches' if stats['no_data_queries'] else
                'no search queries completed; provider errors')
        raise ValueError('JobSpy '+site+': '+reason)
    return output

def linkedin_jobspy(board):
    """Backward-compatible guarded adapter for existing tests/board definitions."""
    return jobspy_for_board({**board,'type':'jobspy_linkedin'})
