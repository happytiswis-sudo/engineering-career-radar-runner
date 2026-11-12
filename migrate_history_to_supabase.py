#!/usr/bin/env python3
"""One-time idempotent import of retained Hugging Face search archives into Supabase."""
from __future__ import annotations
import json, os, time, urllib.request, urllib.error
from pathlib import Path
from huggingface_hub import hf_hub_download

def rpc(base,key,run_id,jobs):
    endpoint=base.rstrip('/')+'/rest/v1/rpc/career_radar_upsert_scan_jobs'
    total=0
    for offset in range(0,len(jobs),100):
        payload=json.dumps({'p_run_id':run_id,'p_jobs':jobs[offset:offset+100]},ensure_ascii=False).encode()
        req=urllib.request.Request(endpoint,data=payload,method='POST',headers={
          'apikey':key,'Authorization':'Bearer '+key,'Content-Type':'application/json','Accept':'application/json'})
        count=None
        # PostgREST may briefly fail while its schema cache is refreshing. Retry only
        # the transient cache-load 503; fail fast on auth, SQL, or payload errors.
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req,timeout=40) as response:
                    count=json.loads(response.read().decode())
                break
            except urllib.error.HTTPError as exc:
                body=exc.read(1200).decode(errors='replace')
                cache_error=exc.code==503 and ('PGRST002' in body or 'schema cache' in body.lower())
                if not cache_error or attempt==5:
                    raise RuntimeError('Supabase RPC failed HTTP '+str(exc.code)+': '+body) from exc
                delay=min(5*(2**attempt),30)
                print('Supabase PostgREST schema cache unavailable (PGRST002); retry '+str(attempt+1)+'/5 in '+str(delay)+'s')
                time.sleep(delay)
        if not isinstance(count,int):raise RuntimeError('Unexpected Supabase batch return: '+repr(count))
        total+=count
    return total

def finalize(base,key,entry,snapshot,jobs):
    run_id=str(entry.get('run_id') or '')
    endpoint=base.rstrip('/')+'/rest/v1/rpc/career_radar_finalize_scan_run'
    west=sum(1 for job in jobs if isinstance(job,dict) and
             isinstance(job.get('market'),dict) and job['market'].get('west') is True)
    payload=json.dumps({
        'p_run_id':run_id,
        'p_collected_jobs':int(entry.get('collected_count',snapshot.get('total_collected',len(jobs))) or 0),
        'p_shortlisted_jobs':int(entry.get('job_count',len(jobs)) or 0),
        'p_western_germany_matches':west,
        'p_completed_at':entry.get('published_at') or snapshot.get('generated_at'),
        'p_history_metadata':{
            'event':entry.get('event') or 'workflow_dispatch',
            'attempt':int(entry.get('attempt',1) or 1),
            'status':entry.get('status') or 'completed',
            'conclusion':entry.get('conclusion') or 'success',
            'published':bool(entry.get('published',True)),
            'published_at':entry.get('published_at') or snapshot.get('generated_at'),
            'created_at':entry.get('created_at') or entry.get('published_at') or snapshot.get('generated_at'),
            'run_url':entry.get('run_url') or '',
            'profile':entry.get('profile') if isinstance(entry.get('profile'),dict) else {},
            'search_mode':entry.get('search_mode') or snapshot.get('search_mode'),
            'job_count':int(entry.get('job_count',len(jobs)) or 0),
            'collected_count':int(entry.get('collected_count',snapshot.get('total_collected',len(jobs))) or 0),
            'ai_count':int(entry.get('ai_count',snapshot.get('ai_evaluated',0)) or 0),
            'hard_excluded':int(entry.get('hard_excluded',snapshot.get('hard_excluded_count',0)) or 0),
            'archive_file':entry.get('archive_file') or 'history/run-'+run_id+'.json'
        }
    }).encode('utf-8')
    request=urllib.request.Request(endpoint,data=payload,method='POST',headers={
        'apikey':key,'Authorization':'Bearer '+key,'Content-Type':'application/json',
        'Accept':'application/json','User-Agent':'CareerRadar-HistoryMigration/1.0'})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request,timeout=40) as response:
                result=json.loads(response.read().decode('utf-8'))
            if result is not True:
                raise RuntimeError('Supabase did not finalize scan metadata for '+run_id)
            return
        except urllib.error.HTTPError as exc:
            body=exc.read(1200).decode(errors='replace')
            cache_error=exc.code==503 and ('PGRST002' in body or 'schema cache' in body.lower())
            if not cache_error or attempt==5:
                raise RuntimeError('Supabase metadata finalization failed HTTP '+str(exc.code)+': '+body) from exc
            delay=min(5*(2**attempt),30)
            print('Supabase metadata finalization schema cache unavailable; retry '+str(attempt+1)+'/5 in '+str(delay)+'s')
            time.sleep(delay)

def main():
    base=os.environ.get('SUPABASE_URL','').strip()
    key=os.environ.get('SUPABASE_SERVICE_ROLE_KEY','').strip()
    space=os.environ.get('HF_SPACE_ID','').strip()
    token=os.environ.get('HF_TOKEN','').strip()
    if not all([base,key,space,token]):raise RuntimeError('Set SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, HF_SPACE_ID and HF_TOKEN')
    index_path=hf_hub_download(repo_id=space,filename='search-history.json',repo_type='space',token=token)
    index=json.loads(Path(index_path).read_text(encoding='utf8'))
    entries=index.get('runs') or []
    imported=0;skipped=0;count=0
    for entry in entries:
        run_id=str(entry.get('run_id') or '')
        archive=str(entry.get('archive_file') or '')
        if not run_id.isdigit() or not (7<=len(run_id)<=15) or archive!='history/run-'+run_id+'.json':
            skipped+=1;continue
        path=hf_hub_download(repo_id=space,filename=archive,repo_type='space',token=token)
        snapshot=json.loads(Path(path).read_text(encoding='utf8'))
        jobs=snapshot.get('jobs')
        if str(snapshot.get('run_id') or '')!=run_id or not isinstance(jobs,list):
            raise RuntimeError('Invalid historical snapshot for run '+run_id)
        n=rpc(base,key,run_id,jobs)
        if n!=len(jobs):raise RuntimeError('Imported count mismatch for run '+run_id)
        if jobs:finalize(base,key,entry,snapshot,jobs)
        imported+=1;count+=n
        print('Imported archive '+run_id+': '+str(n)+' jobs')
    print('Migration finished. Archives imported='+str(imported)+', jobs='+str(count)+', legacy/non-numeric skipped='+str(skipped))
if __name__=='__main__':main()
