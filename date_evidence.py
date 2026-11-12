"""Bounded, same-employer public JobPosting JSON-LD date evidence.

Never infer publication dates from fetch time, URL IDs, expiry dates or HTTP
Last-Modified. Fallback is always "unknown" when employer evidence is absent.
"""
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import json
import re

class _JSONLDScripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.capture=False
        self.depth=0
        self.parts=[]
        self.scripts=[]
    def handle_starttag(self,tag,attrs):
        if tag!='script':return
        attributes=dict(attrs)
        self.capture='application/ld+json' in str(attributes.get('type','')).lower()
        self.parts=[]
    def handle_data(self,data):
        if self.capture:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag=='script' and self.capture:
            self.scripts.append(''.join(self.parts))
            self.capture=False

def jsonld_jobposting_date(html_text):
    parser=_JSONLDScripts()
    parser.feed(html_text[:500000])
    def visit(obj):
        if isinstance(obj,list):
            for item in obj:
                found=visit(item)
                if found:return found
        if not isinstance(obj,dict):return ''
        type_field=obj.get('@type') or []
        types=type_field if isinstance(type_field,list) else [type_field]
        if any(isinstance(t,str) and t.split('/')[-1].lower()=='jobposting'
               for t in types):
            value=obj.get('datePosted')
            if isinstance(value,str) and re.match(r'^\d{4}-\d\d-\d\d',value):
                try:
                    date.fromisoformat(value[:10])
                    return value[:35]
                except ValueError:
                    pass
        return visit(obj.get('@graph')) if '@graph' in obj else ''
    for raw in parser.scripts:
        try:structured=json.loads(raw)
        except (ValueError,TypeError):continue
        result=visit(structured)
        if result:return result
    return ''

def public_pinpoint_date(url,expected_host):
    parsed=urlparse(str(url))
    if parsed.scheme!='https' or parsed.hostname!=expected_host:
        return ''
    # Only read public employer career pages already supplied by Pinpoint.
    if not re.match(r'^/(?:[a-zA-Z-]{2,8}/)?(?:postings|jobs)/',parsed.path):
        return ''
    req=Request(url,headers={'User-Agent':'CareerRadar/1.0 (public-employer-job-date-check)',
                             'Accept':'text/html'})
    try:
        with urlopen(req,timeout=6) as response:
            if urlparse(response.geturl()).hostname!=expected_host:return ''
            page=response.read(280000)
        return jsonld_jobposting_date(page.decode('utf-8',errors='replace'))
    except (OSError,ValueError,UnicodeError,TimeoutError):
        return ''
