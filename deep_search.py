"""Translate dashboard-defined search profiles into new targeted public job searches.
This module never reads or publishes CV secrets and does not scrape LinkedIn/Google.
"""
import json,os,re
from datetime import datetime,timezone
from pathlib import Path
from industry_search import career_track_queries,allocate_track_queries
# Empty cities means wide western German coverage, not a five-city shortcut.
DEFAULT_CITIES=[
 'Stuttgart','Frankfurt am Main','Karlsruhe','Mannheim','Heidelberg','Darmstadt',
 'Mainz','Wiesbaden','Heilbronn','Esslingen','Ludwigsburg','Böblingen','Sindelfingen',
 'Waiblingen','Reutlingen','Pforzheim','Hanau','Aschaffenburg','Neckarsulm','Göppingen',
 'Aalen','Tübingen','Offenburg','Rastatt','Bruchsal','Weinheim','Bensheim','Rüsselsheim',
 'Bad Homburg','Ludwigshafen','Wetzlar','Friedberg','Marburg','Bad Kreuznach']
# All Germany must not silently mean only western cities. Rotate additional
# German airport, industrial and logistics regions without increasing the
# existing per-scan public BA request ceiling or removing western seeds.
NATIONAL_CITIES=[
 'Berlin','Hamburg','München','Leipzig','Dresden','Dortmund','Düsseldorf',
 'Köln','Bremen','Hannover','Nürnberg','Erfurt','Magdeburg','Halle (Saale)',
 'Chemnitz','Rostock','Potsdam','Cottbus','Schwerin','Kiel','Lübeck',
 'Braunschweig','Wolfsburg','Osnabrück','Bielefeld','Münster','Augsburg',
 'Regensburg','Ingolstadt','Kassel','Jena','Zwickau','Gera','Cottbus',
 # Additional industrial, automotive, logistics, chemical and port centres.
 'Ulm','Friedrichshafen','Villingen-Schwenningen','Schwäbisch Gmünd','Lörrach',
 'Bamberg','Bayreuth','Coburg','Passau','Landshut','Schweinfurt','Weiden',
 'Paderborn','Gütersloh','Hamm','Siegen','Iserlohn','Hagen','Wuppertal',
 'Krefeld','Mönchengladbach','Duisburg','Essen','Bochum','Gelsenkirchen',
 'Aachen','Bonn','Leverkusen','Gütersloh','Celle','Salzgitter','Hildesheim',
 'Göttingen','Oldenburg','Bremerhaven','Flensburg','Neumünster','Stralsund',
 'Greifswald','Wismar','Ludwigsfelde','Eisenach','Weimar','Dessau-Roßlau',
 'Bitterfeld-Wolfen','Pirna','Freiberg','Plauen','Riesa','Görlitz',
 'Neubrandenburg','Suhl','Ilmenau','Fulda','Bad Hersfeld','Limburg',
 'Kaiserslautern','Koblenz','Trier','Saarbrücken','Homburg','Neunkirchen',
 'Germersheim','Landau in der Pfalz','Neustadt an der Weinstraße',
 'Lünen','Unna','Recklinghausen','Lippstadt','Herford','Minden',
 'Ahaus','Bocholt','Dinslaken','Emden','Papenburg','Wilhelmshaven'
]
def default_cities_for_region(region,when=None):
    if region!='germany':return list(DEFAULT_CITIES)
    day=when or datetime.now(timezone.utc).date()
    extras=list(dict.fromkeys(NATIONAL_CITIES))
    start=(day.toordinal()*7)%len(extras)
    rotated=extras[start:]+extras[:start]
    # Preserve all 34 existing western seeds; newly searched cities rotate.
    return [*DEFAULT_CITIES,*[c for c in rotated if c not in DEFAULT_CITIES][:12]]

# These are search seeds, not claims that every nearby town has a vacancy.
ROLE_GROUPS={
 'manufacturing':['Fertigungsingenieur','Produktionsingenieur','Industrial Engineer','Prozessingenieur','Arbeitsvorbereitung','Fertigungsplaner','Industrialisierung'],
 'mechanical':['Maschinenbau','Konstrukteur','Entwicklungsingenieur','CAD','Technischer Produktdesigner','Berechnungsingenieur','Simulation'],
 'project':['Projektingenieur','Projektkoordinator','Projektplaner','Technischer Projektleiter','Project Engineer'],
 'quality':['Qualitätsingenieur','Qualitätssicherung','Qualitätsmanagement','Supplier Quality','Qualitätsprüfer'],
 'maintenance':['Instandhaltung','Instandhaltungsingenieur','Zuverlässigkeit','Maintenance Planner'],
 'automation':['Automatisierung','Mechatronik','Systemingenieur','Testingenieur','Validierung'],
 'aerospace':['Luftfahrt','Aircraft Engineer','CAMO','UAV Engineer'],
 'energy':['Anlageningenieur','Energietechnik','Inspektionsingenieur','Betriebsingenieur'],
 'operations':['Betriebsingenieur','Technischer Koordinator','Betriebsplaner','Operations Engineer'],
 'supply':['Materialplanung','Technischer Einkauf','Supply Chain','Disposition'],
 'data':['Technische Datenanalyse','Prozessdaten','Engineering Documentation'],
 'inspection':["Technischer Inspektor","Prüftechniker","Sachverständiger Technik","Prüfingenieur"],
 'technical_sales':["Vertriebsingenieur","Technische Beratung","Application Engineer","Technischer Kundenberater"],
 'installation':["Inbetriebnahmeingenieur","Commissioning Engineer","Servicetechniker","Technischer Außendienst"],
 'materials':["Werkstofftechniker","Materialingenieur","Werkstoffprüfung","Prüflabor Technik"],
 'facilities':["Facility Engineer","Technisches Gebäudemanagement","Anlagenbetreuung"],
 'regulatory':["Regulatory Affairs Specialist","Technische Compliance","Dokumentenmanager Technik"],
 'planning':["Produktionsplaner","Projektassistenz Technik","Disposition Technisch","Fertigungssteuerung"],
 'automotive':["Automotive Engineer","Versuchsingenieur","Kfz Prüftechniker","Automobilproduktion"],
 'rail':["Bahntechnik","Rolling Stock Engineer","Rail Maintenance Engineer"],
 'medical_industry':["Medizintechnik Ingenieur","Validierungsingenieur","Qualitätsprüfer Medizintechnik"],
 'industrial_support':["Technischer Sachbearbeiter","Qualitätsassistent","Engineering Assistant","Technischer Mitarbeiter"],
 'environment':["Umwelttechnik Ingenieur","EHS Coordinator","HSE Engineer","Arbeitssicherheit Technik"],
 'energy_transition':["Wasserstofftechniker","Photovoltaik Projekttechniker","Wind Turbine Service Engineer"],
 'airport_ops':['Flughafen','Bodenabfertigung','Vorfeld','Airport Operations','Ramp Agent','Flughafenmitarbeiter'],
 'airport_technical':['Flughafentechnik','Gepäckförderanlage','Ground Support Equipment','Airfield Maintenance','Flughafen Instandhaltung'],
 'air_cargo':['Luftfracht','Cargo Handling','Frachtabfertigung','Air Cargo Operations','Lagerlogistik Flughafen'],
 'critical_facilities':['Rechenzentrum','Critical Facilities','Data Center Technician','Rechenzentrum Instandhaltung'],
 'ports_logistics':['Hafenlogistik','Intermodal Logistics','Transportlogistik','Güterverkehr Disponent'],
 'water_utilities':['Wasserwerk','Versorgungsnetze','Betriebskoordinator Energieanlagen'],
 'food_packaging':['Lebensmittelproduktion','Verpackungstechnik','Quality Food Manufacturing'],
 'testing':["Test Technician","Validation Technician","Prüffeldtechniker","Versuchstechniker"]
}
BROAD_TERMS=[
 'Ingenieur','Techniker','Betriebskoordinator','Technischer Betriebskoordinator',
 'Instandhaltungsplaner','Servicetechniker','Field Service','Commissioning',
 'Qualitätsprüfer','Qualitätskoordinator','Supplier Quality','Inspektion',
 'Logistikkoordinator','Materialdisponent','Technischer Einkäufer','Supply Chain',
 'Produktionsplaner','Fertigungssteuerung','Technischer Sachbearbeiter',
 'Technischer Support','Application Engineer','Technischer Kundenservice',
 'Facility Management','Gebäudetechnik','Energieanlagen','Wassertechnik',
 'Technische Dokumentation','EHS Koordinator','Werkstoffprüfung','Messtechnik',
 'Airport Operations','Luftfracht','Vorfeld','Bodenabfertigung','Rechenzentrum',
 'Hafenlogistik','Bahninstandhaltung','Medizintechnik Wartung','Technische Dienstleistungen',
 'Konstruktion','CAD','Maschinenbau','Projekttechnik','Produktion','Fertigung']
def validate_request(s):
    if not isinstance(s,dict):return {}
    def sanitize(items,n,limit):
        return [x.strip() for x in items[:limit] if isinstance(x,str) and 2<=len(x.strip())<=n and not re.search(r'[<>{}\\\\\n\r]',x)]
    region=s.get('region','west')
    sources=s.get('sources',['ba','ats','arbeitnow'])
    sources=[v for v in sources if v in ('ba','ats','arbeitnow','smartrecruiters','workday','workable','jobicy','remotive','himalayas','nomado24','themuse','personio','pinpoint','linkedin_alerts','jobspy_linkedin','jobspy_indeed','jobspy_glassdoor','jobspy_zip_recruiter','jobspy_google','jobspy_bayt','jobspy_naukri','jobspy_bdjobs','jobspy_hellowork','cloro')] if isinstance(sources,list) else ['ba','ats','arbeitnow']
    cities=sanitize(s.get('cities',[]) if isinstance(s.get('cities',[]),list) else [],65,12)
    roles=sanitize(s.get('roles',[]) if isinstance(s.get('roles',[]),list) else [],85,14)
    tracks=sanitize(s.get('tracks',[]) if isinstance(s.get('tracks',[]),list) else [],110,40)
    return {'region':region if region in ('west','germany','world') else 'west','cities':cities,'roles':roles,
        'tracks':tracks,'sources':sources or ['ba','ats','arbeitnow'],
        'radius':min(100,max(5,int(s.get('radius') or 90))),
        'min_score':min(95,max(0,int(s.get('min_score') if s.get('min_score') is not None else 45))),
        'support':s.get('support','all') if s.get('support') in ('all','visa','relocation','blue_card','international','any','visa_possible','mobility_possible') else 'all',
        'freshness':s.get('freshness','all') if s.get('freshness') in ('all','1','7','30','90','unknown') else 'all',
        'depth':s.get('depth','deep') if s.get('depth') in ('focused','deep') else 'deep',
        'capacity':s.get('capacity','maximum_safe') if s.get('capacity') in ('maximum_safe','balanced') else 'maximum_safe',
        'seniority':s.get('seniority','entry_junior') if s.get('seniority') in ('entry_junior','all') else 'entry_junior'}
def current_request():
    source=os.environ.get('SEARCH_REQUEST','').strip()
    if not source:return {}
    if len(source)>6000:raise ValueError('Search request too large')
    return validate_request(json.loads(source))
def dynamic_boards(profile):
    # Empty role selection means ALL CV-compatible families, including near-neighbor work,
    # and broad technical keywords. No form field is required to cover the full CV.
    cities=profile['cities'] or default_cities_for_region(profile['region'])
    # 90 km is the standard requested BA radius. Explicit city selection still
    # narrows the centres, never the radius.
    raw=profile['roles']
    terms=[]
    if raw:
        for role in raw:
            terms.extend(ROLE_GROUPS.get(role.casefold(),[role]))
    elif profile.get('tracks'):
        # The Roles tab manages the authoritative editable taxonomy. When
        # a track is selected, search its industry synonyms rather than
        # querying unrelated generic titles then excluding their results.
        try:
            catalog=json.loads((Path(__file__).resolve().parent/'role_catalog.json').read_text(encoding='utf8'))['roles']
            track_terms=career_track_queries(catalog,profile['tracks'],terms_per_track=10,include_all_titles=profile['depth']=='deep')
            for choices in track_terms.values():terms.extend(choices)
        except (OSError,ValueError,KeyError,TypeError):
            pass
        if not terms:terms.extend(BROAD_TERMS)
    else:
        terms.extend(BROAD_TERMS)
        for group in ROLE_GROUPS.values():
            terms.extend(group[:5])
    terms=list(dict.fromkeys(terms))
    # Diversify broad, unfiltered BA searches across days at the same free API budget.
    # Explicit requested role queries are never rotated.
    if not profile['roles'] and not profile.get('tracks') and len(terms)>1:
        offset=(datetime.now(timezone.utc).date().toordinal()*7)%len(terms)
        terms=terms[offset:]+terms[:offset]
    # Balance breadth with the community BA endpoint: 150-220 targeted searches,
    # max 2 result pages each. Employer ATS and Arbeitnow add independent coverage.
    deep_cap=220 if profile.get('capacity','maximum_safe')=='maximum_safe' else 120
    focused_cap=60 if profile.get('capacity','maximum_safe')=='maximum_safe' else 40
    cap=deep_cap if profile['depth']=='deep' else focused_cap
    pages=2 if profile['depth']=='deep' else 1
    result=[]
    # Deep mode allocates catalogue-backed opportunities for ALL tracks by
    # default, or only the user-selected track allow-list. Reserve a small,
    # bounded part of the same BA task budget for the user's typed role terms.
    # Every catalogue track gets a mandatory first query before fair rotation.
    if profile['depth']=='deep':
        try:
            catalog=json.loads((Path(__file__).resolve().parent/'role_catalog.json').read_text(encoding='utf8'))['roles']
            custom_terms=list(dict.fromkeys(terms))[:14] if profile.get('roles') else []
            allocation_cap=max(0,cap-len(custom_terms))
            result=allocate_track_queries(catalog,allocation_cap,
                selected=profile.get('tracks') or None)
            for board in result:
                board['slug']='on-demand'
                board['radius']=profile['radius']
                board['size']=65
                board['pages']=pages
                board['on_demand']=True
            # Typed role-family/title queries are additional explicit tasks,
            # bounded by the remaining capacity; they do not replace the
            # mandatory catalogue-track coverage reservation.
            for index,term in enumerate(custom_terms):
                if len(result)>=cap:break
                city=cities[(datetime.now(timezone.utc).date().toordinal()*3+index*5)%len(cities)]
                result.append({'type':'bundesagentur','slug':'on-demand','company':'BA · '+city+' · '+term,
                    'city':city,'query':term,'radius':profile['radius'],'size':65,
                    'pages':pages,'on_demand':True,'coverage_stage':'user_role_term'})
            return result
        except (OSError,ValueError,KeyError,TypeError):
            # Preserve the existing bounded fallback when the catalogue cannot
            # be loaded or parsed; the run report must expose this gap.
            pass
    # Broad city sweep + diverse role rotation. The fixed cap remains unchanged.
    for i in range(cap):
        if i<len(cities):
            city=cities[i]
            term=terms[0] if (profile['roles'] or profile.get('tracks')) else 'Ingenieur'
        else:
            n=i-len(cities)
            term=terms[n%len(terms)]
            city=cities[(n*7+n//max(1,len(terms)))%len(cities)]
        result.append({'type':'bundesagentur','slug':'on-demand','company':'BA · '+city+' · '+term,
              'city':city,'query':term,'radius':int(profile.get('radius') or 90),'size':65,
              'pages':pages,'on_demand':True})
    return result
def cloro_boards(profile):
    """At most eight Google SERP queries per scan; queries follow requested CV tracks."""
    limit = 4 if profile.get('depth') == 'focused' else 8
    terms = []
    if profile.get('roles'):
        terms.extend(profile['roles'])
    elif profile.get('tracks'):
        try:
            catalog=json.loads((Path(__file__).resolve().parent/'role_catalog.json').read_text(encoding='utf8'))['roles']
            choices=career_track_queries(catalog,profile['tracks'],terms_per_track=10)
            for values in choices.values(): terms.extend(values[:2])
        except (OSError,ValueError,KeyError,TypeError):
            terms.extend(profile['tracks'])
    else:
        terms.extend(['Fertigungsingenieur','Projektingenieur','Qualitätsingenieur',
                      'Instandhaltungsingenieur','Technischer Koordinator',
                      'UAV Engineer','CAMO Engineer','Industrial Engineer'])
    terms=list(dict.fromkeys(t.strip() for t in terms if isinstance(t,str) and t.strip()))
    if not terms: return []
    if not profile.get('roles') and not profile.get('tracks'):
        offset=(datetime.now(timezone.utc).date().toordinal()*3)%len(terms)
        terms=terms[offset:]+terms[:offset]
    return [{'type':'cloro','slug':'google-serp-'+str(i+1),
             'company':'Cloro Google · '+term,
             'query':'("stellenangebot" OR "jobs" OR "karriere") "'+term+'" Germany',
             'country':'de','language':'de','num':15}
            for i,term in enumerate(terms[:limit])]

def exclusion_reasons(job,profile):
    """Explain ALL user-filter exclusions without interpreting unknown support as refusal.

    Reasons overlap intentionally; the caller can additionally measure the
    first blocking condition to build an additive rejection waterfall.
    """
    reasons=[]
    market=job.get('market',{})
    if profile['region']=='west' and not market.get('west'):
        reasons.append('location')
    elif profile['region']=='germany' and not market.get('germany'):
        reasons.append('location')
    if job.get('score',0)<profile['min_score']:
        cap=job.get('capability') or {}
        credential_ok=(job.get('qualification') or {}).get('status')!='excluded'
        transferable=(cap.get('transferable') and credential_ok and
            cap.get('capability_score',0)>=max(50,profile['min_score']+10))
        junior=(cap.get('open_to_junior_roles') and credential_ok and
            cap.get('capability_score',0)>=profile['min_score']+10)
        if not (transferable or junior):
            reasons.append('score')
    if profile['tracks'] and job.get('career_track') not in profile['tracks']:
        reasons.append('career_track')
    seniority=job.get('seniority_assessment') or {}
    # Default applicant mode excludes clearly senior/leadership postings by
    # explicit body evidence OR a senior title signal, unless the posting also
    # explicitly advertises entry/junior eligibility. Keep all-level mode opt-in.
    senior_title=bool(seniority.get('title_signal'))
    senior_body=bool(seniority.get('body_senior_evidence'))
    junior_body=bool(seniority.get('body_junior_evidence'))
    if profile.get('seniority','entry_junior')=='entry_junior' and (senior_body or senior_title) and not junior_body:
        reasons.append('seniority')
    from career_intelligence import recent_enough, hiring_opportunity
    if not recent_enough(job,profile.get('freshness','all')):
        reasons.append('freshness')
    support=profile['support']
    statuses={k:v.get('status') for k,v in job.get('hiring_support',{}).items()}
    opportunity=job.get('immigration_opportunity') or hiring_opportunity(job.get('hiring_support',{}),market)
    if support=='any' and not opportunity['confirmed_assistance']:
        reasons.append('support')
    elif support=='visa_possible' and opportunity['tier']=='visa_not_offered':
        reasons.append('support')
    elif support=='mobility_possible' and opportunity['tier']=='visa_not_offered' and statuses.get('relocation') not in ('explicit','mentioned'):
        reasons.append('support')
    elif support in ('visa','relocation','international') and statuses.get(support)!='explicit':
        reasons.append('support')
    elif support=='blue_card' and statuses.get('blue_card') not in ('explicit','mentioned'):
        reasons.append('support')
    return reasons


def eligible_job(job,profile):
    return not exclusion_reasons(job,profile)
