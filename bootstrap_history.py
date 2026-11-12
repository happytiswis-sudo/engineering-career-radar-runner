"""Backfill the currently published private Hugging Face job list immediately.

Runs during interface deployment, WITHOUT launching another job scan. Creates
the first searchable history record if this published snapshot is not yet in
search-history.json. Existing history is preserved.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd
from huggingface_hub.errors import EntryNotFoundError
from search_history import create_snapshot, legacy_snapshot, merge_index


def load_private_json(space, filename, token):
    try:
        path=hf_hub_download(repo_id=space,filename=filename,repo_type='space',
                             token=token,force_download=True)
    except EntryNotFoundError:
        return None
    return json.loads(Path(path).read_text(encoding='utf-8'))


def prepare_backfill(current, index):
    if not isinstance(current,dict) or not isinstance(current.get('jobs'),list):
        raise ValueError('Published results are missing or malformed')
    if not current.get('generated_at'):
        raise ValueError('Refusing to archive results without a publication timestamp')
    actual_id=str(current.get('run_id') or '')
    if actual_id.isdigit() and 7<=len(actual_id)<=15:
        entry,snapshot=create_snapshot(current,actual_id,
               'workflow_dispatch' if current.get('search_mode')=='on-demand' else 'schedule',
               str(current.get('run_attempt') or '1'))
    else:
        entry,snapshot=legacy_snapshot(current)
    rows=index.get('runs') or []
    if any(str(x.get('run_id'))==entry['run_id'] and
           x.get('published_at')==entry['published_at'] for x in rows if isinstance(x,dict)):
        return None
    return entry,snapshot,merge_index(index,entry)


def main():
    space=os.environ['HF_SPACE_ID']
    token=os.environ['HF_TOKEN']
    api=HfApi(token=token)
    published=load_private_json(space,'jobs.json',token)
    if published is None:
        print('No existing Space jobs.json; skipping history backfill.')
        return
    history=load_private_json(space,'search-history.json',token)
    prepared=prepare_backfill(published,history or {'runs':[]})
    if prepared is None:
        print('Current published jobs already indexed; no history backfill needed.')
        return
    entry,snapshot,index=prepared
    content=json.dumps(snapshot,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    index_bytes=json.dumps(index,ensure_ascii=False,indent=2).encode('utf-8')
    # Keep index and source snapshot together in ONE commit. The latest jobs
    # remain untouched, and existing archive files are not deleted.
    ops=[
        CommitOperationAdd(path_in_repo=entry['archive_file'],path_or_fileobj=content),
        CommitOperationAdd(path_in_repo='search-history.json',path_or_fileobj=index_bytes)
    ]
    api.create_commit(repo_id=space,repo_type='space',operations=ops,
                      commit_message='Archive currently published Career Radar vacancies',
                      token=token)
    print(f"Archived existing published search {entry['run_id']}: "+
          f"{entry['job_count']} vacancies. This is a historic snapshot, not a new scan.")


if __name__=='__main__':
    main()
