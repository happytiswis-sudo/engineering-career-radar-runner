"""Analyze every accessible published job run, with only aggregate public-job output.

Historical archives can be missing; report coverage instead of inventing a full history.
Private CV, secrets, individual CV skill matches and application notes are never printed.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import json
from career_intelligence import published_on
from novelty import job_key

def analyze(index,load):
    rows=index.get('runs') or []
    rows=[r for r in rows if isinstance(r,dict) and str(r.get('archive_file') or '').startswith('history/')]
    rows.sort(key=lambda r:str(r.get('published_at') or ''))
    per_source=defaultdict(Counter);per_track=defaultdict(Counter)
    per_run=[];seen_keys=set();missed=[];all_occurrences=0
    first_keys=defaultdict(set)
    for row in rows:
        run_id=str(row.get('run_id') or '')
        try:
            snapshot=load(row['archive_file'])
            if str(snapshot.get('run_id'))!=run_id or not isinstance(snapshot.get('jobs'),list):
                raise ValueError('Archive metadata or jobs invalid')
        except (ValueError,TypeError,KeyError,OSError) as exc:
            missed.append({'run_id':run_id,'cause':type(exc).__name__})
            continue
        try:now=datetime.fromisoformat(str(snapshot.get('generated_at') or row.get('published_at')).replace('Z','+00:00'))
        except ValueError:now=datetime.now(timezone.utc)
        if now.tzinfo is None:now=now.replace(tzinfo=timezone.utc)
        local=Counter();new_sources=Counter();new_tracks=Counter()
        source_lists=defaultdict(list)
        for j in snapshot['jobs']:
            if not isinstance(j,dict):continue
            all_occurrences+=1
            src=str(j.get('source') or 'Unknown')[:85]
            track=str(j.get('career_track') or 'Unspecified')[:100]
            date=published_on(j.get('published_at'),now=now)['age_days']
            dated=date is not None and date<=7
            late=date is None
            restricted=bool(j.get('remote') and j.get('remote_location_restriction'))
            score=float(j.get('score') or 0)
            key=job_key(j)
            is_new=bool(key and key not in seen_keys)
            source=per_source[src];industry=per_track[track]
            source['appearances']+=1;industry['appearances']+=1
            if dated:source['recent_7d_appearances']+=1;industry['recent_7d_appearances']+=1
            if late:source['undated_appearances']+=1
            if restricted:source['restricted_remote_appearances']+=1
            if score>=35:source['cv_score35_appearances']+=1
            if is_new:
                seen_keys.add(key);first_keys[src].add(key)
                source['first_seen_unique']+=1
                industry['first_seen_unique']+=1
                new_sources[src]+=1;new_tracks[track]+=1
                if dated:source['recent_7d_first_seen']+=1;industry['recent_7d_first_seen']+=1
                if restricted:source['restricted_remote_first_seen']+=1
                if score>=35 and dated and not restricted:
                    source['actionable_candidate_first_seen']+=1
                    industry['actionable_candidate_first_seen']+=1
            else:
                local['repeat_or_unidentifiable']+=1
            local['total']+=1
        per_run.append({'run_id':run_id,'jobs':local['total'],
          'repeats_or_unidentifiable':local['repeat_or_unidentifiable'],
          'new_unique':sum(new_sources.values()),
          'novelty_reported':(snapshot.get('novelty_summary') or {}).get('new_to_history'),
          'top_new_sources':dict(new_sources.most_common(7)),
          'top_new_tracks':dict(new_tracks.most_common(7)),
          'source_failures':snapshot.get('source_failure_counts') or {},
          'query_samples':len(snapshot.get('source_query_metrics') or [])})
    sort_key=lambda p:(-p[1].get('actionable_candidate_first_seen',0),-p[1].get('recent_7d_first_seen',0),-p[1].get('first_seen_unique',0))
    sources=sorted(per_source.items(),key=sort_key)
    tracks=sorted(per_track.items(),key=sort_key)
    return {'runs_available_in_index':len(rows),'runs_analyzed':len(per_run),
       'missing_archives':missed,'public_job_appearances':all_occurrences,
       'distinct_public_job_identities':len(seen_keys),
       'source_statistics':{k:dict(v) for k,v in sources},
       'track_statistics':{k:dict(v) for k,v in tracks},
       'run_comparisons':per_run,
       'caveat':'Job identity = normalized company/title/public URL; not verified active, eligible or recently opened. Actionable means only >=35 CV score, dated <=7d, no explicit remote-country restriction; employer qualification and immigration checks still apply.'}

def main():
    import os
    from huggingface_hub import hf_hub_download
    token=os.environ.get('HF_TOKEN');space=os.environ.get('HF_SPACE_ID')
    if not token or not space:raise SystemExit('Hugging Face private archive authentication missing')
    hub=lambda path:json.loads(Path(hf_hub_download(repo_id=space,filename=path,repo_type='space',token=token)).read_text(encoding='utf8'))
    index=hub('search-history.json')
    def load(path):
        if not path.startswith('history/') or not path.endswith('.json') or '..' in path:
            raise ValueError('Rejected unsafe archive name')
        try:return hub(path)
        except Exception as exc:raise OSError('Archived public result unavailable') from exc
    report=analyze(index,load)
    print('ALL-RUN PUBLIC DISCOVERY AUDIT START')
    print(json.dumps(report,ensure_ascii=False,separators=(',',':')))
    print('ALL-RUN PUBLIC DISCOVERY AUDIT END')

if __name__=='__main__':main()
