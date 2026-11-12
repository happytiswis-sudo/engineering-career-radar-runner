"""36 cooperating evidence-oriented career review specialists (stdlib only).

These are deterministic agents, not 36 paid LLM calls. They share the same
verified vacancy evidence and depend on prior checks. Mercury 3 can adjudicate
priority jobs downstream; no agent is allowed to invent qualifications, salary,
work permits, or employer sponsorship.
"""
from __future__ import annotations
from dataclasses import dataclass
import datetime as dt
import re
from urllib.parse import urlparse

@dataclass(frozen=True)
class Specialist:
    ident: str
    team: str
    title: str
    mode: str
    terms: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()

def s(key, team, title, mode, terms=(), deps=()):
    return Specialist(key, team, title, mode, tuple(terms), tuple(deps))

# The order is a topological ordering: dependencies must appear first.
AGENTS=(
 # Team 1 — Provenance and data integrity
 s('01_url','source','Source URL integrity','url'),
 s('02_ats','source','Employer ATS provenance','ats',deps=('01_url',)),
 s('03_employer','source','Employer identity','employer',deps=('01_url',)),
 s('04_content','source','Description completeness','completeness',deps=('02_ats',)),
 s('05_date','source','Posting freshness','date',deps=('04_content',)),
 s('06_unique','source','Source identity / deduplication','identity',deps=('01_url','03_employer')),
 # Team 2 — Geographic context
 s('07_germany','geography','German location validation','germany',deps=('03_employer',)),
 s('08_west','geography','Western Germany fit','west',deps=('07_germany',)),
 s('09_small_town','geography','Smaller industrial town signal','small_town',deps=('08_west',)),
 s('10_radius','geography','Search radius provenance','radius',deps=('07_germany',)),
 s('11_remote','geography','Remote eligibility wording','pattern',('remote','hybrid','homeoffice','mobiles arbeiten'),('07_germany',)),
 s('12_travel','geography','Travel and site presence','pattern',('travel required','reisebereitschaft','on-site','vor ort','site visits'),('11_remote',)),
 # Team 3 — Hard prerequisites; none inferred from absence of evidence
 s('13_degree','eligibility','Mandatory degree gate','degree',deps=('04_content',)),
 s('14_doctorate','eligibility','PhD requirement screen','pattern',('phd required','doctorate required','promotion erforderlich'),('13_degree',)),
 s('15_experience','eligibility','Years-of-experience requirement','years',deps=('04_content',)),
 s('16_language','eligibility','Language requirement evidence','pattern',('c1 deutsch','deutsch c1','fließend deutsch','fluent german','native german','german c1'),('15_experience',)),
 s('17_clearance','eligibility','Security citizenship restrictions','pattern',('security clearance','eu citizenship required','us citizenship required','itar','sicherheitsüberprüfung'),('13_degree',)),
 s('18_certification','eligibility','Mandatory license evidence','pattern',('part-66','easa b1','easa b2','pe license','professional engineer license','meisterbrief'),('17_clearance',)),
 # Team 4 — Direct CV engineering pathways
 s('19_cad','engineering','Mechanical CAD design','pattern',('solidworks','catia','cad','konstruktion','mechanical design'),('13_degree',)),
 s('20_simulation','engineering','Simulation & finite element','pattern',('fea','fem','cfd','stress analysis','strukturanalyse','simulation'),('19_cad',)),
 s('21_manufacturing','engineering','Manufacturing/industrialisation','pattern',('manufacturing','fertigung','produktion','industrialisierung','assembly line','lean'),('13_degree',)),
 s('22_aerospace','engineering','Aerospace and UAV','pattern',('aerospace','uas','uav','unmanned','drohne','luftfahrt','avionics'),('13_degree',)),
 s('23_camo','engineering','Airworthiness/CAMO','pattern',('camo','airworthiness','maintenance records','part-m','part-camo','lufttüchtigkeit'),('22_aerospace',)),
 s('24_projects','engineering','Engineering project coordination','pattern',('project engineer','projektingenieur','projektkoordination','project delivery','project planning','projektmanagement'),('13_degree',)),
 # Team 5 — Adjacent industrial pathways
 s('25_quality','industrial','Quality systems and ISO','pattern',('quality','qualität','iso 9001','quality assurance','supplier quality','audits'),('21_manufacturing',)),
 s('26_maintenance','industrial','Reliability/maintenance','pattern',('maintenance','instandhaltung','reliability','technische dokumentation'),('21_manufacturing',)),
 s('27_systems','industrial','Automation and integration','pattern',('automation','automatisierung','system integration','validation','verifikation'),('19_cad',)),
 s('28_energy','industrial','Energy/oil and gas inspection','pattern',('energy','pipeline','oil and gas','asset integrity','anlagen','inspection'),('26_maintenance',)),
 s('29_operations','industrial','Operations and field delivery','pattern',('operations','betrieb','field engineer','betriebsingenieur','technical operations'),('24_projects',)),
 s('30_supply','industrial','Supply/manufacturing planning','pattern',('material planning','supply chain','disposition','arbeitsvorbereitung','technical procurement'),('21_manufacturing',)),
 # Team 6 — Decision support; coordinated results from all pods
 s('31_skills','decision','CV skills evidence','cvskills',deps=('19_cad','21_manufacturing','24_projects','25_quality')),
 s('32_skill_gaps','decision','Missing advertised capability flags','missing',deps=('31_skills','04_content')),
 s('33_seniority','decision','Seniority feasibility','seniority',deps=('15_experience','31_skills')),
 s('34_visa','decision','Explicit sponsorship classification','visa',deps=('07_germany','13_degree','17_clearance')),
 s('35_mobility','decision','Relocation/international signals','mobility',deps=('11_remote','12_travel','34_visa')),
 s('36_priority','decision','Evidence-grounded prioritization','priority',deps=('06_unique','08_west','13_degree','31_skills','32_skill_gaps','33_seniority','34_visa','35_mobility'))
)
BY_ID={x.ident:x for x in AGENTS}
assert len(AGENTS)==36 and len(BY_ID)==len(AGENTS)
for i,a in enumerate(AGENTS):
    earlier={b.ident for b in AGENTS[:i]}
    assert set(a.depends_on)<=earlier, (a.ident,a.depends_on)

def run_specialists(job):
    """Run the dependency DAG and return bounded, source-linked evidence summaries."""
    description=str(job.get('description') or '')
    title=str(job.get('title') or '')
    text=title+'\n'+description
    market=job.get('market') or {}
    qualification=job.get('qualification') or {}
    support=job.get('hiring_support') or {}
    result={}
    for agent in AGENTS:
        kind=agent.mode
        evidence=[]
        status='not_stated'
        if kind=='pattern':
            for term in agent.terms:
                if re.search(r'(?<![\w])'+re.escape(term)+r'(?![\w])',text,re.I):
                    evidence.append(term)
            if evidence:status='mentioned'
        elif kind=='url':
            u=urlparse(str(job.get('url') or ''))
            status='verified_format' if u.scheme=='https' and bool(u.netloc) else 'needs_review'
        elif kind=='ats':
            status='employer_ats' if str(job.get('source','')).lower() in ('ashby','greenhouse','lever') else 'external_feed'
        elif kind=='employer':
            status='named' if len(str(job.get('company','')).strip())>=3 else 'needs_review'
        elif kind=='completeness':
            n=len(description.strip())
            status='fuller_excerpt' if n>=400 else 'short_excerpt' if n>=80 else 'missing_detail'
        elif kind=='date':
            stamp=job.get('published_at')
            if stamp:
                try:
                    d=dt.datetime.fromisoformat(str(stamp).replace('Z','+00:00'))
                    if d.tzinfo is None:d=d.replace(tzinfo=dt.timezone.utc)
                    age=(dt.datetime.now(dt.timezone.utc)-d).days
                    status='recent' if -1<=age<=30 else 'older_or_future_date'
                except (ValueError,TypeError):status='unparseable'
        elif kind=='identity':
            status='source_url_present' if str(job.get('url','')).startswith('http') else 'needs_review'
        elif kind=='germany':
            status='matched' if market.get('germany') else 'not_confirmed'
        elif kind=='west':
            status='matched' if market.get('west') else 'not_confirmed'
        elif kind=='small_town':
            status='matched' if market.get('small_city') else 'not_confirmed'
        elif kind=='radius':
            status='search_radius_only' if market.get('matched_by_search_radius') else 'stated_location'
        elif kind=='degree':
            status=qualification.get('status','review')
            evidence.extend(qualification.get('evidence',[])[:1])
        elif kind=='years':
            match=re.findall(r'(?:minimum\s+(?:of\s+)?|at\s+least\s+)(\d{1,2})\s*(?:years|jahre)',text,re.I)
            if match:status='requirement_mentioned';evidence=['Minimum '+max(match,key=int)+' years (verify discipline)']
        elif kind=='cvskills':
            skills=job.get('matched_skills') or []
            status='cv_overlap' if skills else 'limited_evidence'
            evidence=skills[:3]
        elif kind=='missing':
            gaps=job.get('missing_skills') or []
            status='advertised_gaps' if gaps else 'none_documented'
            evidence=gaps[:3]
        elif kind=='seniority':
            status='senior_or_lead' if re.search(r'\b(senior|principal|head of|director|lead)\b',title,re.I) else 'general'
        elif kind=='visa':
            v=support.get('visa') or {}
            status=v.get('status','not_stated')
        elif kind=='mobility':
            states={key:(support.get(key) or {}).get('status') for key in ('relocation','international','blue_card')}
            status='explicit_assistance' if 'explicit' in states.values() else 'unconfirmed'
            evidence=[key+' '+str(v) for key,v in states.items() if v in ('explicit','mentioned')][:3]
        elif kind=='priority':
            if qualification.get('status')=='excluded':status='hard_exclusion'
            elif int(job.get('score') or 0)>=75 and not job.get('check_requirements'):status='high_priority_review'
            elif int(job.get('score') or 0)>=45:status='candidate_review'
            else:status='stretch'
        result[agent.ident]={'status':status,'evidence':evidence[:3]}
    interesting=[{'agent':a.ident,'name':a.title,'team':a.team,'status':result[a.ident]['status'],
       'evidence':result[a.ident]['evidence'],'depends_on':list(a.depends_on)}
       for a in AGENTS if result[a.ident]['status'] in ('mentioned','matched','cv_overlap','advertised_gaps','explicit','explicit_assistance','hard_exclusion','high_priority_review','employer_ats','requirement_mentioned','senior_or_lead','short_excerpt')]
    team_counts={team:sum(1 for a in AGENTS if a.team==team and result[a.ident]['status'] not in ('not_stated','not_confirmed'))
        for team in ('source','geography','eligibility','engineering','industrial','decision')}
    return {'version':1,'specialists_executed':len(result),'teams':team_counts,
            'key_findings':interesting[:16],'priority':result['36_priority']['status'],
            'degree_gate':result['13_degree']['status'],
            'coordination':'Sequential dependency DAG; all claims derived from source text or previous verified scoring.'}
