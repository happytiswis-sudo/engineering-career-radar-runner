import unittest
from novelty import (canonical_url,job_key,registry_from_archives,annotate_newness,
                     registry_needs_archive_rebuild,merge_archive_registry,
                     mark_archive_published)
from deep_search import validate_request,dynamic_boards,ROLE_GROUPS
from pathlib import Path
import json

class NoveltyAndAirportCoverageTests(unittest.TestCase):
 def test_tracking_does_not_create_false_new_job(self):
  a={'title':'Airport Operations Coordinator','company':'Airport A','url':'http://www.jobs.example/123/?utm_source=abc&ref=feed'}
  b={**a,'url':'https://jobs.example/123?utm_medium=mail'}
  self.assertEqual(job_key(a),job_key(b))
  self.assertNotEqual(job_key(a),job_key({**a,'title':'Airport Operations Technician'}))
  self.assertNotEqual(job_key(a),job_key({**a,'url':'https://jobs.example/124'}))
 def test_prior_history_and_repeat_classification(self):
  prior={'runs':[{'run_id':'12345678901','published_at':'2026-10-25T09:00:00Z',
                  'archive_file':'history/run-12345678901.json'}]}
  j={'title':'Airport Operations Coordinator','company':'Airport A','url':'https://jobs.example/123'}
  registry=registry_from_archives(prior,lambda p:{'run_id':'12345678901','jobs':[j]})
  self.assertTrue(registry['coverage']['complete'])
  output={'jobs':[dict(j),{'title':'Cargo Planner','company':'Airport A','url':'https://jobs.example/125'},
                  {'title':'Missing URL','company':'Airport A'}]}
  updated=annotate_newness(output,registry,'12345678902')
  self.assertEqual([j['novelty_status'] for j in output['jobs']],
                   ['previously_seen','new_to_history','unverified'])
  self.assertEqual(output['novelty_summary']['previously_seen'],1)
  self.assertEqual(output['novelty_summary']['new_to_history'],1)
  self.assertEqual(updated['entries'][job_key(j)]['count'],2)
  next_run={'jobs':[dict(j)]}
  annotate_newness(next_run,updated,'12345678903')
  self.assertEqual(next_run['jobs'][0]['previous_run_count'],2)
 def test_partial_history_is_reported_not_claimed_complete(self):
  runs=[{'run_id':str(12345678900+i),'archive_file':f'history/run-{12345678900+i}.json'} for i in range(5)]
  doc=registry_from_archives({'runs':runs},lambda path:{'run_id':path[12:-5],'jobs':[]},limit=2)
  self.assertFalse(doc['coverage']['complete'])
  self.assertEqual(doc['coverage']['archives_loaded'],2)
 def test_airport_and_related_sectors_are_searchable(self):
  role_data=json.loads(Path('role_catalog.json').read_text(encoding='utf-8'))
  old_names=[r['title'].casefold() for r in role_data['roles']]
  self.assertEqual(len(old_names),len(set(old_names)))
  self.assertGreaterEqual(len(old_names),780)
  self.assertGreaterEqual(len(set(r['track'] for r in role_data['roles'])),34)
  self.assertIn('airport_ops',ROLE_GROUPS)
  self.assertIn('air_cargo',ROLE_GROUPS)
  p=validate_request({'region':'world','roles':['airport_ops'],'depth':'focused'})
  queries=[b['query'] for b in dynamic_boards(p)]
  self.assertIn('Flughafen',queries)
  self.assertTrue(any('Bodenabfertigung' in q or 'Vorfeld' in q for q in queries))
 def test_new_runs_same_session_count_once(self):
  j={'title':'Airport Technician','company':'Airport A','url':'https://jobs.example/9'}
  reg={'entries':{},'coverage':{'complete':True}}
  next_=annotate_newness({'jobs':[dict(j)]},reg,12345678901)
  again=annotate_newness({'jobs':[dict(j)]},next_,12345678901)
  self.assertEqual(again['entries'][job_key(j)]['count'],1)

 def test_cross_run_suppression_design_preserves_default_visible_results(self):
  source=Path('radar.py').read_text(encoding='utf-8')
  self.assertNotIn("CAREER_RADAR_SUPPRESS_PREVIOUSLY_SEEN",source)
  self.assertIn("'mode': 'observe_only'",source)
  self.assertIn("'active': False",source)
  self.assertIn("'candidates_matching_registry'",source)
  self.assertIn("suppression_audit['suppressed']=0",source)
  self.assertIn("unverified_kept",source)
  # Cross-run identity is SHA-256 URL+employer+title, not title alone.
  a={'title':'Field Service Engineer','company':'Agilent','url':'https://jobs.example/req/1'}
  b={'title':'Field Service Engineer','company':'Agilent','url':'https://jobs.example/req/2'}
  c={'title':'Field Service Engineer','company':'Another employer','url':'https://jobs.example/req/1'}
  self.assertNotEqual(job_key(a),job_key(b))
  self.assertNotEqual(job_key(a),job_key(c))
  self.assertEqual(job_key(a),job_key({**a,'url':'http://www.jobs.example/req/1?utm_source=mail'}))
  dashboard=(Path('public/ui-v2.js').read_text(encoding='utf-8'))
  history=(Path('search_history.py').read_text(encoding='utf-8'))
  self.assertIn("job?.novelty_status!=='previously_seen'",dashboard)
  self.assertIn("j.novelty_status==='review_required'",dashboard)
  self.assertIn("'multiple_historical_locations'",Path('novelty.py').read_text(encoding='utf-8'))
  self.assertIn("'novelty_review_reasons'",history)

 def test_stale_existing_registry_is_rebuilt_from_newly_indexed_archives(self):
  first={'run_id':'12345678901','archive_file':'history/run-12345678901.json','published_at':'2026-10-01'}
  second={'run_id':'12345678902','archive_file':'history/run-12345678902.json','published_at':'2026-10-02'}
  prior={'runs':[first,second]}
  repeated={'title':'Field Service Engineer','company':'Example GmbH','url':'https://jobs.example/req/1'}
  newer={'title':'Maintenance Engineer','company':'Example GmbH','url':'https://jobs.example/req/2'}
  docs={
   first['archive_file']:{'run_id':first['run_id'],'jobs':[repeated]},
   second['archive_file']:{'run_id':second['run_id'],'jobs':[dict(repeated),newer]}
  }
  extra='a'*64
  old={'schema_version':1,'entries':{extra:{'first_run':'12345678888','last_run':'12345678888','count':1}},
       'coverage':{'archives_loaded':0,'archives_available':0,'complete':True}}
  self.assertTrue(registry_needs_archive_rebuild(old,prior))
  rebuilt=registry_from_archives(prior,lambda name:docs[name])
  merged=merge_archive_registry(old,rebuilt)
  self.assertEqual(merged['coverage']['archive_run_ids'],
                   ['12345678901','12345678902'])
  self.assertEqual(merged['coverage']['archives_loaded'],2)
  self.assertEqual(merged['coverage']['archives_available'],2)
  self.assertTrue(merged['coverage']['complete'])
  self.assertIn(extra,merged['entries'])
  self.assertEqual(merged['entries'][job_key(repeated)]['count'],2)
  self.assertFalse(registry_needs_archive_rebuild(merged,prior))

 def test_archive_rebuild_retries_when_an_archive_is_missing(self):
  runs=[{'run_id':'12345678901','archive_file':'history/run-12345678901.json','published_at':'2026-10-01'},
        {'run_id':'12345678902','archive_file':'history/run-12345678902.json','published_at':'2026-10-02'}]
  prior={'runs':runs}
  doc={'run_id':runs[0]['run_id'],'jobs':[]}
  def reader(name):
   if name==runs[1]['archive_file']:
    raise OSError('archive unavailable')
   return doc
  rebuilt=registry_from_archives(prior,reader)
  self.assertEqual(rebuilt['coverage']['archive_run_ids'],['12345678901'])
  self.assertEqual(rebuilt['coverage']['expected_archive_run_ids'],
                   ['12345678901','12345678902'])
  self.assertFalse(rebuilt['coverage']['complete'])
  self.assertTrue(registry_needs_archive_rebuild(rebuilt,prior))

 def test_archive_merge_uses_max_seen_count_without_double_counting(self):
  job={'title':'Quality Engineer','company':'Example','url':'https://jobs.example/quality'}
  prior={'runs':[{'run_id':'12345678901','archive_file':'history/run-12345678901.json',
                  'published_at':'2026-10-01'}]}
  rebuilt=registry_from_archives(prior,lambda name:{'run_id':'12345678901','jobs':[job]})
  key=job_key(job)
  existing={'entries':{key:{'first_run':'12345678888','last_run':'12345678901','count':4}},
            'coverage':{'archive_run_ids':[]}}
  merged=merge_archive_registry(existing,rebuilt)
  self.assertEqual(merged['entries'][key]['count'],4)
  self.assertEqual(merged['entries'][key]['first_run'],'12345678888')

 def test_reconciliation_job_only_targets_private_seen_registry(self):
  root=Path(__file__).resolve().parents[1]
  script=(root/'reconcile_seen_registry.py').read_text(encoding='utf-8')
  workflow=(root/'.github'/'workflows'/'reconcile-seen-registry.yml').read_text(encoding='utf-8')
  self.assertIn("path_in_repo=\"seen-jobs.json\"",script)
  self.assertIn("force_download=True",script)
  self.assertIn('if not coverage.get("complete")',script)
  self.assertIn("search-history.json",script)
  self.assertIn("workflow_dispatch:",workflow)
  self.assertIn(".github/reconcile-requests/**",workflow)
  self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY",script)

 def test_current_run_coverage_advances_only_after_archive_is_indexed(self):
  first={'run_id':'12345678901','archive_file':'history/run-12345678901.json','published_at':'2026-10-01'}
  second={'run_id':'12345678902','archive_file':'history/run-12345678902.json','published_at':'2026-10-02'}
  prior={'runs':[first]}
  registry=registry_from_archives(
   prior,lambda name:{'run_id':'12345678901','jobs':[]})
  self.assertFalse(registry_needs_archive_rebuild(registry,prior))
  published={'runs':[second,first]}
  marked=mark_archive_published(registry,published,'12345678902')
  self.assertEqual(marked['coverage']['archive_run_ids'],
                   ['12345678901','12345678902'])
  self.assertEqual(marked['coverage']['expected_archive_run_ids'],
                   ['12345678901','12345678902'])
  self.assertTrue(marked['coverage']['complete'])
  self.assertFalse(registry_needs_archive_rebuild(marked,published))

 def test_registry_records_location_date_and_requisition_evidence(self):
  first={'title':'Project Engineer','company':'Example GmbH',
         'url':'https://jobs.example/req/1','location':'Stuttgart, Germany',
         'published_at':'2026-10-30T00:00:00+00:00','source':'Example ATS',
         'employer_posting_id':'REQ-1'}
  second={**first,'location':'Stuttgart, Germany'}
  prior={'runs':[
   {'run_id':'12345678901','archive_file':'history/run-12345678901.json','published_at':'2026-10-30'},
   {'run_id':'12345678902','archive_file':'history/run-12345678902.json','published_at':'2026-10-31'}]}
  docs={
   prior['runs'][0]['archive_file']:{'run_id':'12345678901','jobs':[first]},
   prior['runs'][1]['archive_file']:{'run_id':'12345678902','jobs':[second]}
  }
  registry=registry_from_archives(prior,lambda name:docs[name])
  entry=registry['entries'][job_key(first)]
  self.assertEqual(entry['locations'],['stuttgart, germany'])
  self.assertEqual(entry['posting_dates'],['2026-10-30'])
  self.assertEqual(entry['posting_ids'],['REQ-1'])
  self.assertEqual(entry['count'],2)
  self.assertEqual(registry['schema_version'],2)

 def test_location_changed_exact_key_is_review_required_and_never_hidden_as_stable_repeat(self):
  old={'title':'Project Engineer','company':'Example GmbH',
       'url':'https://jobs.example/req/1','location':'Stuttgart, Germany',
       'published_at':'2026-10-30','source':'Example ATS'}
  prior={'runs':[{'run_id':'12345678901','archive_file':'history/run-12345678901.json',
                  'published_at':'2026-10-30'}]}
  registry=registry_from_archives(
   prior,lambda name:{'run_id':'12345678901','jobs':[old]})
  changed={**old,'location':'Darmstadt, Germany'}
  output={'jobs':[changed]}
  updated=annotate_newness(output,registry,'12345678902')
  self.assertEqual(changed['novelty_status'],'review_required')
  self.assertIn('location_changed',changed['novelty_review_reasons'])
  self.assertEqual(output['novelty_summary']['review_required'],1)
  self.assertIn('darmstadt, germany',updated['entries'][job_key(old)]['locations'])
  # A key with more than one historical location remains visible for review,
  # even after both locations have been observed on separate runs.
  next_job={**old,'location':'Darmstadt, Germany'}
  next_output={'jobs':[next_job]}
  annotate_newness(next_output,updated,'12345678903')
  self.assertEqual(next_job['novelty_status'],'review_required')
  self.assertIn('multiple_historical_locations',next_job['novelty_review_reasons'])

 def test_changed_posting_date_or_non_personio_requisition_id_stays_visible(self):
  old={'title':'Quality Engineer','company':'Example GmbH',
       'url':'https://jobs.example/quality/1','location':'Stuttgart',
       'published_at':'2026-10-20','source':'Example ATS',
       'employer_posting_id':'REQ-1'}
  prior={'runs':[{'run_id':'12345678901','archive_file':'history/run-12345678901.json',
                  'published_at':'2026-10-20'}]}
  registry=registry_from_archives(
   prior,lambda name:{'run_id':'12345678901','jobs':[old]})
  changed_date={**old,'published_at':'2026-11-02'}
  changed_id={**old,'employer_posting_id':'REQ-2'}
  output={'jobs':[changed_date,changed_id]}
  annotate_newness(output,registry,'12345678902')
  self.assertEqual(changed_date['novelty_status'],'review_required')
  self.assertIn('posting_date_changed',changed_date['novelty_review_reasons'])
  self.assertEqual(changed_id['novelty_status'],'review_required')
  self.assertIn('requisition_id_changed',changed_id['novelty_review_reasons'])

 def test_review_required_is_separate_in_source_novelty_summary(self):
  from source_novelty_summary import shortlist_novelty_by_source
  rows=shortlist_novelty_by_source([
   {'source':'ATS A','novelty_status':'previously_seen'},
   {'source':'ATS A','novelty_status':'review_required'},
   {'source':'ATS A','novelty_status':'new_to_history'},
   {'source':'ATS A','novelty_status':'unverified'},
  ])
  self.assertEqual(rows['ATS A']['previously_seen'],1)
  self.assertEqual(rows['ATS A']['review_required'],1)
  self.assertEqual(rows['ATS A']['new_to_history'],1)
  self.assertEqual(rows['ATS A']['unverified_identity'],1)

 def test_same_run_observation_union_does_not_count_as_another_run(self):
  job={'title':'Project Engineer','company':'Example GmbH',
       'url':'https://jobs.example/req/2','location':'Stuttgart'}
  second={**job,'location':'Darmstadt'}
  registry=annotate_newness({'jobs':[job,second]}, {'schema_version':2,'entries':{},
       'coverage':{'complete':True}}, '12345678901')
  entry=registry['entries'][job_key(job)]
  self.assertEqual(entry['count'],1)
  self.assertEqual(entry['locations'],['darmstadt','stuttgart'])

 def test_schema_v1_registry_rebuilds_even_when_archive_ids_match(self):
  prior={'runs':[{'run_id':'12345678901','archive_file':'history/run-12345678901.json',
                  'published_at':'2026-10-30'}]}
  old={'schema_version':1,'entries':{},
       'coverage':{'archive_run_ids':['12345678901']}}
  self.assertTrue(registry_needs_archive_rebuild(old,prior))

 def test_rolling_archive_window_stays_stable_after_run_41(self):
  runs=[{'run_id':str(12345678901+i),
         'archive_file':f'history/run-{12345678901+i}.json',
         'published_at':f'2026-10-01T00:{i:02d}:00Z'} for i in range(41)]
  first_window={'runs':runs[:40]}
  registry=registry_from_archives(
   first_window,
   lambda path:{'run_id':path.split('run-')[1][:-5],'jobs':[]},
   limit=40)
  self.assertEqual(len(registry['coverage']['archive_run_ids']),40)
  updated_index={'runs':runs}
  marked=mark_archive_published(
   registry,updated_index,runs[-1]['run_id'],limit=40)
  self.assertEqual(marked['coverage']['archive_run_ids'],
                   marked['coverage']['expected_archive_run_ids'])
  self.assertEqual(len(marked['coverage']['archive_run_ids']),40)
  self.assertFalse(marked['coverage']['complete'])
  self.assertFalse(registry_needs_archive_rebuild(marked,updated_index,limit=40))

 def test_non_object_archive_is_rejected_without_claiming_coverage(self):
  prior={'runs':[{'run_id':'12345678901','archive_file':'history/run-12345678901.json'}]}
  rebuilt=registry_from_archives(prior,lambda name:[])
  self.assertEqual(rebuilt['coverage']['archives_loaded'],0)
  self.assertEqual(rebuilt['coverage']['errors'],1)
  self.assertFalse(rebuilt['coverage']['complete'])

 def test_malformed_registry_schema_version_forces_rebuild_safely(self):
  prior={'runs':[{'run_id':'12345678901','archive_file':'history/run-12345678901.json'}]}
  old={'schema_version':'v2','entries':{},
       'coverage':{'archive_run_ids':['12345678901']}}
  self.assertTrue(registry_needs_archive_rebuild(old,prior))

if __name__=='__main__':unittest.main()
