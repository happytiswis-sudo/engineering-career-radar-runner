"""Bounded public job-page status verification for stale vacancy URLs."""
from __future__ import annotations
from html import unescape
from html.parser import HTMLParser
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen


_CLOSED = re.compile(
    r"position (?:has been )?filled|job (?:is )?no longer available|"
    r"vacancy (?:is )?closed|application period (?:has )?ended|"
    r"stellenangebot (?:ist )?nicht mehr verfügbar|stelle bereits besetzt|"
    r"bewerbungsfrist (?:ist )?abgelaufen|keine bewerbungen mehr|"
    r"this job has expired|job posting expired",
    re.I,
)


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def verify_public_job_page(url, timeout=6):
    """Return active/inactive/unknown; follow only same-host HTTPS redirects."""
    parsed = urlparse(str(url or ""))
    if parsed.scheme != "https" or not parsed.hostname:
        return {"status": "unknown", "reason": "unsafe_or_missing_https_url"}
    host = parsed.hostname.casefold()
    if host in ("localhost",) or host.endswith(".localhost") or host.endswith(".local"):
        return {"status": "unknown", "reason": "local_host_rejected"}
    request = Request(str(url), headers={
        "User-Agent": "EngineeringCareerRadar/5.2 (public vacancy status check)",
        "Accept": "text/html",
    })
    try:
        with urlopen(request, timeout=max(2, min(10, int(timeout)))) as response:
            final = urlparse(response.geturl())
            if final.scheme != "https" or not final.hostname or final.hostname.casefold() != host:
                return {"status": "unknown", "reason": "cross_host_redirect"}
            code = int(getattr(response, "status", 200) or 200)
            if code in (404, 410):
                return {"status": "inactive", "reason": "http_" + str(code)}
            if code < 200 or code >= 400:
                return {"status": "unknown", "reason": "http_" + str(code)}
            raw = response.read(120000).decode("utf-8", errors="replace")
    except Exception as exc:
        code = getattr(exc, "code", None)
        if code in (404, 410):
            return {"status": "inactive", "reason": "http_" + str(code)}
        return {"status": "unknown", "reason": type(exc).__name__}
    parser = _Text()
    parser.feed(raw)
    text = " ".join(unescape(x) for x in parser.parts)
    if _CLOSED.search(text):
        return {"status": "inactive", "reason": "closed_phrase_on_source_page"}
    return {"status": "active", "reason": "https_page_responded_without_closed_marker"}
