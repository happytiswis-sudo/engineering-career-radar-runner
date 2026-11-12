import json
import tempfile
import unittest
from pathlib import Path
from search_history import create_snapshot, merge_index,write_history, legacy_snapshot

class PersistentSearchHistoryTests(unittest.TestCase):
 def sample(self):
  return {
   'generated_at':'2026-10-26T08:00:00+00:00',
   'search_mode':'on-demand',
   'search_request':{'region':'west','cities':['Stuttgart'],'roles':[],'sources':['ba','ats']},
   'total_collected':1700,'ai_evaluated':12,'hard_excluded_count':4,
   'source_metrics':{'ats':{'succeeded':3}},
   'linkedin_query_state':{'cursor':32,'total_query_terms':886,'status':'batch_complete'},
   'jobs':[{'title':'Manufacturing Engineer','company':'Example GmbH',
      'url':'https://company.example/jobs/1','score':82,
      'description':'Manufacturing '+('x'*4000),'matched_skills':['CAD'],
      'agent_review':{'specialists_executed':36,'key_findings':[]},
      'private_note':'must not be published'}]
  }
 def test_archive_has_run_id_and_all_job_results(self):
  summary,snapshot=create_snapshot(self.sample(),'40243304499')
  self.assertEqual(summary['job_count'],1)
  self.assertEqual(summary['archive_file'],'history/run-40243304499.json')
  self.assertEqual(snapshot['run_id'],'40243304499')
  self.assertEqual(snapshot['search_request']['cities'],['Stuttgart'])
  self.assertEqual(snapshot['jobs'][0]['score'],82)
  self.assertNotIn('private_note',snapshot['jobs'][0])
  self.assertLessEqual(len(snapshot['jobs'][0]['description']),2400)
 def test_history_preserves_failure_inventory_and_final_source_novelty(self):
  data=self.sample()
  data['classified_failed_boards']=[{'source':'greenhouse','board':'factory',
         'category':'board_not_found','error':'HTTP 404'}]
  data['shortlist_novelty_by_source']={'Greenhouse':{
      'shortlisted':1,'new_to_history':1,'new_within_7d':1}}
  data['runtime_metrics']={'scanner_seconds':185}
  _,archive=create_snapshot(data,'40243304501')
  self.assertEqual(archive['classified_failed_boards'][0]['board'],'factory')
  self.assertEqual(archive['shortlist_novelty_by_source']['Greenhouse']['new_to_history'],1)
  self.assertEqual(archive['runtime_metrics']['scanner_seconds'],185)
  self.assertEqual(archive['linkedin_query_state']['cursor'],32)

 def test_previous_published_list_can_be_saved_as_legacy(self):
  summary,snapshot=legacy_snapshot(self.sample())
  self.assertTrue(summary['run_id'].startswith('legacy-'))
  self.assertTrue(summary['archive_file'].startswith('history/legacy-'))
  self.assertEqual(snapshot['jobs'][0]['title'],'Manufacturing Engineer')
  self.assertNotIn('run_url',summary)
 def test_index_preserves_all_distinct_runs(self):
  s1,_=create_snapshot(self.sample(),'40243304499')
  s2,_=create_snapshot(self.sample(),'40243304500')
  older=merge_index({'runs':[]},s1)
  newer=merge_index(older,s2)
  self.assertEqual(len(newer['runs']),2)
  again=merge_index(newer,s2)
  self.assertEqual(len(again['runs']),2)
 def test_not_accept_arbitrary_archive_id(self):
  with self.assertRaises(ValueError):create_snapshot(self.sample(),'../password')
 def test_roundtrip(self):
  with tempfile.TemporaryDirectory() as temp:
   entry,index=write_history(self.sample(),'40243304499','workflow_dispatch','1',{'runs':[]},temp)
   self.assertTrue(Path(temp,entry['archive_file']).exists())
   self.assertEqual(json.loads(Path(temp,'search-history.json').read_text())['runs'][0]['run_id'],'40243304499')
 def test_dashboard_controls_and_archive(self):
  html=(Path(__file__).resolve().parents[1]/'public/index.html').read_text()
  js=(Path(__file__).resolve().parents[1]/'public/frontend-v3.js').read_text()
  worker=(Path(__file__).resolve().parents[1]/'cloudflare/search-worker.js').read_text()
  self.assertIn('data-route="history"',html)
  self.assertIn("api('/supabase-history?limit=100')",js)
  self.assertIn("api('/runs?limit=60')",js)
  self.assertIn("function drawHist()",js)
  self.assertIn("url.pathname==='/supabase-history'",worker)
  self.assertIn("url.pathname==='/runs'",worker)
if __name__=='__main__':unittest.main()
