import unittest
import json
from unittest.mock import patch
from public_source_adapters import nomado24,themuse,workday
from radar import merge_duplicate_evidence,parse_structured_assessment
from deep_search import validate_request

class FreeSourceUpgradeTests(unittest.TestCase):
 def test_nomado_cursor_continues_after_empty_page(self):
  result=[
   {'data':[{'title':'Test Engineer','companyName':'Factory GmbH','url':'https://www.nomado24.de/en/remote-jobs/job/test-one',
             'location':'Remote (Germany)','workArrangement':'remote','publishedAt':'2026-10-25'}],
    'hasNext':True,'nextCursor':'next'},
   {'data':[],'hasNext':True,'nextCursor':'last'},
   {'data':[{'title':'Quality Inspector','companyName':'Factory GmbH','url':'https://www.nomado24.de/en/remote-jobs/job/test-two',
             'location':'Hybrid Germany'}],'hasNext':False}]
  with patch('public_source_adapters.request_json',side_effect=result) as fn,patch('public_source_adapters.time.sleep'):
   jobs=nomado24({'queries':['quality']})
  self.assertEqual(len(jobs),2)
  self.assertEqual(jobs[0]['source_attribution'],'Nomado24')
  self.assertEqual(jobs[0]['published_at'],'2026-10-25')
  self.assertTrue(jobs[0]['applicant_region_unverified'])
  self.assertIn('cursor=next',fn.call_args_list[1].args[0])
  self.assertNotIn('q=',fn.call_args_list[1].args[0])
 def test_nomado_rejects_cursor_loop(self):
  with patch('public_source_adapters.request_json',return_value={'data':[],'hasNext':True,'nextCursor':'repeat'}),patch('public_source_adapters.time.sleep'):
   with self.assertRaises(ValueError):nomado24({'queries':['quality']})
 def test_muse_requires_registered_key(self):
  with patch.dict('os.environ',{},clear=True):
   with self.assertRaisesRegex(ValueError,'registered API key'):
    themuse({})
 def test_muse_public_contract(self):
  listing={'results':[{'id':123,'name':'Manufacturing Engineer','publication_date':'2026-10-22T12:00:00Z',
    'company':{'name':'Widget Manufacturer'},'locations':[{'name':'London, UK'}],
    'contents':'Engineering quality and production','refs':{'landing_page':'https://www.themuse.com/jobs/widget/engineer'}}]}
  with patch.dict('os.environ',{'THE_MUSE_API_KEY':'test-not-real'}),patch('public_source_adapters.request_json',return_value=listing) as fn:
   jobs=themuse({'categories':['Science and Engineering']})
  self.assertEqual(len(jobs),1)
  self.assertEqual(jobs[0]['source'],'The Muse')
  self.assertTrue(jobs[0]['application_url_unverified'])
  self.assertIn('category=Science+and+Engineering',fn.call_args.args[0])
 def test_duplicate_enrichment_preserves_original_link(self):
  old={'title':'Test Engineer','company':'Manufacturer','url':'https://jobs.example/42',
     'source':'Employer ATS','description':'Short summary','published_at':'','score':65,
     'hiring_support':{},'immigration_opportunity':{'tier':'unconfirmed_other'}}
  new={'source':'Job aggregator','description':'Full technical job posting with responsibilities, engineering process, quality control, testing and documented tasks.'*2,
       'published_at':'2026-10-25','visa_sponsorship_feed':True}
  with patch('radar.evaluate_rule',side_effect=lambda job,settings,cv:job):
   result=merge_duplicate_evidence(old,new,{},'cv')
  self.assertEqual(result['url'],'https://jobs.example/42')
  self.assertIn('Job aggregator',result['also_seen_on'])
  self.assertTrue(result['visa_sponsorship_feed'])
  self.assertEqual(result['immigration_opportunity']['tier'],'feed_tagged')
  self.assertEqual(result['published_at'],'2026-10-25')
 def test_json_extracts_object_from_model_prose(self):
  parsed=parse_structured_assessment('Analysis:\\n{"fit_score":80,"recommendation":"Apply"}\\nEnd.')
  self.assertEqual(parsed['fit_score'],80)
  with self.assertRaises(ValueError):parse_structured_assessment('not JSON')
 def test_muse_is_explicit_source(self):
  p=validate_request({'sources':['nomado24','themuse'],'region':'world'})
  self.assertEqual(p['sources'],['nomado24','themuse'])

 def test_workday_rotates_german_and_english_industrial_terms(self):
  board={'type':'workday','slug':'industrial','company':'Example','host':'example.wd3.myworkdayjobs.com','site':'Jobs'}
  with patch('public_source_adapters.request_json',return_value={'total':0,'jobPostings':[]}) as req:
   results=workday(board)
  self.assertEqual(results,[])
  self.assertEqual(req.call_count,8)
  self.assertTrue(any('Instandhaltung' in str(c.args) for c in req.call_args_list))
  self.assertTrue(any('Projekt' in str(c.args) for c in req.call_args_list))
 def test_source_expiry_does_not_fabricate_closed_status(self):
  from radar import listing_verification_status
  import datetime as dt
  now=dt.datetime(2026,10,27,tzinfo=dt.timezone.utc)
  self.assertEqual(listing_verification_status({'expires_at':'2026-10-20'},now),'expired_by_source_date')
  self.assertEqual(listing_verification_status({'expires_at':'2026-11-10'},now),'unexpired_by_source_date')
  self.assertEqual(listing_verification_status({'published_at':'2024-01-01'},now),'not_verified')

 def test_career_track_queries_expand_every_track(self):
  from industry_search import career_track_queries
  from pathlib import Path
  catalogue=json.loads((Path(__file__).resolve().parents[1]/'role_catalog.json').read_text())['roles']
  tracks=sorted({row['track'] for row in catalogue})
  queries=career_track_queries(catalogue,terms_per_track=10)
  self.assertEqual(set(queries),set(tracks))
  self.assertGreaterEqual(len(queries),30)
  self.assertTrue(all(len(values)>=1 for values in queries.values()))
  self.assertIn('CAMO Planner',queries['Aviation, CAMO & Maintenance'])
  self.assertIn('Luftfrachtabfertigung',queries['Airport Cargo, Freight & Logistics'])

if __name__=='__main__':unittest.main()
