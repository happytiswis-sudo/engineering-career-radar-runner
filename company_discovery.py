"""Nationwide German employer discovery and cautious hidden-opportunity research.

Uses a small, rotating Google Search budget via SerpApi, then checks only
public official company websites and their linked career/contact pages.
A missing vacancy is never inferred from a failed or incomplete crawl.
"""
from __future__ import annotations

import datetime as dt
import html
import ipaddress
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

AGENT = "EngineeringCareerRadar/1.0 (+personal employer research)"
SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
MAX_SEARCH_RESULTS = 10
MAX_COMPANIES = 600
MAX_VERIFY_PER_RUN = 12
MAX_PAGE_BYTES = 850_000
CAREER_WORDS = re.compile(r"(karriere|career|jobs?|stellen|bewerbung|recruit|personalabteilung|join.?us|work.?with.?us)", re.I)
CONTACT_WORDS = re.compile(r"(kontakt|contact|impressum|imprint|ansprechpartner)", re.I)
VACANCY_WORDS = re.compile(r"(stellenangebote|offene stellen|jobangebote|job openings|open positions|vacancies|apply now|jetzt bewerben|bewerben sie sich|bewerbung)", re.I)
NO_OPENINGS = re.compile(r"(keine offenen stellen|derzeit keine offenen stellen|aktuell keine stellenangebote|no current openings|no open positions|currently no vacancies|there are no open roles)", re.I)
GENERIC_MAILBOX = re.compile(r"^(info|kontakt|contact|karriere|career|jobs?|bewerbung|bewerbungen|recruiting|hr|personal|office|bewerber)@", re.I)
BLOCKED_HOSTS = {
    "linkedin.com", "facebook.com", "instagram.com", "youtube.com", "x.com",
    "twitter.com", "wikipedia.org", "kununu.com", "xing.com", "glassdoor.com",
    "indeed.com", "stepstone.de", "monster.de", "stellenanzeigen.de",
    "wlw.de", "wer-zu-wem.de", "northdata.de", "unternehmensregister.de",
    "handelsregister.de", "dasoertliche.de", "gelbeseiten.de", "11880.com",
    "crunchbase.com", "zoominfo.com", "opencorporates.com"
}
ATS_HOSTS = (
    "jobs.personio.", "personio.de", "personio.com", "boards.greenhouse.io",
    "job-boards.greenhouse.io", "jobs.ashbyhq.com", "jobs.lever.co",
    "careers.smartrecruiters.com", "apply.workable.com", "pinpointhq.com",
    "jobs.workable.com", "myworkdayjobs.com", "softgarden.io",
    "recruitee.com", "teamtailor.com", "jobs.jobvite.com"
)

STATES = [
    ("Nordrhein-Westfalen", "NRW", True),
    ("Hessen", "Hessen", True),
    ("Baden-Württemberg", "Baden-Württemberg", True),
    ("Rheinland-Pfalz", "Rheinland-Pfalz", True),
    ("Saarland", "Saarland", True),
    ("Niedersachsen", "Niedersachsen", True),
    ("Bremen", "Bremen", True),
    ("Bayern", "Bayern", False),
    ("Berlin", "Berlin", False),
    ("Brandenburg", "Brandenburg", False),
    ("Hamburg", "Hamburg", False),
    ("Mecklenburg-Vorpommern", "Mecklenburg-Vorpommern", False),
    ("Sachsen", "Sachsen", False),
    ("Sachsen-Anhalt", "Sachsen-Anhalt", False),
    ("Schleswig-Holstein", "Schleswig-Holstein", False),
    ("Thüringen", "Thüringen", False),
]
INDUSTRIES = [
    ("Maschinenbau", "engineering manufacturing"),
    ("Automatisierungstechnik", "automation robotics"),
    ("Elektrotechnik", "electrical engineering"),
    ("Produktionstechnik", "production technology"),
    ("Medizintechnik", "medical devices"),
    ("Energietechnik", "energy technology"),
    ("Fahrzeugzulieferer", "automotive suppliers"),
    ("Anlagenbau", "plant engineering"),
    ("Logistiktechnik", "industrial logistics"),
    ("Werkstofftechnik", "materials technology"),
    ("Umwelttechnik", "environmental technology"),
    ("Luftfahrttechnik", "aerospace aviation"),
]

def _domain(host: str) -> str:
    host = (host or "").lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    return host

def _blocked(host: str) -> bool:
    host = _domain(host)
    if not host or host == "localhost" or host.endswith((".local", ".internal")):
        return True
    try:
        ip = ipaddress.ip_address(host)
        return not ip.is_global
    except ValueError:
        pass
    return any(host == x or host.endswith("." + x) for x in BLOCKED_HOSTS)

def _safe_http_url(value: str, base: str = "") -> str:
    if not value:
        return ""
    url = urljoin(base, value.strip())
    try:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return ""
        if _blocked(parsed.hostname):
            return ""
        clean = urlunparse(("https", parsed.netloc, parsed.path or "/", "", parsed.query, ""))
        return clean[:1200]
    except ValueError:
        return ""

def build_query_plan(run_rotation: int = 0, budget: int = 3):
    """Every run prioritizes two western state searches and one rotating national search."""
    budget = max(0, min(6, int(budget)))
    west = [s for s in STATES if s[2]]
    rest = [s for s in STATES if not s[2]]
    rotation = int(run_rotation or 0)
    day = dt.datetime.now(dt.timezone.utc).date().toordinal()
    cursor = (day + rotation) % len(STATES)
    west_cursor = (day + rotation) % len(west)
    nonwest_cursor = (day // 3 + rotation) % len(rest)
    sectors = [INDUSTRIES[(day + rotation + i * 3) % len(INDUSTRIES)] for i in range(budget)]
    plan = []
    for i in range(budget):
        if budget == 2 and i == 0 and west:
            state = west[west_cursor]
        elif budget == 2 and i == 1 and rest:
            # Pair each western-priority search with a rotating state outside the west.
            state = rest[nonwest_cursor]
        elif i < 2 and west:
            state = west[(west_cursor + i) % len(west)]
        elif i == 2 and rest:
            state = rest[nonwest_cursor]
        else:
            state = STATES[(cursor + i) % len(STATES)]
        sector = sectors[i]
        query = f'{sector[0]} Unternehmen Hersteller {state[1]} offizielle Website'
        plan.append({
            "query": query, "state": state[0], "region_priority": "west" if state[2] else "national",
            "industry": sector[0], "industry_group": sector[1]
        })
    return plan

class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.text_parts = []
        self.title_parts = []
        self.in_title = False
        self.skip_depth = 0
        self.mails = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style", "noscript", "svg"):
            self.skip_depth += 1
        if tag == "title":
            self.in_title = True
        if tag == "a":
            href = attrs.get("href", "")
            label = attrs.get("aria-label", "") or attrs.get("title", "")
            if href:
                self.links.append((href[:1200], label[:200]))
        if tag == "meta" and (attrs.get("name") or "").lower() in ("description", "og:description"):
            self.text_parts.append(attrs.get("content", "")[:500])
        if tag == "a" and attrs.get("href", "").lower().startswith("mailto:"):
            address = attrs["href"][7:].split("?", 1)[0].strip().lower()
            if GENERIC_MAILBOX.match(address) and len(address) < 160:
                self.mails.add(address)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.skip_depth:
            self.skip_depth -= 1
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.skip_depth:
            return
        value = re.sub(r"\s+", " ", data).strip()
        if not value:
            return
        if self.in_title:
            self.title_parts.append(value)
        self.text_parts.append(value)

    @property
    def title(self):
        return " ".join(self.title_parts)[:220]

    @property
    def text(self):
        return " ".join(self.text_parts)[:18000]

class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe = _safe_http_url(newurl)
        if not safe:
            raise urllib.error.HTTPError(req.full_url, code, "unsafe_redirect", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, safe)

def _open_public(request, timeout=10):
    opener = urllib.request.build_opener(_SafeRedirectHandler())
    return opener.open(request, timeout=timeout)

def _read_page(url: str, timeout: int = 10):
    request = urllib.request.Request(url, headers={
        "User-Agent": AGENT, "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "de,en;q=0.8"
    })
    with _open_public(request, timeout=timeout) as response:
        final_url = _safe_http_url(response.geturl())
        content_type = (response.headers.get("Content-Type") or "").lower()
        if not final_url or ("html" not in content_type and content_type):
            raise ValueError("not_public_html")
        raw = response.read(MAX_PAGE_BYTES + 1)
        if len(raw) > MAX_PAGE_BYTES:
            raw = raw[:MAX_PAGE_BYTES]
        charset = response.headers.get_content_charset() or "utf-8"
        return final_url, raw.decode(charset, errors="replace")

def _robots_allowed(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"https://{parsed.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        request = urllib.request.Request(robots_url, headers={"User-Agent": AGENT})
        with _open_public(request, timeout=6) as response:
            body = response.read(120_000).decode("utf-8", errors="replace")
        parser.parse(body.splitlines())
        return parser.can_fetch(AGENT, url)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return False
        if exc.code == 404:
            parser.parse([])
            return parser.can_fetch(AGENT, url)
        return False
    except Exception:
        return False

def _career_and_contact_links(page: _PageParser, base_url: str):
    careers, contacts = [], []
    for href, label in page.links:
        full = _safe_http_url(href, base_url)
        if not full:
            continue
        host = _domain(urlparse(full).hostname or "")
        path = urlparse(full).path
        haystack = f"{label} {path} {host}"
        if CAREER_WORDS.search(haystack) or any(host.endswith(x) for x in ATS_HOSTS):
            careers.append(full)
        if CONTACT_WORDS.search(haystack):
            contacts.append(full)
    return list(dict.fromkeys(careers))[:4], list(dict.fromkeys(contacts))[:3]

def _vacancy_links(page: _PageParser, base_url: str):
    links = []
    for href, label in page.links:
        full = _safe_http_url(href, base_url)
        if not full:
            continue
        haystack = f"{label} {urlparse(full).path} {urlparse(full).hostname or ''}"
        if VACANCY_WORDS.search(haystack) or any(_domain(urlparse(full).hostname or "").endswith(x) for x in ATS_HOSTS):
            links.append(full)
    return list(dict.fromkeys(links))[:20]

def _generic_emails(page: _PageParser):
    return sorted(page.mails)[:5]

def verify_company(candidate: dict, checked_at: str | None = None):
    """Verify homepage and, where linked, careers/contact pages with bounded public requests."""
    checked_at = checked_at or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    website = _safe_http_url(candidate.get("website", ""))
    if not website:
        candidate.update({"verification_status": "not_checked", "career_status": "not_checked",
                          "last_checked_at": checked_at, "check_note": "No safe official HTTPS website URL."})
        return candidate
    try:
        if not _robots_allowed(website):
            candidate.update({"verification_status": "blocked", "career_status": "blocked",
                              "last_checked_at": checked_at, "check_note": "Homepage disallowed by robots.txt or robots policy could not be verified."})
            return candidate
        final_url, raw = _read_page(website)
        home = _PageParser()
        home.feed(raw)
        host = _domain(urlparse(final_url).hostname or "")
        candidate["website"] = final_url
        candidate["domain"] = host
        candidate["official_site_title"] = home.title
        candidate["site_description"] = home.text[:700]
        careers, contacts = _career_and_contact_links(home, final_url)
        candidate["contact_url"] = contacts[0] if contacts else ""
        candidate["public_contact_email"] = _generic_emails(home)[0] if _generic_emails(home) else ""
        candidate["contact_source_url"] = final_url if candidate.get("public_contact_email") else ""
        if not candidate.get("public_contact_email") and candidate.get("contact_url"):
            contact_url = candidate["contact_url"]
            contact_host = _domain(urlparse(contact_url).hostname or "")
            # Only inspect contact pages on the verified company's own host/domain.
            if contact_host == host or contact_host.endswith("." + host) or host.endswith("." + contact_host):
                if _robots_allowed(contact_url):
                    try:
                        contact_final, contact_raw = _read_page(contact_url)
                        contact_page = _PageParser()
                        contact_page.feed(contact_raw)
                        found_emails = _generic_emails(contact_page)
                        if found_emails:
                            candidate["public_contact_email"] = found_emails[0]
                            candidate["contact_source_url"] = contact_final
                    except Exception:
                        pass
        candidate["verification_status"] = "website_verified"
        candidate["last_checked_at"] = checked_at
        if not careers:
            candidate.update({"career_status": "no_public_careers_page",
                              "open_vacancy_count": None,
                              "check_note": "Official homepage checked; no linked public careers page was identified. This does not prove there are no vacancies."})
            candidate["hidden_opportunity_candidate"] = bool(candidate.get("contact_url") or candidate.get("public_contact_email"))
            return candidate
        career_url = careers[0]
        candidate["careers_url"] = career_url
        if not _robots_allowed(career_url):
            candidate.update({"career_status": "blocked", "open_vacancy_count": None,
                              "check_note": "Careers page blocked by robots.txt or robots policy could not be verified."})
            candidate["hidden_opportunity_candidate"] = False
            return candidate
        career_final, career_raw = _read_page(career_url)
        career = _PageParser()
        career.feed(career_raw)
        vacancies = _vacancy_links(career, career_final)
        candidate["vacancy_urls"] = vacancies
        candidate["open_vacancy_count"] = len(vacancies) if vacancies else 0
        text = career.text
        if vacancies:
            candidate["career_status"] = "vacancies_found"
            candidate["hidden_opportunity_candidate"] = False
            candidate["check_note"] = "Public career page links to vacancy or ATS listings; verify each opening at its source."
        elif NO_OPENINGS.search(text):
            candidate["career_status"] = "checked_no_openings"
            candidate["hidden_opportunity_candidate"] = True
            candidate["check_note"] = "Career page explicitly states that no openings are currently available."
        else:
            candidate["career_status"] = "careers_page_found_no_jobs"
            candidate["hidden_opportunity_candidate"] = True
            candidate["check_note"] = "Career page checked; no vacancy links were detected. This is not proof that the employer has no vacancies."
        if not candidate.get("public_contact_email") and not candidate.get("contact_url"):
            _, career_contacts = _career_and_contact_links(career, career_final)
            candidate["contact_url"] = career_contacts[0] if career_contacts else ""
            candidate["contact_source_url"] = career_final if candidate.get("contact_url") else ""
        candidate["verification_status"] = "website_and_careers_checked"
        return candidate
    except urllib.error.HTTPError as exc:
        candidate.update({"verification_status": "blocked" if exc.code in (401, 403, 429) else "not_checked",
                          "career_status": "blocked" if exc.code in (401, 403, 429) else "not_checked",
                          "last_checked_at": checked_at, "check_note": f"Public site returned HTTP {exc.code}; no vacancy conclusion."})
    except Exception as exc:
        candidate.update({"verification_status": "not_checked", "career_status": "not_checked",
                          "last_checked_at": checked_at, "check_note": f"Site check unavailable ({type(exc).__name__}); no vacancy conclusion."})
    candidate["hidden_opportunity_candidate"] = False
    return candidate

def _serpapi_search(query: str, api_key: str):
    params = urllib.parse.urlencode({
        "engine": "google", "q": query, "google_domain": "google.de",
        "gl": "de", "hl": "de", "num": MAX_SEARCH_RESULTS,
        "api_key": api_key
    })
    request = urllib.request.Request(SERPAPI_ENDPOINT + "?" + params, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(request, timeout=18) as response:
        data = json.load(response)
    if data.get("error"):
        message = str(data.get("error", "")).casefold()
        if "quota" in message or "limit" in message or "out of searches" in message:
            raise RuntimeError("serpapi_quota_exhausted")
        raise ValueError("serpapi_error")
    return data.get("organic_results") or []


def _serper_search(query: str, api_key: str):
    """Google SERP fallback with an independent free starter allowance."""
    body = json.dumps({"q": query, "gl": "de", "hl": "de", "num": MAX_SEARCH_RESULTS}).encode("utf-8")
    request = urllib.request.Request("https://google.serper.dev/search", data=body,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json",
                 "Accept": "application/json", "User-Agent": AGENT}, method="POST")
    with urllib.request.urlopen(request, timeout=18) as response:
        data = json.load(response)
    if data.get("message") or data.get("error"):
        raise ValueError("serper_error")
    return [{"title": x.get("title", ""), "link": x.get("link", ""),
             "snippet": x.get("snippet", "")}
            for x in (data.get("organic") or []) if isinstance(x, dict)]


def _cloro_search(query: str, api_key: str):
    """One sequential Google SERP request; free Cloro accounts allow one in-flight request."""
    body = json.dumps({"query": query, "country": "DE"}).encode("utf-8")
    request = urllib.request.Request("https://api.cloro.dev/v1/monitor/google", data=body,
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json",
                 "Accept": "application/json", "User-Agent": AGENT}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read(1200).decode("utf-8", "ignore").casefold()
        if exc.code == 403 and ("insufficient credit" in detail or "credits" in detail):
            raise RuntimeError("cloro_credits_exhausted")
        raise
    result = data.get("result") or {}
    rows = result.get("organicResults") or result.get("organic_results") or []
    return [{"title": x.get("title", ""), "link": x.get("link", ""),
             "snippet": x.get("snippet", x.get("description", ""))}
            for x in rows if isinstance(x, dict)]


def _searxng_search(query: str, base_url: str, api_token=""):
    """Query an operator-configured SearXNG instance; public instances are not assumed."""
    base = str(base_url or "").strip().rstrip("/")
    if not base:
        raise RuntimeError("searxng_not_configured")
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise ValueError("invalid_searxng_base_url")
    params = urllib.parse.urlencode({"q": query, "format": "json", "language": "de", "categories": "general"})
    headers = {"User-Agent": AGENT, "Accept": "application/json"}
    if api_token:
        headers["Authorization"] = "Bearer " + api_token
    request = urllib.request.Request(base + "/search?" + params, headers=headers)
    with urllib.request.urlopen(request, timeout=25) as response:
        data = json.load(response)
    return [{"title": x.get("title", ""), "link": x.get("url", ""),
             "snippet": x.get("content", "")}
            for x in (data.get("results") or []) if isinstance(x, dict)]


def _search_company_query(query: str, serpapi_key: str, serper_key: str,
                          cloro_keys=None, searxng_url="", searxng_token=""):
    """Fallback chain: SerpApi -> Serper -> Cloro account pool -> configured SearXNG."""
    cloro_keys = [str(x).strip() for x in (cloro_keys or []) if str(x).strip()]
    errors = []
    if serpapi_key:
        try:
            return _serpapi_search(query, serpapi_key), "SerpApi"
        except urllib.error.HTTPError as exc:
            if exc.code != 429:
                raise
            errors.append("SerpApi HTTP 429")
        except RuntimeError as exc:
            if str(exc) != "serpapi_quota_exhausted":
                raise
            errors.append("SerpApi quota")
    if serper_key:
        try:
            return _serper_search(query, serper_key), "Serper" if not errors else "Serper fallback"
        except urllib.error.HTTPError as exc:
            if exc.code != 429:
                raise
            errors.append("Serper HTTP 429")
        except RuntimeError as exc:
            errors.append(str(exc))
    if cloro_keys:
        # Alternate account order by stable query hash. Calls remain sequential:
        # each free account is limited to one concurrent monitor request.
        offset = sum(ord(ch) for ch in query) % len(cloro_keys)
        ordered = cloro_keys[offset:] + cloro_keys[:offset]
        for index, key in enumerate(ordered):
            try:
                return _cloro_search(query, key), "Cloro account " + str(index + 1)
            except urllib.error.HTTPError as exc:
                if exc.code == 429:
                    errors.append("Cloro HTTP 429")
                    continue
                raise
            except RuntimeError as exc:
                if str(exc) == "cloro_credits_exhausted":
                    errors.append("Cloro credits exhausted")
                    continue
                raise
    if searxng_url:
        return _searxng_search(query, searxng_url, searxng_token), "SearXNG fallback"
    if errors:
        raise RuntimeError("search_providers_exhausted:" + ",".join(errors))
    raise RuntimeError("search_provider_not_configured")

def _company_name(title: str):
    title = html.unescape(re.sub(r"\s+", " ", title or "")).strip()
    title = re.split(r"\s+[|–—:]\s+", title, maxsplit=1)[0]
    title = re.sub(r"\s*[-–—]\s*(Startseite|Home|Unternehmen|Offizielle Website).*", "", title, flags=re.I)
    return title[:150].strip(" -|")

def _is_ats_host(host: str) -> bool:
    host = _domain(host)
    return any(host == x or host.endswith("." + x) for x in (
        "personio.de", "personio.com", "greenhouse.io", "ashbyhq.com",
        "lever.co", "smartrecruiters.com", "workable.com", "pinpointhq.com",
        "myworkdayjobs.com", "softgarden.io", "recruitee.com", "teamtailor.com",
        "jobvite.com"
    ))

def _candidate_from_result(result: dict, query: dict, now: str):
    link = _safe_http_url(result.get("link", ""))
    if not link:
        return None
    parsed = urlparse(link)
    host = _domain(parsed.hostname or "")
    if _blocked(host) or _is_ats_host(host):
        return None
    name = _company_name(result.get("title", ""))
    if len(name) < 2 or re.search(r"(maschinenbauunternehmen|firmenverzeichnis|branchenbuch|gelbe seiten|top unternehmen)", name, re.I):
        return None
    snippet = html.unescape(re.sub(r"\s+", " ", result.get("snippet", "") or ""))[:700]
    return {
        "company": name, "website": f"https://{parsed.netloc}/",
        "domain": host, "company_domain": host, "state": query["state"],
        "region_priority": query["region_priority"], "industry": query["industry"],
        "industry_group": query["industry_group"], "discovery_source": "SerpApi Google Search",
        "discovery_query": query["query"], "source_url": link,
        "source_snippet": snippet, "first_discovered_at": now,
        "hidden_opportunity_candidate": False, "verification_status": "not_checked",
        "career_status": "not_checked", "open_vacancy_count": None
    }

def company_quality_metrics(companies):
    """Count separate levels of employer evidence; never conflate them."""
    rows = [x for x in (companies or []) if isinstance(x, dict)]
    verified = sum(x.get("verification_status") in ("website_verified", "website_and_careers_checked") for x in rows)
    careers = sum(x.get("career_status") in ("vacancies_found", "checked_no_openings", "careers_page_found_no_jobs") for x in rows)
    vacancy_links = sum(len(x.get("vacancy_urls") or []) for x in rows if x.get("career_status") == "vacancies_found")
    contactable_hidden = sum(bool(x.get("hidden_opportunity_candidate") and (x.get("public_contact_email") or x.get("contact_url"))) for x in rows)
    evidence_states = {}
    for item in rows:
        state = ("vacancy_links_verified" if item.get("career_status") == "vacancies_found" and item.get("vacancy_urls") else
                 "careers_page_checked" if item.get("career_status") in ("checked_no_openings", "careers_page_found_no_jobs") else
                 "official_website_checked" if item.get("verification_status") in ("website_verified", "website_and_careers_checked") else
                 "discovery_only")
        evidence_states[state] = evidence_states.get(state, 0) + 1
    return {"verified_websites": verified, "verified_careers_pages": careers,
            "public_vacancy_links": vacancy_links,
            "contactable_hidden_opportunity_prospects": contactable_hidden,
            "evidence_states": evidence_states}


def discover_german_companies(existing=None, api_key=None, run_rotation=0,
                              query_budget=3, verify_budget=MAX_VERIFY_PER_RUN,
                              serper_api_key=None, cloro_api_keys=None, searxng_base_url=None):
    """Merge rotating nationwide discoveries with SerpApi/Serper quota failover."""
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    api_key = (api_key or os.environ.get("SERPAPI_API_KEY", "")).strip()
    serper_api_key = (serper_api_key or os.environ.get("SERPER_API_KEY", "")).strip()
    cloro_api_keys = cloro_api_keys or [os.environ.get("CLORO_API_KEY_1", ""),
                                       os.environ.get("CLORO_API_KEY_2", "")]
    searxng_base_url = (searxng_base_url or os.environ.get("SEARXNG_BASE_URL", "")).strip()
    searxng_api_token = os.environ.get("SEARXNG_API_TOKEN", "").strip()
    prior = existing if isinstance(existing, list) else []
    by_domain = {}
    for item in prior:
        if isinstance(item, dict) and item.get("domain"):
            host = _domain(item["domain"])
            if host and not _blocked(host) and not _is_ats_host(host):
                by_domain[host] = dict(item)
    if not api_key and not serper_api_key and not any(cloro_api_keys) and not searxng_base_url:
        return {
            "generated_at": now, "provider": "SerpApi / Serper Google Search",
            "status": "not_configured", "query_budget": 0, "queries_attempted": 0,
            "queries_succeeded": 0, "companies": list(by_domain.values())[:MAX_COMPANIES],
            "note": "No search provider is configured. Existing employer records are preserved."
        }
    plan = build_query_plan(run_rotation, query_budget)
    queries_attempted = queries_succeeded = fallback_queries = 0
    provider_counts = {}
    errors = []
    newly_seen = []
    for query in plan:
        queries_attempted += 1
        try:
            results, provider = _search_company_query(query["query"], api_key, serper_api_key, cloro_api_keys, searxng_base_url, searxng_api_token)
            queries_succeeded += 1
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
            if provider.startswith("Serper fallback"):
                fallback_queries += 1
            for result in results[:MAX_SEARCH_RESULTS]:
                candidate = _candidate_from_result(result, query, now)
                if not candidate:
                    continue
                domain = candidate["domain"]
                if domain in by_domain:
                    old = by_domain[domain]
                    old["last_discovered_at"] = now
                    old["discovery_query"] = query["query"]
                    old["state"] = query["state"]
                    old["industry"] = query["industry"]
                    old["region_priority"] = query["region_priority"]
                    if candidate.get("source_snippet"):
                        old["source_snippet"] = candidate["source_snippet"]
                    continue
                by_domain[domain] = candidate
                newly_seen.append(domain)
        except urllib.error.HTTPError as exc:
            errors.append({"query": query["query"], "error": f"http_{exc.code}"})
            if exc.code in (401, 403, 429):
                break
        except Exception as exc:
            errors.append({"query": query["query"], "error": str(exc)[:100] or type(exc).__name__})
    # Recheck stale companies first, then new discoveries; keep west Germany ahead.
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)
    def stale(item):
        raw = item.get("last_checked_at") or ""
        try:
            stamp = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if stamp.tzinfo is None: stamp = stamp.replace(tzinfo=dt.timezone.utc)
            return stamp < cutoff
        except Exception:
            return True
    candidates = list(by_domain.values())
    candidates.sort(key=lambda x: (
        0 if x.get("region_priority") == "west" else 1,
        0 if stale(x) else 1,
        0 if x.get("domain") in newly_seen else 1,
        x.get("domain", "")
    ))
    verified = 0
    for item in candidates:
        if verified >= max(0, int(verify_budget)):
            break
        if item.get("verification_status") == "website_and_careers_checked" and not stale(item) and item.get("career_status") in ("vacancies_found", "checked_no_openings", "careers_page_found_no_jobs"):
            continue
        if item.get("verification_status") == "website_verified" and not stale(item) and item.get("career_status") == "no_public_careers_page":
            continue
        verify_company(item, now)
        verified += 1
        time.sleep(0.2)
    rows = sorted(by_domain.values(), key=lambda x: (
        0 if x.get("region_priority") == "west" else 1,
        0 if x.get("hidden_opportunity_candidate") else 1,
        x.get("company", "").casefold()
    ))[:MAX_COMPANIES]
    return {
        "generated_at": now, "provider": "SerpApi / Serper / Cloro / SearXNG",
        "status": "ok" if queries_succeeded else ("partial" if errors else "empty"),
        "query_budget": len(plan), "queries_attempted": queries_attempted,
        "queries_succeeded": queries_succeeded, "provider_query_counts": provider_counts,
        "fallback_queries": fallback_queries, "verification_attempted": verified,
        "new_companies": len(newly_seen), "hidden_opportunity_candidates": sum(bool(x.get("hidden_opportunity_candidate")) for x in rows),
        "western_germany_companies": sum(x.get("region_priority") == "west" for x in rows),
        "national_company_count": len(rows), "quality_metrics": company_quality_metrics(rows), "query_plan": plan, "errors": errors[:10],
        "companies": rows,
        "note": "Company discovery is separate from vacancy retrieval. 'Checked no openings' requires an explicit statement on a checked careers page; crawl failures and missing career pages are not counted as no vacancies. Public contact details are limited to generic business mailboxes and published contact pages."
    }

if __name__ == "__main__":
    result = discover_german_companies(query_budget=3)
    print(json.dumps({k: v for k, v in result.items() if k != "companies"}, ensure_ascii=False, indent=2))
