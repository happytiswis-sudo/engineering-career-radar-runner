"""Refresh persistent private-HF-Space history before uploading this GitHub scan.

Never invent an empty history index when Hub access fails. This keeps prior
searches safe from transient authentication/API failures.
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import EntryNotFoundError
from search_history import write_history, legacy_snapshot
from source_health import comparable_source_health
from novelty import (registry_from_archives,registry_needs_archive_rebuild,
                     merge_archive_registry,mark_archive_published,annotate_newness)
from source_novelty_summary import shortlist_novelty_by_source,classify_board_failures

def main():
    token=os.environ.get('HF_TOKEN','')
    space=os.environ.get('HF_SPACE_ID','')
    run=os.environ.get('GITHUB_RUN_ID','')
    event=os.environ.get('GITHUB_EVENT_NAME','workflow_dispatch')
    attempt=os.environ.get('GITHUB_RUN_ATTEMPT','1')
    if not token or not space:raise RuntimeError('Missing Hugging Face configuration needed to read the legacy registry')
    root=Path(__file__).resolve().parent/'public'
    latest=json.loads((root/'jobs.json').read_text(encoding='utf8'))
    try:
        remote=hf_hub_download(repo_id=space,filename='search-history.json',
                repo_type='space',token=token)
    except EntryNotFoundError:
        prior={'runs':[]}
        # Preserve the last visible results file as a one-time legacy archive;
        # older overwritten versions cannot be reconstructed.
        try:
            old_file=hf_hub_download(repo_id=space,filename='jobs.json',
                    repo_type='space',token=token)
        except EntryNotFoundError:
            pass
        else:
            old=json.loads(Path(old_file).read_text(encoding='utf8'))
            entry,archived=legacy_snapshot(old)
            archive=root/entry['archive_file']
            archive.parent.mkdir(parents=True,exist_ok=True)
            archive.write_text(json.dumps(archived,ensure_ascii=False,separators=(',',':')),encoding='utf8')
            prior={'runs':[entry]}
            print('Preserved the last pre-history published snapshot; earlier overwritten runs may not be available.')
    else:
        try:
            prior=json.loads(Path(remote).read_text(encoding='utf8'))
        except (OSError,ValueError,TypeError) as exc:
            print('History index unavailable ('+type(exc).__name__+'); preserving current output without rewriting registry.')
            return
    # Classify current listings against earlier *published* snapshots, not their
    # publication date. Reconcile the registry against the actual archive IDs
    # on every run; a pre-existing but incomplete seen-jobs.json is not trusted.
    def read_archive(name):
        if not re.fullmatch(r'history/(?:run-[0-9]{7,15}|legacy-[0-9]{14})\.json',name):
            raise ValueError('Invalid archived run path')
        try:
            old_path=hf_hub_download(repo_id=space,filename=name,
                                     repo_type='space',token=token)
            archive=json.loads(Path(old_path).read_text(encoding='utf8'))
            if not isinstance(archive,dict) or not isinstance(archive.get('jobs'),list):
                raise ValueError('Historical Hugging Face archive is malformed')
            return archive
        except EntryNotFoundError as exc:
            raise OSError('Historical archive unavailable in private Hugging Face Space') from exc

    try:
        seen_path=hf_hub_download(repo_id=space,filename='seen-jobs.json',
                                 repo_type='space',token=token)
    except EntryNotFoundError:
        existing_registry=None
    else:
        existing_registry=json.loads(Path(seen_path).read_text(encoding='utf8'))

    if registry_needs_archive_rebuild(existing_registry,prior,limit=40):
        archive_registry=registry_from_archives(prior,read_archive,limit=40)
        registry=merge_archive_registry(existing_registry,archive_registry)
        print('Reconciled seen-vacancy registry with '+str(registry['coverage']['archives_loaded'])+
              ' / '+str(registry['coverage']['archives_available'])+
              ' archived runs; coverage complete: '+str(registry['coverage']['complete'])+
              '; retained additional existing identities: '+
              str(len(registry['entries'])-len(archive_registry['entries'])))
    else:
        registry=existing_registry
        print('Seen-vacancy registry archive coverage already matches the published history index.')

    updated_registry=annotate_newness(latest,registry,run)
    latest['shortlist_novelty_by_source']=shortlist_novelty_by_source(latest.get('jobs') or [])
    latest['classified_failed_boards']=classify_board_failures(latest.get('source_failures'))
    for name,counts in latest['shortlist_novelty_by_source'].items():
        if counts['new_to_history']:
            print('New shortlist attribution: '+name+': '+
                  str(counts['new_to_history'])+' new-to-history; '+
                  str(counts['new_within_7d'])+' have source dates within 7d.')
    if latest['classified_failed_boards']:
        for failure in latest['classified_failed_boards']:
            if not str(failure.get('board','')).startswith('optional-'):
                print('Failed source diagnostic: '+str(failure.get('source',''))+
                      ' / '+str(failure.get('board',''))+' / '+
                      failure['category']+' / '+str(failure.get('error',''))[:120])
    (root/'jobs.json').write_text(json.dumps(latest,ensure_ascii=False,indent=2),encoding='utf8')
    print('New to tracked history: '+str(latest['novelty_summary']['new_to_history'])+
          '; seen before: '+str(latest['novelty_summary']['previously_seen'])+
          '; unverified: '+str(latest['novelty_summary']['unverified']))
    # Compare only after successfully reading the remote historical index.
    # A metrics lookup failure does NOT erase earlier scans or block publication.
    try:
        old_jobs_path=hf_hub_download(repo_id=space,filename='jobs.json',
                                     repo_type='space',token=token)
        previous_jobs=json.loads(Path(old_jobs_path).read_text(encoding='utf8'))
        if str(previous_jobs.get('run_id') or '')!=str(run):
            latest['source_health_comparison']=comparable_source_health(previous_jobs,latest)
            (root/'jobs.json').write_text(json.dumps(latest,ensure_ascii=False,indent=2),encoding='utf8')
            alarms=latest['source_health_comparison'].get('alerts') or []
            if alarms:print('Source coverage warning (same search profile): '+json.dumps(alarms,ensure_ascii=False))
    except EntryNotFoundError:
        pass
    except (OSError,ValueError,TypeError) as exc:
        print('Source comparison unavailable: '+type(exc).__name__)
    # A private-Space permissions or connectivity failure MUST abort publishing
    # rather than destroy existing search history.
    entry,index=write_history(latest,run,event,attempt,prior,root)
    # Only now, after the archive and index exist locally, mark this run as
    # covered. A failed archive write must never advance the registry cursor.
    updated_registry=mark_archive_published(updated_registry,index,run,limit=40)
    (root/'seen-jobs.json').write_text(
        json.dumps(updated_registry,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    print(f"Archived scan {entry['run_id']} with {entry['job_count']} matched jobs; "
          f"{len(index['runs'])} published-run summaries retained.")
    print('Seen registry archive coverage: '+str(updated_registry['coverage']['archives_loaded'])+
          ' / '+str(updated_registry['coverage']['archives_available'])+
          '; complete: '+str(updated_registry['coverage']['complete']))

if __name__=='__main__':
    main()
