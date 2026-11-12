"""Bounded, on-demand industrial employer leads from OpenStreetMap / Overpass.

No API key or Nominatim geocoding required. Public community instances are
rate-limited and queried only for a small, user-requested sample of towns.
These are OSM sites, never verified vacancies, sponsors or employers hiring.
"""
from __future__ import annotations
import json
import re
import time
import urllib.parse
import urllib.request
from urllib.parse import urlparse
from datetime import datetime, timezone

OVERPASS_ENDPOINT='https://overpass-api.de/api/interpreter'
USER_AGENT='EngineeringCareerRadar/5.0 (private personal job research; github.com/happytiswis-sudo/engineering-career-radar)'
DEFAULT_INDUSTRIAL_TOWNS=('Esslingen am Neckar','Hanau','Böblingen','Heilbronn')
# User-friendly search aliases mapped to German municipal boundary names.
ALIASES={
 'esslingen':'Esslingen am Neckar',
 'frankfurt':'Frankfurt am Main',
 'frankfurt am main':'Frankfurt am Main',
 'stuttgart':'Stuttgart',
 'hanau':'Hanau',
 'mannheim':'Mannheim',
 'karlsruhe':'Karlsruhe',
 'böblingen':'Böblingen',
 'boeblingen':'Böblingen',
 'heilbronn':'Heilbronn',
 'rüsselsheim':'Rüsselsheim am Main',
 'ruesselsheim':'Rüsselsheim am Main',
 'heidelberg':'Heidelberg',
 'darmstadt':'Darmstadt'
}
MAX_CITIES=4
MAX_RESULTS_PER_CITY=90
MAX_RESULTS=240

def request_json(url,data=None,timeout=38):
    headers={'User-Agent':USER_AGENT,'Accept':'application/json'}
    if data is not None:headers['Content-Type']='application/x-www-form-urlencoded'
    req=urllib.request.Request(url,data=data,headers=headers,method='POST' if data is not None else 'GET')
    with urllib.request.urlopen(req,timeout=timeout) as response:
        return json.load(response)

def choose_towns(cities):
    """Explicit cities first; otherwise a spread of small western industrial towns."""
    requested=[x.strip() for x in (cities or []) if isinstance(x,str)]
    if not requested:requested=list(DEFAULT_INDUSTRIAL_TOWNS)
    out=[];seen=set()
    for entered in requested:
        name=ALIASES.get(entered.casefold(),entered)
        if not re.fullmatch(r"[\w .ÄÖÜäöüß()/-]{2,65}",name,re.UNICODE):
            continue
        if name.casefold() in seen:continue
        seen.add(name.casefold());out.append(name)
        if len(out)>=MAX_CITIES:break
    return out

def overpass_query(city):
    # One city-boundary polygon per query. The containment filter prevents cities
    # with the same name outside Germany from being treated as German leads.
    quoted=json.dumps(city,ensure_ascii=False)
    return f'''[out:json][timeout:24];
area["ISO3166-1"="DE"]["admin_level"="2"]->.country;
area["name"={quoted}]["boundary"="administrative"]["admin_level"~"^(8|9)$"]->.city;
(
 nwr(area.city)(area.country)["name"]["man_made"="works"];
 nwr(area.city)(area.country)["name"]["industrial"];
 nwr(area.city)(area.country)["name"]["craft"~"^(metal_construction|metalworking|carpenter|electronics|machinery|mechanic)$"];
);
out tags center {MAX_RESULTS_PER_CITY};'''

def website_from(tags):
    raw=str(tags.get('website') or tags.get('contact:website') or '').strip()
    if raw.startswith('www.'):raw='https://'+raw
    if not raw.startswith(('http://','https://')):return ''
    try:
        parsed=urlparse(raw)
        if not parsed.hostname or parsed.username or parsed.password:return ''
        if parsed.hostname in ('localhost','127.0.0.1'):return ''
        return parsed.geturl()
    except ValueError:return ''

def discover_local_companies(cities,enabled=False):
    base={'source':'© OpenStreetMap contributors (ODbL); Overpass',
          'source_api':'Overpass API (public instance, no key)',
          'jobs_verified':False,'career_sites_verified':False,
          'note':'OSM data identify candidate industrial sites only. Company identity, careers page, vacancy, visa policy and hiring activity are not verified.',
          'searched_on_demand':bool(enabled),'searched_at':None,
          'cities_queried':[],'candidates':[],'errors':[],'queries_succeeded':0}
    if not enabled:return {**base,'note':'OSM discovery runs only in user-initiated Deep searches for Germany. No OSM scan was requested.'}
    selected=choose_towns(cities)
    found=[];seen=set()
    base['cities_queried']=selected
    base['searched_at']=datetime.now(timezone.utc).isoformat(timespec='seconds')
    for city in selected:
        try:
            query=overpass_query(city)
            results=request_json(OVERPASS_ENDPOINT,urllib.parse.urlencode({'data':query}).encode('utf-8'))
            base['queries_succeeded']+=1
            for item in results.get('elements',[])[:MAX_RESULTS_PER_CITY]:
                tags=item.get('tags') or {}
                company=str(tags.get('name') or '').strip()[:140]
                if len(company)<2:continue
                osm_type=str(item.get('type','node'))
                osm_id=item.get('id')
                if osm_type not in ('node','way','relation') or not str(osm_id).isdigit():continue
                website=website_from(tags)
                key=('domain',urlparse(website).hostname.lower()) if website else ('name',company.casefold(),city.casefold())
                if key in seen:continue
                seen.add(key)
                coordinates=item.get('center') or item
                try:
                    latitude=float(coordinates.get('lat'));longitude=float(coordinates.get('lon'))
                    location={'lat':round(latitude,6),'lon':round(longitude,6)}
                except (TypeError,ValueError):
                    location={}
                lead={'company':company,'city_search':city,'website':website,
                      'category':str(tags.get('industrial') or tags.get('man_made') or tags.get('craft') or 'Industrial')[:65],
                      'source':'OpenStreetMap','jobs_verified':False,'career_site_verified':False,
                      'website_listed':bool(website),'lead_type':'industrial_site_with_website' if website else 'industrial_site_to_verify',
                      'osm_url':f'https://www.openstreetmap.org/{osm_type}/{osm_id}',**location}
                found.append(lead)
                if len(found)>=MAX_RESULTS:break
        except Exception as exc:
            # Never output private request URLs or tokens; errors are diagnostics only.
            base['errors'].append(f'{city}: {type(exc).__name__}')
        finally:
            time.sleep(1.25)
        if len(found)>=MAX_RESULTS:break
    base['candidates']=found
    base['candidate_sites']=len(found)
    base['sites_with_website']=sum(bool(x['website']) for x in found)
    if not found:
        base['note']+=' No mapped leads were returned for these city-boundary searches; this is not proof that no industrial businesses exist.'
    return base
