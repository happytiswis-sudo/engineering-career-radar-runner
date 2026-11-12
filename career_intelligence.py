"""Additional evidence-aware career analysis teams (12 deterministic agents).

Sponsorship is NEVER assumed from Germany/English-language status.
A low title-fit score is not evidence that a candidate is unable to do a job.
Publication-date uncertainty is explicit rather than fabricated.
"""
from __future__ import annotations
import datetime as dt
import re
from germany import hiring_signals

def published_on(value,now=None):
    now=now or dt.datetime.now(dt.timezone.utc)
    if value is None or value=='':return {'age_days':None,'bucket':'unknown','label':'Publication date not supplied'}
    try:
        if isinstance(value,(int,float)) or (isinstance(value,str) and value.strip().isdigit()):
            raw=float(value)
            if raw>10**11:raw/=1000
            d=dt.datetime.fromtimestamp(raw,dt.timezone.utc)
        else:
            v=str(value).strip()
            if len(v)==10 and re.fullmatch(r'\d{4}-\d{2}-\d{2}',v):
                # Whole-day granularity, no fictitious clock time.
                d=dt.datetime.fromisoformat(v).replace(tzinfo=dt.timezone.utc)
            else:
                d=dt.datetime.fromisoformat(v.replace('Z','+00:00'))
                if d.tzinfo is None:d=d.replace(tzinfo=dt.timezone.utc)
        elapsed=(now-d).total_seconds()/86400
        if elapsed< -1 or elapsed>3650:return {'age_days':None,'bucket':'unknown','label':'Invalid / future publication date'}
        age=round(max(0,elapsed),3)  # retain fractional days; 36h is NOT 'within 24 hours'
        return {'age_days':age,'bucket':'day' if age<=1 else 'week' if age<=7 else 'month' if age<=30 else 'quarter' if age<=90 else 'older',
                'label':'Posted within 24 hours' if age<=1 else 'Posted within 7 days' if age<=7 else 'Posted within 30 days' if age<=30 else 'Posted within 90 days' if age<=90 else 'Older than 90 days'}
    except (ValueError,TypeError,OSError,OverflowError):
        return {'age_days':None,'bucket':'unknown','label':'Publication date unavailable / invalid'}

def recent_enough(job,max_age):
    if max_age in ('all',None,''):return True
    freshness=job.get('freshness') or published_on(job.get('published_at'))
    if max_age=='unknown':return freshness['age_days'] is None
    if max_age not in ('1','7','30','90'):return True
    return freshness['age_days'] is not None and freshness['age_days']<=int(max_age)

def hiring_opportunity(hiring,market=None):
    """Differentiate *proven* assistance from *possible to ask* about it."""
    statuses={k:(v.get('status') if isinstance(v,dict) else None) for k,v in (hiring or {}).items()}
    positives=[k for k,v in statuses.items() if v=='explicit']
    negatives=[k for k,v in statuses.items() if v=='not_offered']
    if 'visa' in negatives:
        tier='visa_not_offered'
    elif any(k in positives for k in ('visa','relocation','international','blue_card')):
        tier='assistance_advertised'
    elif statuses.get('visa')=='mentioned' or statuses.get('blue_card')=='mentioned':
        tier='visa_process_mentioned'
    elif market and market.get('germany'):
        tier='unconfirmed_germany'
    else:
        tier='unconfirmed_other'
    return {'tier':tier,'confirmed_assistance':bool(positives),
            'explicit_types':positives,'negative_types':negatives,
            'can_inquire':tier in ('visa_process_mentioned','unconfirmed_germany','unconfirmed_other'),
            'warning':'German location, an English advert or EU Blue Card mention does not prove employer sponsorship.'}

def capability_assessment(job):
    skills=list(job.get('matched_skills') or [])
    gaps=list(job.get('missing_skills') or [])
    risks=list(job.get('check_requirements') or [])
    qual=job.get('qualification') or {}
    role=float((job.get('score_components') or {}).get('role') or 0)
    if qual.get('status')=='excluded':
        # Keep the same stable capability contract as eligible jobs. Without
        # this field, mandatory-degree exclusions crash the entire scanner when
        # extended agents or the applicant-path classifier read the result.
        return {'tier':'mandatory_ineligible','capability_score':0,'transferable':False,
                'open_to_junior_roles':False,
                'explanation':'Mandatory credential not demonstrated; do not describe as eligible.'}
    # The advert's body decides experience level. Title-only senior labels are
    # retained as a weak clue and exposed separately from explicit requirements.
    title=str(job.get('title',''))
    body=str(job.get('description') or '').casefold()
    junior_terms=(
        r'\bjunior\b',r'\bentry[ -]?level\b',r'\bgraduate\b',
        r'\btrainee\b',r'\bberufseinsteiger\b',r'\bberufseinstieg\b',
        r'\beinsteiger\b',r'\babsolvent(?:in|en)?\b',r'\bberufsanfänger\b',
        r'\bberufserfahrung nicht erforderlich\b',r'\bfirst (?:professional )?experience\b',
        r'\bno prior experience required\b',
        r'\b(erste|erste[nr]?)\s+berufserfahrung\b',
        r'\b0\s*[-–]?\s*2\s+(?:years?|jahre?)\b')
    senior_terms=(
        r'\b(at least|minimum of|minimum)\s*[5-9]\+?\s*(?:years?|jahre?)\b',
        r'\b[5-9]\+\s+(?:years?|jahre?)\s+(?:of )?(?:relevant )?(?:professional )?experience\b',
        r'\bmindestens\s+[5-9]\s+jahre?\s+berufserfahrung\b',
        r'\bmanage(?:s|d)?\s+(?:a |the )?(?:team|department|function|people)\b',
        r'\bline management\b',r'\bpeople management\b',
        r'\b(?:direct|line) reports?\b',r'\bteam leadership\b',
        r'\bleadership responsibility\b',r'\bbudget ownership\b',
        r'\bstrategic ownership\b',r'\bpersonalverantwortung\b',
        r'\bteamleitung\b',r'\bfachliche und disziplinarische führung\b',
        r'\bdisziplinarische führung\b')
    explicit_junior=any(re.search(p,body,re.I) for p in junior_terms)
    def positive_seniority_evidence(patterns,text):
        for pattern in patterns:
            for match in re.finditer(pattern,text,re.I):
                prefix=text[max(0,match.start()-55):match.start()]
                negation=re.search(r'\b(?:no|not|without|never|kein(?:e|en)?|nicht|keine)\b',prefix,re.I)
                if negation:
                    contrast=re.search(r'\b(?:but|however|except|yet|sondern)\b',prefix[negation.end():],re.I)
                    if not contrast:continue
                return True
        return False
    senior_evidence=positive_seniority_evidence(senior_terms,body)
    title_senior_signal=bool(re.search(r'\b(senior|lead|principal|manager|head of|director|staff engineer)\b',title,re.I))
    junior_signal=bool(explicit_junior and not senior_evidence)
    broad=bool((re.search(r'\b(junior|assistant|associate|technician|techniker|specialist|coordinator|planner|sachbearbeiter|mitarbeiter|einsteiger|berufseinsteiger|fachkraft|absolvent|trainee)\b',title,re.I)
                or junior_signal) and len(skills)>=1)
    points=min(100,int(37+min(8,len(skills))*7+min(role,45)*.17- min(8,len(gaps))*3))
    if any('Security clearance' in x or 'US person' in x for x in risks):points=min(points,48)
    return {'tier':'strong_transferable' if points>=70 else 'adjacent_capable' if points>=50 else 'explore',
            'capability_score':max(0,points),'transferable':bool(len(skills)>=1),
            'open_to_junior_roles':bool(broad),'junior_signal':junior_signal,
            'senior_evidence':senior_evidence,'title_senior_signal':title_senior_signal,
            'experience_level':'junior' if junior_signal else 'senior' if senior_evidence else 'unspecified',
            'explanation':
            'The capability indicator highlights CV evidence and transferable skills independently of title-seniority match. Junior priority is based on explicit posting language; it is not a guarantee of eligibility or job performance.'}

EXTENDED_TEAMS={
 'mobility_and_evidence':(
  ('37','Verified visa evidence'),
  ('38','Visa refusal flag'),
  ('39','Relocation offer evidence'),
  ('40','Work authorization uncertainty'),
  ('41','International hiring evidence'),
  ('42','Immigration inquiry opportunity')),
 'recency_and_accessibility':(
  ('43','Published date precision'),
  ('44','Recent posting bucket'),
  ('45','Unknown freshness integrity'),
  ('46','Junior / lower-level openness'),
  ('47','Transferable capability fit'),
  ('48','Recruiter application priority')),
 'career_expansion':(
  ('49','Operations and service pathway'),
  ('50','Quality and inspection pathway'),
  ('51','Supply chain and planning pathway'),
  ('52','Technical customer and applications pathway'),
  ('53','Facilities and utilities pathway'),
  ('54','Cross-track transferable capability'))}

# Evidence dependencies connect the two extended teams to the existing six:
# 37/38 rely on the base visa specialist; 39/41 on mobility context;
# 42 adjudicates those statuses without inventing employer sponsorship.
# Date quality passes 43 -> 44 -> 45; candidate seniority 46 and skill proof
# 47 feed cautious application triage 48. Agents 49-54 surface non-design
# pathways and transferable capability. These are deterministic checks, not
# 18 additional AI-model calls.
AGENT_DEPENDENCIES={
 '37':['34_visa'],
 '38':['37'],
 '39':['35_mobility'],
 '40':['17_clearance','37'],
 '41':['35_mobility'],
 '42':['37','38','39','40','41'],
 '43':['05_date'],
 '44':['43'],
 '45':['43','44'],
 '46':['33_seniority'],
 '47':['31_skills','32_skill_gaps','13_degree','46'],
 '48':['42','44','45','46','47'],
 '49':['29_operations','31_skills'],
 '50':['25_quality','31_skills'],
 '51':['30_supply','31_skills'],
 '52':['31_skills','35_mobility'],
 '53':['28_energy','29_operations','31_skills'],
 '54':['47','49','50','51','52','53']
}

def run_extended_agents(job):
    hire=hiring_opportunity(job.get('hiring_support',{}),job.get('market',{}))
    fresh=published_on(job.get('published_at'))
    capability=capability_assessment(job)
    status={key:(job.get('hiring_support',{}).get(key) or {}).get('status','not_stated')
            for key in ('visa','blue_card','relocation','international')}
    runs=[
       ('37',status['visa'],['Explicit visa assistance only if advert proves it']),
       ('38','negative' if status['visa']=='not_offered' else 'not_confirmed',[]),
       ('39',status['relocation'],[]),
       ('40','verify_eligibility',[]),
       ('41',status['international'],[]),
       ('42',hire['tier'],[hire['warning']]),
       ('43','provided' if fresh['age_days'] is not None else 'unknown',[]),
       ('44',fresh['bucket'],[fresh['label']]),
       ('45','unknown_date' if fresh['age_days'] is None else 'dated',[]),
       ('46','junior_open' if capability['open_to_junior_roles'] else 'standard',[]),
       ('47',capability['tier'],[capability['explanation']]),
       ('48','review' if capability['capability_score']>=50 else 'explore',[])
    ]
    title=str(job.get('title') or '')
    description=str(job.get('description') or '')
    evidence_text=title+' '+description
    pathways=[
      ('49',r'operations?|betrieb|maintenance|instandhaltung|service|field|commissioning|inbetriebnahme|fleet|technical support'),
      ('50',r'quality|qualität|inspection|inspektion|prüf|audit|compliance|validation|validierung|metrology|messtechnik'),
      ('51',r'supply chain|logistics|logistik|procurement|einkauf|purchasing|material|disposition|planning|planung|warehouse|lager'),
      ('52',r'application engineer|applikation|technical sales|vertrieb|customer support|kundenservice|technical consultant|anwendungstechnik'),
      ('53',r'facility|facilities|utilities|versorgungs|energy|energie|water|wasser|data center|rechenzentrum|critical facilities|building services|gebäudetechnik'),
    ]
    matched_pathways=[]
    for key,pattern in pathways:
        hit=bool(re.search(pattern,evidence_text,re.I))
        runs.append((key,'evidence_found' if hit else 'not_stated',[title[:100]] if hit else []))
        if hit:matched_pathways.append(key)
    career_track=str(job.get('career_track') or '').casefold()
    design_tracks=('mechanical design','cad','simulation','manufacturing & production','project engineering')
    transferable=(bool(job.get('matched_skills')) and
                  (job.get('qualification') or {}).get('status')!='excluded' and
                  not any(x in career_track for x in design_tracks))
    runs.append(('54','transferable_non_design' if transferable else 'design_adjacent_or_limited_evidence',
                 (job.get('matched_skills') or [])[:3]))
    return {'freshness':fresh,'immigration_opportunity':hire,'capability':capability,
            'career_expansion':{'matched_pathways':matched_pathways,'non_design_transferable':transferable},
            'agent_findings':[{'agent':key,'status':value,'evidence':evidence,
                               'depends_on':AGENT_DEPENDENCIES.get(key,[]),
                               'team':('mobility_and_evidence' if int(key)<=42 else
                                       'recency_and_accessibility' if int(key)<=48 else
                                       'career_expansion')}
                              for key,value,evidence in runs],
            'teams':{k:len(v) for k,v in EXTENDED_TEAMS.items()},
            'specialists_executed':len(runs)}
