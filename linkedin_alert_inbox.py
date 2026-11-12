"""Personal LinkedIn job-alert inbox. Never logs in or requests LinkedIn pages.

Records are supplied explicitly by the user (e.g. from their job alert
messages), not scraped. No source publication date is inferred from an email
or import timestamp. The ordinary Career Radar CV engine screens them.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse
from public_source_adapters import vacancy

MAX_INBOX_ITEMS = 500
LINKEDIN_ID = re.compile(r'^/(?:comm/)?jobs/view/(\d{6,20})(?:/|$)',re.I)


def canonical_linkedin_job_url(raw):
    try:
        parsed=urlparse(str(raw or '').strip())
    except ValueError:
        return ''
    host=(parsed.hostname or '').lower()
    if parsed.scheme!='https' or host not in (
        'linkedin.com','www.linkedin.com','de.linkedin.com'):
        return ''
    found=LINKEDIN_ID.match(parsed.path)
    if not found or parsed.username or parsed.password or parsed.port:
        return ''
    return 'https://www.linkedin.com/jobs/view/'+found.group(1)+'/'


def inbox_postings(path):
    """Return validated user-entered jobs, never fetching or enriching at LinkedIn."""
    try:
        data=json.loads(Path(path).read_text(encoding='utf-8'))
    except FileNotFoundError:
        return []
    if not isinstance(data,dict) or not isinstance(data.get('jobs'),list):
        raise ValueError('Invalid private LinkedIn alert inbox')
    output=[]
    seen=set()
    for item in data['jobs'][-MAX_INBOX_ITEMS:]:
        if not isinstance(item,dict):
            continue
        link=canonical_linkedin_job_url(item.get('url'))
        title=str(item.get('title') or '').strip()[:180]
        company=str(item.get('company') or '').strip()[:140]
        location=str(item.get('location') or '').strip()[:160]
        description=str(item.get('description') or '').strip()[:3500]
        if not link or len(title)<3 or len(company)<2 or len(location)<2 or link in seen:
            continue
        seen.add(link)
        record=vacancy(company,title,location,link,description,
            'LinkedIn Job Alerts (user imported)','',False,
            source_attribution='LinkedIn Job Alerts (user imported)',
            posting_date_basis='user_alert_import_no_employer_posting_date',
            description_completeness=('User-supplied job alert excerpt; original advert unverified'
                                      if description else
                                      'Job title and employer supplied by user; description unavailable'),
            employer_posting_id=link.split('/jobs/view/')[1].strip('/'),
            listing_status='not_verified',
            imported_from_user_alert=True,
            alert_imported_at=str(item.get('imported_at') or '')[:35])
        if record:output.append(record)
    return output
