import unittest
from datetime import datetime,timezone
from investigate_new_jobs import summarize

class ArchivedNoveltyAnalysisTests(unittest.TestCase):
 def setUp(self):
  self.a={'run_id':'40519766917','generated_at':'2026-10-27T14:33:08+00:00',
          'novelty_summary':{'new_to_history':2},
          'source_metrics':{'bundesagentur':{'boards':25,'returned':100}},
          'jobs':[{'title':'Ramp Operations Coordinator','company':'Airport One','location':'Frankfurt',
                   'source':'Bundesagentur','url':'https://jobs.example/a',
                   'published_at':'2026-10-27T10:00:00Z','score':83,
                   'novelty_status':'new_to_history','career_track':'Airport Ground Ops',
                   'immigration_opportunity':{'tier':'unconfirmed_germany'}},
                  {'title':'Packaging Technician','company':'Factory Two','location':'Cologne',
                   'source':'Greenhouse','url':'https://jobs.example/b',
                   'published_at':'2026-10-15','score':72,
                   'novelty_status':'new_to_history'},
                  {'title':'Older role','company':'Airport One','source':'Bundesagentur',
                   'novelty_status':'previously_seen'}]}
 def test_new_sources_recency_and_comparison(self):
  result=summarize(self.a,'40519766917')
  self.assertEqual(result['total_jobs'],3)
  self.assertEqual(result['new_jobs'],2)
  self.assertEqual(result['sources_new'],{'Bundesagentur':1,'Greenhouse':1})
  self.assertEqual(result['sources_all'],{'Bundesagentur':2,'Greenhouse':1})
  self.assertEqual(result['date_buckets_new'],{'24h':1,'30d':1})
  self.assertEqual(result['industry_family_new'],{'Airport, ground or cargo':1,'Other industries':1})
  self.assertEqual(result['new_listings'][0]['date_age_bucket'],'24h')
 def test_wrong_run_refused(self):
  with self.assertRaises(ValueError):summarize(self.a,'12345678900')
 def test_no_implicit_unknown_as_recent(self):
  self.a['jobs'][0]['published_at']=''
  result=summarize(self.a,'40519766917')
  self.assertEqual(result['date_buckets_new'].get('unknown'),1)
 def test_mismatched_novelty_count_refused(self):
  self.a['novelty_summary']['new_to_history']=20
  with self.assertRaises(ValueError):summarize(self.a,'40519766917')

if __name__=='__main__':unittest.main()
