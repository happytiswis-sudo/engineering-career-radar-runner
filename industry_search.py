"""Balanced discovery across the user-editable 34+ career-track taxonomy.

Only generate public BA search queries. This module never infers qualifications,
visa sponsorship, source freshness or an actual vacancy.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime,timezone
from hashlib import sha256

TRACK_TERMS={
 'Project Engineering & Delivery':['Projektingenieur','Projektkoordinator Technik','Project Engineer'],
 'Manufacturing & Production':['Fertigungsplaner','Produktionskoordinator','Manufacturing Technician'],
 'Mechanical Design, CAD & Simulation':['Konstrukteur','CAD Techniker','Mechanical Design'],
 'Quality, Process & Compliance':['Qualitätssicherung','Qualitätsprüfer','Quality Coordinator','Prüftechniker','Supplier Quality','Qualitätsmanagement'],
 'Airworthiness & Maintenance Planning':['CAMO','Aircraft Maintenance Planner','Airworthiness'],
 'UAV, Aviation & Inspection':['Drohnen Technik','UAV Operations','Aircraft Inspection'],
 'Energy, Oil & Gas Infrastructure':['Anlageninstandhaltung','Pipeline Inspection','Asset Integrity'],
 'Systems Integration & Validation':['Validierung Technik','Testingenieur','Systems Integration'],
 'Operations & Technical Delivery':['Technischer Betriebskoordinator','Operations Coordinator','Betriebstechnik','Instandhaltungsplaner','Servicetechniker','Field Service Coordinator'],
 'Supply Chain, Planning & Procurement':['Materialdisponent','Supply Chain Coordinator','Logistikplanung','Technischer Einkäufer','Produktionsplaner','Lagerlogistik'],
 'Engineering Data & Digital Improvement':['Technische Datenanalyse','Engineering Documentation','Prozessdaten'],
 'Safety, Risk & Technical Documentation':['HSE Koordinator','Technische Dokumentation','Arbeitssicherheit'],
 'Product Development & Prototyping':['Produktentwicklung','Prototypenbau','Product Development'],
 'Aviation, CAMO & Maintenance':['Flugzeug Instandhaltung','CAMO Planner','Lufttüchtigkeit'],
 'Energy, Infrastructure & Inspection':['Anlageninspektion','Prüftechniker Energie','Betriebsingenieur'],
 'Industrial Technical & Technician Opportunities':['Produktionstechniker','Technischer Mitarbeiter','Servicetechniker'],
 'Automotive & Mobility Engineering':['Fahrzeugtechnik','Versuchsingenieur Fahrzeug','Automotive Quality'],
 'Rail & Transportation Engineering':['Bahntechnik','Schienenfahrzeug Instandhaltung','Rail Maintenance'],
 'Medical & Precision Manufacturing':['Medizintechnik Produktion','Qualität Medizintechnik','Medical Device Manufacturing'],
 'Commissioning, Field Service & Industrial Inspection':['Inbetriebnahme Techniker','Industrie Inspektion','Field Service'],
 'Materials, Laboratory & Metrology':['Werkstoffprüfung','Messtechnik','Kalibriertechniker'],
 'Renewables, Utilities & Sustainability':['Photovoltaik Wartung','Windenergie Techniker','Batterieproduktion'],
 'Technical Sales, Applications & Commercial Engineering':['Anwendungstechniker','Technischer Kundenservice','Vertriebsingenieur','Application Engineer','Technical Support Engineer','Technical Account Specialist'],
 'Facilities, Industrial Operations & Compliance':['Technisches Gebäudemanagement','Facility Maintenance','Industrieanlagen','Facility Coordinator','Technischer Objektbetreuer','Instandhaltung Gebäude'],
 'Airport Operations, Apron & Turnaround':['Vorfeldmitarbeiter','Bodenabfertigung','Airport Operations','Flughafenbetriebskoordinator','Turnaround Koordinator','Airside Operations'],
 'Airport Technical Systems & Infrastructure':['Flughafentechnik','Gepäckförderanlage','Ground Support Equipment','Flughafen Instandhaltung','Gepäcksystem Techniker','Flughafen Elektrotechnik','Airport Systems Engineer'], 
 'Airport Cargo, Freight & Logistics':['Luftfrachtabfertigung','Air Cargo','Cargo Handling','Luftfracht Sachbearbeiter','Cargo Logistics Coordinator','Warehouse Operations Airport','Luftfracht Logistikplaner','Zollabwicklung Luftfracht','Cargo Operations Agent'], 
 'Airline Ground Support & Flight Operations Administration':['Flugbetrieb Sachbearbeiter','Aircraft Records','Airline Operations'],
 'Transport, Port & Intermodal Logistics':['Hafenlogistik','Intermodal Logistics','Güterverkehr Disponent'],
 'Healthcare Facilities & Medical Logistics':['Krankenhaus Logistik','Medizintechnik Wartung','Medical Equipment','Clinical Engineering Coordinator','Medical Equipment Planner','Healthcare Procurement','Krankenhaustechnik','Medizinprodukte Instandhaltung','Klinik Einkauf','Medizinischer Geräteplaner'], 
 'Data Centers, Telecom & Critical Facilities':['Rechenzentrum Technik','Critical Facilities','Telekommunikation Projekt','Data Center Operations','Critical Facilities Technician','Network Rollout Coordinator','Rechenzentrum Instandhaltung','Elektrotechniker Rechenzentrum','USV Techniker','Kühltechnik Rechenzentrum'], 
 'Construction, Property & Building Services':['Bauprojekt Technik','Gebäudetechnik','Baustellenlogistik','MEP Coordinator','Building Maintenance Coordinator','Construction Quality','TGA Projektkoordinator','Bauleiter technische Gebäudeausrüstung','Gebäudetechnik Ingenieur','Bau Qualitätsmanagement'], 
 'Energy, Water & Public Utilities Operations':['Wasserwerk Technik','Versorgungsnetze','Instandhaltung Energieanlagen','Energieanlagen Betriebsführer','Netzplanung','Wasseraufbereitung','Netzbetrieb Techniker','Kläranlagen Betrieb','Energieversorgung Instandhaltung','Wassertechnik Ingenieur'], 
 'Food, Packaging & Consumer Production':['Verpackungstechniker','Lebensmittelproduktion','Produktionsplanung Lebensmittel','Lebensmitteltechniker','Abfüllanlagen Instandhaltung','Qualitätskontrolle Lebensmittel','Verpackungsingenieur'], 
}
CITIES=('Frankfurt am Main','Stuttgart','Düsseldorf','München','Köln',
        'Mannheim','Karlsruhe','Hamburg','Berlin','Bremen','Hannover',
        'Leipzig','Dortmund','Nürnberg','Darmstadt','Duisburg','Bonn','Essen',
        'Kassel','Aachen')
UNDERSEARCHED={'Airport Operations, Apron & Turnaround',
    'Airport Technical Systems & Infrastructure','Airport Cargo, Freight & Logistics',
    'Airline Ground Support & Flight Operations Administration',
    'Healthcare Facilities & Medical Logistics','Data Centers, Telecom & Critical Facilities',
    'Energy, Water & Public Utilities Operations','Food, Packaging & Consumer Production',
    'Transport, Port & Intermodal Logistics','Construction, Property & Building Services'}

def career_track_queries(catalog_roles,selected=None,terms_per_track=10,include_all_titles=False):
    """Return track seeds plus catalog titles using fair, deterministic sampling.

    By default this preserves the bounded legacy sample. Deep-mode plans can
    request every catalogue title. Explicit track selections remain a strict
    allow-list and aliases are retained when present in the catalogue rows.
    """
    tracks=defaultdict(list)
    for row in catalog_roles:
        if not isinstance(row,dict):continue
        title=str(row.get('title') or '').strip()
        group=str(row.get('track') or '').strip()
        if 2<=len(title)<=85 and 2<=len(group)<=110:
            aliases=row.get('aliases') or []
            values=[title] + (aliases if isinstance(aliases,list) else [])
            for value in values:
                value=str(value or '').strip()
                if 2<=len(value)<=85:
                    tracks[group].append(value)
    requested=set(selected) if selected else None
    try:limit=max(1,min(20,int(terms_per_track)))
    except (TypeError,ValueError):limit=10
    result={}
    for group,titles in tracks.items():
        if requested is not None and group not in requested:continue
        curated=list(dict.fromkeys(TRACK_TERMS.get(group,[])))
        distinct=[x for x in dict.fromkeys(titles) if x not in curated]
        if include_all_titles:
            sampled=distinct
        else:
            sample_count=min(limit,len(distinct))
            if len(distinct)>sample_count:
                indexes=sorted({round(i*(len(distinct)-1)/(sample_count-1)) for i in range(sample_count)}) if sample_count>1 else [0]
                sampled=[distinct[i] for i in indexes]
            else:sampled=distinct[:sample_count]
        result[group]=list(dict.fromkeys([*curated,*sampled]))
    return result


def allocate_track_queries(catalog_roles,cap,selected=None,when=None,city_pool=CITIES):
    """Allocate at least one distinct task per selected catalogue track when feasible.

    Tracks get one mandatory seed before any extra query is allocated. Remaining
    slots rotate fairly through tracks and titles, with deterministic city/term
    pairing. The cap is never exceeded; when cap < track count the report
    explicitly identifies tracks that could not fit.
    """
    if cap<=0:return []
    day=when or datetime.now(timezone.utc).date()
    terms=career_track_queries(catalog_roles,selected=selected,include_all_titles=True)
    tracks=sorted(terms)
    if not tracks:return []
    cursor=day.toordinal()
    planned=[]
    offsets={track:(int(sha256(track.encode()).hexdigest()[:8],16)+cursor)%max(1,len(terms[track])) for track in tracks}
    # Mandatory round: one distinct catalogue-backed query per track.
    for index,track in enumerate(tracks[:cap]):
        choices=terms[track]
        term=choices[offsets[track] % len(choices)]
        city=city_pool[(cursor*7+index*11)%len(city_pool)]
        planned.append({'type':'bundesagentur','slug':'industry-rotation','company':'BA cross-industry · '+city+' · '+term,
            'city':city,'query':term,'radius':55,'size':45,'pages':2,
            'industry_track':track,'rotating_search':True,'coverage_stage':'mandatory_track'})
    # Allocate spare capacity round-robin; catalogue terms are not truncated
    # before allocation and all track families receive equal query opportunity.
    extra_index=0
    while len(planned)<cap:
        track=tracks[extra_index%len(tracks)]
        choices=terms[track]
        term=choices[(offsets[track]+1+(extra_index//len(tracks)))%len(choices)]
        city=city_pool[(cursor*5+extra_index*7+int(sha256(track.encode()).hexdigest()[-5:],16))%len(city_pool)]
        planned.append({'type':'bundesagentur','slug':'industry-rotation','company':'BA cross-industry · '+city+' · '+term,
            'city':city,'query':term,'radius':55,'size':45,'pages':2,
            'industry_track':track,'rotating_search':True,'coverage_stage':'fair_rotation'})
        extra_index+=1
        if extra_index>cap*max(2,len(tracks))*2:break
    return planned

def industry_boards(existing,catalog_roles,prior_metrics=None,when=None,limit=44):
    if limit<=0:return []
    day=when or datetime.now(timezone.utc).date()
    terms=career_track_queries(catalog_roles)
    reserved={(str(b.get('city','')).casefold(),str(b.get('query','')).casefold())
              for b in existing if b.get('type')=='bundesagentur'}
    out=[];used=set(reserved)
    def add(track,city,term,feedback=False):
        k=(city.casefold(),term.casefold())
        if k in used:return False
        used.add(k)
        out.append({'type':'bundesagentur','slug':'industry-rotation','company':'BA cross-industry · '+city+' · '+term,
          'city':city,'query':term,'radius':55,'size':45,'pages':2,
          'industry_track':track,'rotating_search':True,'feedback_reused':feedback})
        return True
    # Equal opportunity for every track, including newly created Roles-tab tracks.
    for index,track in enumerate(sorted(terms)):
        choices=terms[track]
        if not choices:continue
        seed=int(sha256(track.encode()).hexdigest()[:8],16)
        for attempt in range(len(choices)*len(CITIES)):
            term=choices[(day.toordinal()+seed+attempt)%len(choices)]
            city=CITIES[(day.toordinal()*7+index*11+attempt*3)%len(CITIES)]
            if add(track,city,term):break
        if len(out)>=limit:return out
    # Limited productive reuse for proven *recent & previously unseen CV matches*.
    scores=sorted((p for p in (prior_metrics or []) if isinstance(p,dict)
         and str(p.get('industry_track') or '') in terms
         and int(p.get('unseen_recent_cv_matches') or 0)>0),
         key=lambda x:(int(x.get('unseen_recent_cv_matches') or 0),int(x.get('cv_matches') or 0)),reverse=True)
    reuse_limit=min(6,max(0,limit-len(out)))
    reused=0
    for row in scores:
        if reused>=reuse_limit:break
        if add(row['industry_track'],str(row.get('city') or ''),
               str(row.get('query') or ''),True):reused+=1
    # Remaining slots are exploratory and favor badly underrepresented industries.
    order=sorted(terms,key=lambda t:(t not in UNDERSEARCHED,t))
    extra=0
    while len(out)<limit and extra<limit*10:
        track=order[extra%len(order)]
        terms_here=terms[track]
        index=extra//len(order)
        offset=int(sha256(track.encode()).hexdigest()[-5:],16)
        term=terms_here[(day.toordinal()+index+offset+1)%len(terms_here)]
        city=CITIES[(day.toordinal()*5+extra*7+offset)%len(CITIES)]
        add(track,city,term)
        extra+=1
    return out

def load_prior_board_metrics(path):
    """Load only past aggregate public ATS board metrics, not applicant data."""
    from pathlib import Path
    import json
    try:
        value=json.loads(Path(path).read_text(encoding='utf8'))
        stats=value.get('source_board_metrics') or []
        return [x for x in stats[:600] if isinstance(x,dict)
                and isinstance(x.get('type'),str) and isinstance(x.get('slug'),str)]
    except (OSError,ValueError,TypeError,AttributeError):
        return []


def allocate_historical_boards(directory,prior_metrics=None,when=None,cap=360,
                              prior_failures=None,now=None):
    """Rotate historical candidates; honor active 404 and 429 cooldown records."""
    if cap<=0:return []
    current=now or datetime.now(timezone.utc)
    if current.tzinfo is None:current=current.replace(tzinfo=timezone.utc)
    failure_rows=(list(prior_failures.values()) if isinstance(prior_failures,dict)
                  else list(prior_failures or []))
    blocked=set()
    for failure in failure_rows:
        if not isinstance(failure,dict) or failure.get('reason') not in ('http_404','http_429'):
            continue
        retry=str(failure.get('retry_after') or '')
        try:retry_at=datetime.fromisoformat(retry.replace('Z','+00:00'))
        except (TypeError,ValueError):continue
        if retry_at.tzinfo is None:retry_at=retry_at.replace(tzinfo=timezone.utc)
        if retry_at>current:
            blocked.add((str(failure.get('type') or ''),
                         str(failure.get('slug') or '').casefold()))
    directory=[b for b in directory if
               (str(b.get('type') or ''),str(b.get('slug') or '').casefold()) not in blocked]
    if len(directory)<=cap:return list(directory)
    day=when or current.date()
    data={(str(x.get('type')),str(x.get('slug')).casefold()):x
          for x in (prior_metrics or []) if isinstance(x,dict)}
    productive=[]
    for b in directory:
        performance=data.get((str(b.get('type')),str(b.get('slug')).casefold())) or {}
        if int(performance.get('unseen_recent_cv_matches') or 0)>0:
            productive.append((b,performance))
    productive.sort(key=lambda x:(int(x[1].get('unseen_recent_cv_matches') or 0),
       int(x[1].get('cv_matches') or 0)),reverse=True)
    retained=[];seen=set()
    for b,_ in productive[:min(cap//4,90)]:
        key=(b['type'],b['slug'].casefold())
        if key not in seen:retained.append(b);seen.add(key)
    # Co-prime-ish daily stride, so unchosen historical ATS boards are still
    # revisited over consecutive runs rather than permanently excluded.
    offset=(day.toordinal()*211)%len(directory)
    for b in [*directory[offset:],*directory[:offset]]:
        key=(b['type'],b['slug'].casefold())
        if key not in seen:retained.append(b);seen.add(key)
        if len(retained)>=cap:break
    return retained

WORKDAY_BASE_TERMS=('Ingenieur','Engineer','Techniker','Projekt','Instandhaltung')
WORKDAY_ROTATING_TERMS=('Manufacturing','Quality','Produktion','Logistics',
   'Airport','Cargo','Baggage','Facility','Maintenance','Automation',
   'Supply Chain','Commissioning','Laboratory','Rail','Renewable',
   'Construction','Technical Support')

def rotating_workday_terms(board,when=None):
    """Same eight CXS queries, but 3 daily rotating multi-industry terms."""
    day=when or datetime.now(timezone.utc).date()
    seed=int(sha256(str(board.get('slug') or '').encode()).hexdigest()[:8],16)
    offset=(seed+day.toordinal()*3)%len(WORKDAY_ROTATING_TERMS)
    added=tuple(WORKDAY_ROTATING_TERMS[(offset+5*i)%len(WORKDAY_ROTATING_TERMS)]
                for i in range(3))
    return (*WORKDAY_BASE_TERMS,*added)

NOMADO_ROTATING_TERMS=('airport','cargo','logistics','maintenance','quality',
 'medical manufacturing','technical service','food production','rail','facility',
 'supply chain','technical support','renewable energy','project coordinator',
 'data center','packaging','automotive','airport operations','material planner')

def rotating_nomado_queries(when=None):
    """Six bounded public REST v2 topics, three rotate across industries."""
    day=when or datetime.now(timezone.utc).date()
    offset=(day.toordinal()*3)%len(NOMADO_ROTATING_TERMS)
    varied=tuple(NOMADO_ROTATING_TERMS[(offset+5*i)%len(NOMADO_ROTATING_TERMS)]
                 for i in range(3))
    return ('Ingenieur','manufacturing','Techniker',*varied)
