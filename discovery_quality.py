"""Opportunity freshness and employer diversity controls.

These functions rank already-qualified postings, never waive eligibility or
interpret unknown posting dates as evidence of a recent advert.
"""
from __future__ import annotations
import json
from pathlib import Path
from career_intelligence import published_on
from novelty import job_key

def load_prior_job_keys(path):
    """Optional prior-run hints downloaded privately by GitHub Actions.

    Failure is non-fatal; never confuse an unavailable registry with proof that
    all vacancies are new.
    """
    try:
        doc=json.loads(Path(path).read_text(encoding='utf-8'))
        if doc.get('schema_version')!=1 or not isinstance(doc.get('entries'),dict):
            return None
        return set(doc['entries'])
    except (OSError,ValueError,TypeError):
        return None

def freshness_counts(jobs):
    counts={'within_24h':0,'within_7d':0,'within_30d':0,
            'older_than_30d':0,'date_unknown':0}
    for job in jobs:
        age=published_on(job.get('published_at'))['age_days']
        if age is None:counts['date_unknown']+=1
        elif age<=1:
            counts['within_24h']+=1;counts['within_7d']+=1;counts['within_30d']+=1
        elif age<=7:
            counts['within_7d']+=1;counts['within_30d']+=1
        elif age<=30:counts['within_30d']+=1
        else:counts['older_than_30d']+=1
    return counts

def review_candidates(candidates,limit,prior_keys=None):
    """Select diverse employers for limited AI review, favoring fresh/unseen.

    This does not remove anything from published search results and uses only
    CV-screened, qualification-eligible candidates supplied by the caller.
    """
    if limit<=0:return []
    def key(job):
        age=published_on(job.get('published_at'))['age_days']
        jid=job_key(job)
        # Unknown history must not be labeled "new"; it receives no novelty boost.
        unseen=(prior_keys is not None and jid is not None and jid not in prior_keys)
        recent=3 if age is not None and age<=1 else 2 if age is not None and age<=7 else 1 if age is not None and age<=30 else 0
        score=float(job.get('rule_score',job.get('score',0)) or 0)
        market=job.get('market') or {}
        # Country-restricted remote postings remain in Results, but should not
        # monopolize AI review capacity ahead of accessible recent jobs.
        restrictions=job.get('remote_location_restriction') or []
        if isinstance(restrictions,str):restrictions=[restrictions]
        restricted_remote=bool(job.get('remote') and restrictions)
        # Technical / cargo titles merit investigation before unrelated HR roles.
        from re import search,IGNORECASE
        relevant_title=bool(search(
            r'airport|airside|cargo|ramp|baggage|flughafen|luftfracht|'
            r'engineer|ingenieur|techniker|technician|quality|maintenance|'
            r'logistics|logistik|manufactur|production|produktion|instandhaltung|'
            r'mechanic|mechanisch|project|projekt|warehouse|lager|facilities',
            str(job.get('title') or ''),IGNORECASE))
        within_week=bool(age is not None and age<=7)
        return (int(not restricted_remote),int(score>=35),int(within_week and unseen),
                int(within_week),int(relevant_title),int(unseen),int(score>=55),
                int(bool(market.get('west'))),score)
    ranked=sorted(candidates,key=key,reverse=True)
    # Keep employer diversity without making the employer itself a hard
    # exclusion: large companies often publish several genuinely distinct roles.
    # Bound each employer to three AI-review slots, then fill any remaining slots
    # from the ranked list. Persistent vacancy identity is handled by job_key.
    picked=[];company_counts={};used=set()
    for job in ranked:
        company=' '.join(str(job.get('company') or '').casefold().split())
        if company and company_counts.get(company,0)>=3:continue
        picked.append(job);used.add(id(job))
        if company:company_counts[company]=company_counts.get(company,0)+1
        if len(picked)>=limit:return picked
    for job in ranked:
        if id(job) not in used:
            picked.append(job)
            if len(picked)>=limit:break
    return picked

def load_prior_query_metrics(path):
    """Only historical aggregate query yields; never read CV content."""
    try:
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        metrics=data.get('source_query_metrics') or []
        if not isinstance(metrics,list):return []
        return [m for m in metrics[:400] if isinstance(m,dict)
            and isinstance(m.get('city'),str) and isinstance(m.get('query'),str)]
    except (OSError,ValueError,TypeError,AttributeError):
        return []


AIRPORT_SEARCH_CITIES=(
    'Frankfurt am Main','München','Düsseldorf','Köln','Stuttgart',
    'Hamburg','Berlin','Hannover','Bremen','Nürnberg',
    'Leipzig','Dortmund'
)
AIRPORT_ROTATING_TERMS=(
    'Bodenabfertigung','Ramp Agent','Vorfeld','Gepäckabfertigung',
    'Luftfracht','Cargo Handling','Cargo Warehouse','Airport Logistics',
    'ULD','Aircraft Turnaround','Flugzeugabfertigung','Ground Handling',
    'Ground Support Equipment','Flughafen Wartung','Flughafen Instandhaltung',
    'Airport Facilities','Flughafen Technik','Flughafen Materialwirtschaft',
    'Luftfrachtabfertigung','Airport Operations','Swissport','dnata',
    'Menzies Aviation','Worldwide Flight Services','Fraport',
    'Rechenzentrum Techniker','Facility Maintenance','Industrie Logistik',
    'Instandhaltungsplaner','Verpackungsindustrie',
    # Broad BA vocabulary recovery for industrial/engineering tracks with zero
    # raw results. Keep city rotation bounded; all postings still pass filters.
    'Ingenieur','Techniker','Technische Planung','Konstruktion',
    'Maschinenbau','Elektrotechnik','Mechatronik','Qualitätsmanagement',
    'Qualitätssicherung','Fertigung','Produktion','Arbeitsvorbereitung',
    'Projektmanagement Technik','Wartung','Instandhaltung','Prüftechnik',
    'Werkstofftechnik','Prozessingenieur','Betriebstechnik',
    'Anlagenmechaniker','Industriemechaniker','Logistikingenieur',
    'Luftfahrttechnik','Flugzeugmechaniker','Luftfahrzeugtechnik',
    'Technischer Zeichner','CAD Konstrukteur','Bauingenieur',
    'Umwelttechnik','Energieingenieur','Automatisierungstechnik',
    'Technischer Einkauf','Supply Chain','Produktionsplaner'
)

def rotating_airport_boards(existing,when=None,limit=24,prior_metrics=None):
    """Rotate bounded BA queries across airport cities and industrial families.

    Does not infer that a company or airport is currently hiring. A result must
    still pass the original source, role, CV and eligibility checks.
    """
    from datetime import datetime,timezone
    date=when or datetime.now(timezone.utc).date()
    existing_keys={(str(b.get('city','')).casefold(),str(b.get('query','')).casefold())
                   for b in existing if b.get('type')=='bundesagentur'}
    combos=[]
    for ix,term in enumerate(AIRPORT_ROTATING_TERMS):
        for k in range(3):
            city=AIRPORT_SEARCH_CITIES[(ix*5+k*7)%len(AIRPORT_SEARCH_CITIES)]
            key=(city.casefold(),term.casefold())
            if key not in existing_keys:combos.append((city,term))
    if not combos:return []
    start=(date.toordinal()*11)%len(combos)
    candidates=combos[start:]+combos[:start]
    # Best-effort historical feedback: reserve at most 6 queries for previously
    # productive, fresh CV-backed new listings. Explore elsewhere with the rest.
    previous=prior_metrics or []
    productive=sorted(
        (m for m in previous if int(m.get('unseen_recent_cv_matches') or 0)>0),
        key=lambda m:(int(m.get('unseen_recent_cv_matches') or 0),
                      int(m.get('cv_matches') or 0)),reverse=True)
    allowed={(city.casefold(),term.casefold()) for city,term in combos}
    winners=[];prior_rotated=set()
    for m in previous:
        key=(str(m.get('city','')).casefold(),str(m.get('query','')).casefold())
        if m.get('rotating_search'):prior_rotated.add(key)
    for m in productive:
        key=(str(m.get('city','')).casefold(),str(m.get('query','')).casefold())
        if key in allowed and all((c.casefold(),t.casefold())!=key for c,t in winners):
            winners.append((str(m['city']),str(m['query'])))
        if len(winners)>=min(6,limit//3):break
    # Do not immediately repeat zero-yield rotating searches when enough other
    # city/term pairs exist; retain a fallback to preserve the query budget.
    candidates=(winners+
        [(c,t) for c,t in candidates if (c.casefold(),t.casefold()) not in prior_rotated]+
        [(c,t) for c,t in candidates if (c.casefold(),t.casefold()) in prior_rotated])
    added=[];used=set()
    for city,term in candidates:
        key=(city.casefold(),term.casefold())
        if key in used:continue
        used.add(key)
        added.append({'type':'bundesagentur','slug':'rotating-airport',
                      'company':'BA rotating airport/industry · '+city+' · '+term,
                      'city':city,'query':term,'radius':55,'size':45,'pages':2,
                      'rotating_search':True})
        if len(added)>=limit:break
    return added
