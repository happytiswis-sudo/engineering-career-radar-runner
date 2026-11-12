"""Conservative, persistent seen-before matching for archived vacancy runs.

The identity key is normalized employer + title + canonical URL (+ a Personio
requisition ID when available). A key match is a strong signal, not proof that
a vacancy is unchanged. Changed location, posting date or requisition evidence
is therefore surfaced for review and is never hidden by the dashboard's
new-only view.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

IGNORED_PARAMS = {
    'ref', 'referrer', 'source', 'src', 'trk', 'tracking', 'gh_src',
    'fbclid', 'gclid', 'mc_cid', 'mc_eid', 'campaign', 'utm_campaign',
}
MAX_KEYS = 120000
REGISTRY_SCHEMA_VERSION = 2
OBSERVATION_FIELDS = ('locations', 'posting_dates', 'posting_ids')


def canonical_url(raw):
    p = urlparse(str(raw or '').strip())
    if p.scheme.lower() not in ('https', 'http') or not p.netloc:
        return ''
    host = p.netloc.lower().removeprefix('www.')
    query = sorted(
        (k.lower(), v)
        for k, v in parse_qsl(p.query, keep_blank_values=True)
        if k.lower() not in IGNORED_PARAMS and not k.lower().startswith('utm_')
    )
    return urlunparse(('https', host, p.path.rstrip('/'), '', urlencode(query), ''))


def job_key(job):
    title = ' '.join(str(job.get('title') or '').casefold().split())
    company = ' '.join(str(job.get('company') or '').casefold().split())
    url = canonical_url(job.get('url'))
    if not title or not company or not url:
        return None
    # Use requisition IDs to split vacancies only when the source URL itself
    # is generic. A requisition-ID change on a specific vacancy URL is evidence
    # for review_required, not proof of a new job.
    posting_id = str(job.get('employer_posting_id') or job.get('reference') or '').strip()
    path_parts = [part for part in urlparse(url).path.casefold().split('/') if part]
    generic_paths = {'job', 'jobs', 'career', 'careers', 'vacancy', 'vacancies',
                     'opening', 'openings', 'apply', 'job-search', 'stellenangebote'}
    generic_url = (not path_parts or len(path_parts) <= 1
                   or path_parts[-1] in generic_paths)
    if posting_id and generic_url:
        provider = ' '.join(str(job.get('source') or '').casefold().split())
        url += '|posting:' + provider + ':' + posting_id.casefold()
    return sha256((company + '|' + title + '|' + url).encode('utf-8')).hexdigest()


def _normalise_location(value):
    return ' '.join(str(value or '').casefold().split())


def _normalise_date(value):
    raw = str(value or '').strip()
    if not raw:
        return ''
    # Compare calendar dates rather than formatting/time-zone differences.
    candidate = raw.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(candidate).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        match = re.match(r'^(\d{4}-\d{2}-\d{2})', raw)
        return match.group(1) if match else ' '.join(raw.casefold().split())


def _observations(job):
    location = _normalise_location(job.get('location'))
    posted = _normalise_date(job.get('published_at'))
    posting_id = str(job.get('employer_posting_id') or '').strip()
    return {
        'locations': [location] if location else [],
        'posting_dates': [posted] if posted else [],
        'posting_ids': [posting_id] if posting_id else [],
    }


def _merge_observations(left, right):
    result = {}
    for field in OBSERVATION_FIELDS:
        values = []
        for source in (left or {}, right or {}):
            candidate = source.get(field, [])
            if candidate is None:
                continue
            if not isinstance(candidate, list):
                raise ValueError('Malformed seen-registry observation field: ' + field)
            for value in candidate:
                item = str(value or '').strip()
                if item and item not in values:
                    values.append(item)
        result[field] = sorted(values)
    return result


def _new_entry(run, job):
    return {
        'first_run': run,
        'last_run': run,
        'count': 1,
        **_observations(job),
    }


def _record_observations(entry, job):
    merged = dict(entry)
    observations = _merge_observations(entry, _observations(job))
    merged.update(observations)
    return merged


def _review_reasons(job, old):
    current = _observations(job)
    reasons = []
    previous_locations = set(old.get('locations') or [])
    current_locations = set(current['locations'])
    if len(previous_locations) > 1:
        reasons.append('multiple_historical_locations')
    if previous_locations and current_locations and not current_locations.issubset(previous_locations):
        reasons.append('location_changed')
    elif previous_locations and not current_locations:
        reasons.append('location_missing_in_current_listing')
    elif current_locations and not previous_locations:
        reasons.append('location_not_recorded_in_prior_archive')

    previous_dates = set(old.get('posting_dates') or [])
    current_dates = set(current['posting_dates'])
    if len(previous_dates) > 1:
        reasons.append('multiple_historical_posting_dates')
    if previous_dates and current_dates and not current_dates.issubset(previous_dates):
        reasons.append('posting_date_changed')
    elif previous_dates and not current_dates:
        reasons.append('posting_date_missing_in_current_listing')
    elif current_dates and not previous_dates:
        reasons.append('posting_date_not_recorded_in_prior_archive')

    previous_ids = set(old.get('posting_ids') or [])
    current_ids = set(current['posting_ids'])
    if len(previous_ids) > 1:
        reasons.append('multiple_historical_requisition_ids')
    if previous_ids and current_ids and not current_ids.issubset(previous_ids):
        reasons.append('requisition_id_changed')
    elif previous_ids and not current_ids:
        reasons.append('requisition_id_missing_in_current_listing')
    elif current_ids and not previous_ids:
        reasons.append('requisition_id_not_recorded_in_prior_archive')
    return reasons


def _archive_entries(prior_index, limit=40):
    rows = prior_index.get('runs', []) if isinstance(prior_index, dict) else []
    sources = [r for r in rows if isinstance(r, dict) and r.get('archive_file')]
    sources.sort(key=lambda r: r.get('published_at') or '')
    return sources[-limit:]


def expected_archive_run_ids(prior_index, limit=40):
    return [str(entry.get('run_id') or '') for entry in _archive_entries(prior_index, limit)]


def registry_needs_archive_rebuild(registry, prior_index, limit=40):
    """Detect stale coverage or an old registry schema lacking review evidence."""
    if not isinstance(registry, dict) or not isinstance(registry.get('entries'), dict):
        return True
    try:
        schema_version = int(registry.get('schema_version', 0) or 0)
    except (TypeError, ValueError):
        return True
    if schema_version < REGISTRY_SCHEMA_VERSION:
        return True
    coverage = registry.get('coverage')
    if not isinstance(coverage, dict):
        return True
    expected = expected_archive_run_ids(prior_index, limit)
    actual = coverage.get('archive_run_ids')
    return actual != expected


def registry_from_archives(prior_index, reader, limit=40):
    sources = _archive_entries(prior_index, limit)
    all_sources = _archive_entries(prior_index, limit=10**9)
    registry = {}
    loaded = 0
    errors = 0
    loaded_run_ids = []
    for entry in sources:
        try:
            doc = reader(entry['archive_file'])
            if not isinstance(doc, dict):
                raise ValueError('Historical archive is not a JSON object')
            if str(doc.get('run_id') or '') != str(entry.get('run_id') or ''):
                raise ValueError('Historical run ID mismatch')
            if not isinstance(doc.get('jobs'), list):
                raise ValueError('Bad job archive')
        except (OSError, ValueError, TypeError, KeyError):
            errors += 1
            continue
        loaded += 1
        run = str(entry.get('run_id') or '')
        loaded_run_ids.append(run)
        for job in doc['jobs']:
            if not isinstance(job, dict):
                continue
            key = job_key(job)
            if not key:
                continue
            if key not in registry:
                registry[key] = _new_entry(run, job)
            else:
                old = registry[key]
                if old['last_run'] != run:
                    old['last_run'] = run
                    old['count'] += 1
                registry[key] = _record_observations(old, job)
    if len(registry) > MAX_KEYS:
        raise ValueError('Historical archive identity registry reached its size limit')
    expected_ids = [str(entry.get('run_id') or '') for entry in sources]
    return {
        'schema_version': REGISTRY_SCHEMA_VERSION,
        'entries': registry,
        'coverage': {
            'archives_loaded': loaded,
            'archives_available': len(all_sources),
            'archives_considered': len(sources),
            'errors': errors,
            'archive_run_ids': loaded_run_ids,
            'expected_archive_run_ids': expected_ids,
            'complete': loaded == len(all_sources),
        },
    }


def merge_archive_registry(existing, rebuilt):
    """Union old identities and their evidence without double-counting runs."""
    if not isinstance(rebuilt, dict) or not isinstance(rebuilt.get('entries'), dict):
        raise ValueError('A rebuilt archive registry is required')
    previous = existing.get('entries', {}) if isinstance(existing, dict) else {}
    if not isinstance(previous, dict):
        raise ValueError('Existing seen-vacancy registry entries are malformed')
    entries = dict(rebuilt['entries'])
    for key, old in previous.items():
        if not isinstance(key, str) or len(key) != 64 or any(ch not in '0123456789abcdef' for ch in key):
            raise ValueError('Existing seen-vacancy registry contains an invalid identity key')
        if not isinstance(old, dict):
            raise ValueError('Existing seen-vacancy registry contains a malformed entry')
        current = entries.get(key)
        if current is None:
            entries[key] = _record_observations(old, {})
            continue
        try:
            old_count = max(1, int(old.get('count', 1)))
            archive_count = max(1, int(current.get('count', 1)))
        except (TypeError, ValueError):
            raise ValueError('Existing seen-vacancy registry contains an invalid count')
        merged = {**old, **current, 'count': max(old_count, archive_count)}
        merged.update(_merge_observations(old, current))
        if old_count > archive_count:
            merged['first_run'] = old.get('first_run') or current.get('first_run')
            merged['last_run'] = old.get('last_run') or current.get('last_run')
        entries[key] = merged
    if len(entries) > MAX_KEYS:
        raise ValueError('Merged history identity registry reached its size limit')
    return {
        'schema_version': REGISTRY_SCHEMA_VERSION,
        'coverage': rebuilt.get('coverage', {}),
        'entries': entries,
    }


def mark_archive_published(registry, history_index, run_id, limit=40):
    """Mark the just-written archive covered, without concealing older gaps."""
    if not isinstance(registry, dict) or not isinstance(registry.get('entries'), dict):
        raise ValueError('A valid seen-vacancy registry is required')
    entry = next(
        (row for row in (history_index.get('runs') or [])
         if isinstance(row, dict) and str(row.get('run_id') or '') == str(run_id)
         and row.get('archive_file')),
        None,
    )
    if entry is None:
        raise ValueError('The current run has no published archive in the history index')
    coverage = dict(registry.get('coverage') or {})
    expected = expected_archive_run_ids(history_index, limit)
    expected_set = set(expected)
    ident = str(run_id)
    if ident not in expected_set:
        raise ValueError('The current run is outside the tracked archive window')
    previous_ids = set(coverage.get('archive_run_ids') or [])
    # Keep the cursor aligned with registry_from_archives' rolling window.
    # Otherwise the 41st archive leaves an extra ID and forces a full rebuild
    # on every subsequent scan.
    actual = [item for item in expected if item in previous_ids or item == ident]
    all_count = len(_archive_entries(history_index, limit=10**9))
    coverage.update({
        'archive_run_ids': actual,
        'expected_archive_run_ids': expected,
        'archives_loaded': len(actual),
        'archives_available': all_count,
        'archives_considered': len(expected),
    })
    complete = (
        set(actual) == expected_set
        and len(expected) == all_count
        and int(coverage.get('errors', 0) or 0) == 0
    )
    coverage['complete'] = complete
    return {
        'schema_version': REGISTRY_SCHEMA_VERSION,
        'coverage': coverage,
        'entries': registry['entries'],
    }


def annotate_newness(output, registry, run_id):
    if not isinstance(registry, dict) or not isinstance(registry.get('entries'), dict):
        raise ValueError('A valid prior-run registry is required')
    previous = registry['entries']
    new_entries = dict(previous)
    run = str(run_id)
    new_count = repeat_count = unknown_count = review_count = 0
    review_reason_counts = {}
    for job in output.get('jobs') or []:
        key = job_key(job) if isinstance(job, dict) else None
        if not key:
            job['novelty_status'] = 'unverified'
            unknown_count += 1
            continue
        old = previous.get(key)
        if old:
            reasons = _review_reasons(job, old)
            job['first_seen_run'] = old.get('first_run')
            job['previous_run_count'] = old.get('count', 0)
            if reasons:
                # The dashboard's new-only mode hides only 'previously_seen'.
                # A changed or missing identity attribute remains visible.
                job['novelty_status'] = 'review_required'
                job['novelty_review_reasons'] = reasons
                review_count += 1
                for reason in reasons:
                    review_reason_counts[reason] = review_reason_counts.get(reason, 0) + 1
            else:
                job['novelty_status'] = 'previously_seen'
                repeat_count += 1
            entry_base = new_entries.get(key, old)
            updated = _record_observations(entry_base, job)
            if updated.get('last_run') != run:
                updated['last_run'] = run
                updated['count'] = int(old.get('count', 0)) + 1
            new_entries[key] = updated
        else:
            job['novelty_status'] = 'new_to_history'
            new_count += 1
            entry_base = new_entries.get(key)
            new_entries[key] = (
                _record_observations(entry_base, job)
                if entry_base is not None else _new_entry(run, job)
            )
    if len(new_entries) > MAX_KEYS:
        raise ValueError('History identity registry reached its size limit; expand storage before continuing')
    coverage = registry.get('coverage', {})
    output['novelty_summary'] = {
        'new_to_history': new_count,
        'previously_seen': repeat_count,
        'review_required': review_count,
        'review_reason_counts': review_reason_counts,
        'unverified': unknown_count,
        'tracked_prior_jobs': len(previous),
        'archives_loaded_at_bootstrap': coverage.get('archives_loaded', 0),
        'archives_available_at_bootstrap': coverage.get('archives_available', 0),
        'history_complete_at_bootstrap': bool(coverage.get('complete', False)),
    }
    return {
        'schema_version': REGISTRY_SCHEMA_VERSION,
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'coverage': coverage,
        'entries': new_entries,
    }
