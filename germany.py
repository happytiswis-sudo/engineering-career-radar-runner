"""West Germany vacancy geography, explicit hiring-assistance evidence, and BA feed.
No inference of work permits/Blue Card eligibility from the employer's address.
German Jobsuche endpoint is community-documented, not an official supported API.
"""
import base64
import datetime as dt
import json
import re
import unicodedata
import urllib.parse
import urllib.request

def norm(value):
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(c for c in value if not unicodedata.combining(c)).replace("ß","ss")

def location_signal(location, preferences):
    raw=norm(location)
    clusters=preferences.get("clusters",{})
    smaller=preferences.get("smaller",[])
    for cluster,cities in clusters.items():
        found=[]
        for name in sorted(cities,key=len,reverse=True):
            test=norm(name)
            if re.search(r"(?<![a-z])"+re.escape(test)+r"(?![a-z])",raw):
                found.append(name)
        if found:
            city=max(found,key=len)
            return dict(country="Germany",germany=True,west=True,cluster=cluster,city=city,
                        small_city=any(norm(city)==norm(t) for t in smaller),
                        location_confidence="city name in advertised job location")
    if re.search(r"(?<![a-z])(germany|deutschland|bundesweit|baden.wurttemberg|hessen|rheinland.pfalz)(?![a-z])",raw) or re.search(r"\bDE\b",str(location or "")):
        return dict(country="Germany",germany=True,west=False,cluster="Other Germany",city="",small_city=False,location_confidence="Germany named in location")
    return dict(country="Other / unspecified",germany=False,west=False,cluster="Outside west Germany / unknown",city="",small_city=False,location_confidence="Not established from location text")

EVIDENCE={
    "visa": {
        "positive": [r"visa sponsorship (?:is |will be )?(?:available|provided|offered)",r"(?:offer|provide|support|sponsor).{0,35}(?:work visas?|visa sponsorship|work permits?)",r"(?:visa|immigration|work.permit) (?:support|assistance|sponsorship)",r"support (?:with|for) (?:your )?(?:visa|immigration|work permit)",r"visumsunterstutzung",r"unterstutzung (?:bei|fur) (?:die )?(?:visum|arbeitserlaubnis|aufenthaltstitel)",r"visa.? und (?:arbeits|aufenthalts)"],
        "negative": [r"no visa sponsorship",r"visa sponsorship (?:is )?not (?:available|offered|provided)",r"(?:do not|don't|cannot|can't|unable to|will not) sponsor (?:visas?|work permits?)",r"keine (?:visumsunterstutzung|visumsponsoring)"],
        "mention": [r"visa sponsorship",r"work permit",r"arbeitserlaubnis",r"aufenthaltstitel"]},
    "blue_card": {
        "positive":[r"(?:help|assist|support|sponsor|guidance).{0,35}(?:eu )?blue card",r"(?:eu )?blue card (?:support|assistance|guidance|process)",r"unterstutzung.{0,30}blaue karte"],
        "negative":[r"(?:do not|cannot|unable to) (?:assist|help|support).{0,30}blue card"],
        "mention":[r"(?:eu )?blue card",r"blaue karte"]},
    "relocation": {
        "positive":[r"relocation (?:support|package|assistance|expenses|budget|allowance|benefits)",r"(?:offer|provide|include|cover).{0,35}(?:relocation|moving expenses)",r"umzugsunterstutzung",r"umzugskosten(?:ubernahme)?",r"relocation assistance"],
        "negative":[r"no relocation (?:support|package|assistance)",r"relocation (?:is )?not (?:available|provided|offered)"],
        "mention":[r"relocation",r"umzug"]},
    "international": {
        "positive":[r"(?:international|overseas|foreign) (?:applicants|candidates|professionals) (?:are )?(?:welcome|encouraged|accepted)",r"(?:applications|candidates) from (?:abroad|outside germany) (?:are )?(?:welcome|accepted|encouraged)",r"(?:worldwide|global) (?:hiring|recruitment)",r"bewerbungen aus dem ausland (?:sind )?willkommen",r"internationale bewerber (?:sind )?willkommen",r"english (?:is |as )(?:the )?(?:working|company) language"],
        "negative":[r"only (?:german|eu|local) (?:applicants|candidates)",r"must already have (?:german|eu) work (?:permit|authorization)"],
        "mention":[r"international (?:team|environment|colleagues)",r"multicultural",r"english.speaking",r"internationa"]}}
LABELS={"visa":"Visa / work-permit support","blue_card":"EU Blue Card assistance","relocation":"Relocation support","international":"International applicants"}
def hiring_signals(description):
    text=norm(description)
    result={}
    for kind,patterns in EVIDENCE.items():
        state="not_stated";proof=""
        for status,items in [("not_offered",patterns["negative"]),("explicit",patterns["positive"]),("mentioned",patterns["mention"])]:
            for pattern in items:
                match=re.search(pattern,text,re.I)
                if not match:continue
                start=max(0,match.start()-65);end=min(len(text),match.end()+80)
                proof=re.sub(r"\s+"," ",text[start:end]).strip()[:170]
                state=status;break
            if state!="not_stated":break
        result[kind]={"status":state,"label":LABELS[kind],"evidence":proof}
    return result

BA_BASE="https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
def fetch_german_jobs(board):
    """German BA employer vacancy search via community-documented v6 API.
    This is not an officially supported service; errors are handled by the caller.
    """
    city=board.get("city","Stuttgart")
    term=board.get("query","Ingenieur")
    pages=min(3,max(1,int(board.get("pages",1))))
    size=min(100,max(10,int(board.get("size",45))))
    # The caller injects the single requested radius into every BA board.
    # Keep the provider contract bounded at 5–100 km and use 90 km by default.
    radius=min(100,max(5,int(board.get("radius",90))))
    headers={"X-API-Key":"jobboerse-jobsuche","Accept":"application/json",
             "User-Agent":"EngineeringCareerRadar/4.0 (personal job research)"}
    output=[]
    seen=set()
    for page in range(1,pages+1):
        params={"angebotsart":1,"wo":city,"was":term,"umkreis":radius,
                "page":page,"size":size}
        address=BA_BASE+"/pc/v6/jobs?"+urllib.parse.urlencode(params)
        with urllib.request.urlopen(urllib.request.Request(address,headers=headers),timeout=14) as response:
            body=json.load(response)
        listings=body.get("ergebnisliste") or body.get("stellenangebote") or body.get("jobs") or []
        if not isinstance(listings,list):break
        for x in listings[:size]:
            reference=x.get("refnr") or x.get("referenznummer") or x.get("id")
            if not reference or reference in seen:continue
            seen.add(reference)
            location=x.get("stellenlokationen") or x.get("arbeitsort") or x.get("arbeitsorte") or {}
            if isinstance(location,list):location=location[0] if location else {}
            if isinstance(location,dict):
                address=location.get("adresse") or location.get("arbeitsort") or location
                if isinstance(address,dict):
                    location=address.get("ort") or address.get("stadt") or address.get("region") or address.get("plz") or ""
                else: location=address
            # Never silently replace missing locations with the query city:
            # a radius query can return jobs in neighboring towns.
            location=(str(location or "Location not stated")+"; Deutschland")
            title=x.get("titel") or x.get("stellenangebotsTitel") or x.get("beruf") or ""
            if not title:continue
            company=x.get("firma") or x.get("arbeitgeber") or x.get("arbeitgeberName") or "Employer (BA)"
            if isinstance(company,dict):company=company.get("name") or company.get("firmenname") or "Employer (BA)"
            description=" ".join(str(x.get(f) or "") for f in ("stellenangebotsTitel","hauptberuf","beruf","branche","vertragsdauer","verguetungsangabe","datumErsteVeroeffentlichung"))
            url=x.get("externeUrl") or ("https://www.arbeitsagentur.de/jobsuche/jobdetail/"+urllib.parse.quote(str(reference),safe=""))
            if not str(url).startswith("https://"):continue
            output.append(dict(company=str(company)[:150],title=str(title)[:180],location=location,url=url,
                 description=description[:7500],source="German Federal Employment Agency (unofficial interface)",
                 published_at=str(x.get("datumErsteVeroeffentlichung") or x.get("aktuelleVeroeffentlichungsdatum") or x.get("datum") or ""),
                 remote=False,reference=str(reference),search_city=city,search_radius_km=radius,
                 employer_site_verified=False,
                 description_completeness="search excerpt only"))
        if len(listings)<size:break
    # Details are deliberately bounded and opt-in per source board. Search results
    # stay useful when detail calls fail; the adapter records completeness per item.
    try:
        detail_budget=max(0,min(30,int(board.get("detail_budget",0))))
    except (TypeError,ValueError):
        detail_budget=0
    for item in output[:detail_budget]:
        try:
            detail=german_job_detail(item.get("reference",""))
            if detail and len(detail)>len(item.get("description",""))+60:
                item["description"]=detail[:11000]
                item["description_completeness"]="BA public detail response"
        except (urllib.error.HTTPError,urllib.error.URLError,ValueError,KeyError,TimeoutError):
            item["detail_fetch_status"]="failed"
        else:
            item["detail_fetch_status"]="succeeded" if detail else "empty"
    return output

def german_job_detail(reference):
    """Fetch actual BA description for reliable CV and sponsorship evidence."""
    code=base64.b64encode(reference.encode("utf-8")).decode("ascii")
    address=BA_BASE+"/pc/v4/jobdetails/"+urllib.parse.quote(code,safe="")
    headers={"X-API-Key":"jobboerse-jobsuche","Accept":"application/json",
             "User-Agent":"EngineeringCareerRadar/4.0 (personal job research)"}
    with urllib.request.urlopen(urllib.request.Request(address,headers=headers),timeout=15) as response:
        detail=json.load(response)
    if not isinstance(detail,dict):return ""
    parts=[]
    for key in ("stellenbeschreibung","stellenAngebot","stellenangebot","beschreibung","aufgaben",
                "anforderungen","wirBieten","wirErwarten","konditionen","arbeitgeberdarstellung"):
        value=detail.get(key)
        if isinstance(value,str):parts.append(value)
        elif isinstance(value,dict):parts.extend(str(x) for x in value.values() if isinstance(x,str))
    return " ".join(parts)[:11000]
