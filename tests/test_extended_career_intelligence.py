import datetime as dt
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from career_intelligence import published_on, hiring_opportunity, capability_assessment, run_extended_agents, AGENT_DEPENDENCIES
from deep_search import eligible_job, validate_request, ROLE_GROUPS
from public_source_adapters import nomado24
from radar import evaluate_rule
ROOT=Path(__file__).resolve().parents[1]

class ExtendedCareerIntelTests(unittest.TestCase):
 def setUp(self):
  self.now=dt.datetime(2026,10,26,12,0,tzinfo=dt.timezone.utc)
  self.west={'west':True,'germany':True,'small_city':False}
  self.support={k:{'status':'not_stated'} for k in ('visa','blue_card','relocation','international')}
 def test_date_windows_are_not_fabricated(self):
  self.assertEqual(published_on('',self.now)['bucket'],'unknown')
  self.assertEqual(published_on('2026-10-26T00:00:00Z',self.now)['bucket'],'day')
  self.assertEqual(published_on('2026-10-24T11:00:00Z',self.now)['bucket'],'week')
  self.assertEqual(published_on('2026-10-10T12:00:00Z',self.now)['bucket'],'month')
  self.assertEqual(published_on('2026-08-20',self.now)['bucket'],'quarter')
  self.assertEqual(published_on('not a date',self.now)['bucket'],'unknown')
  self.assertEqual(published_on('2026-10-25T05:00:00Z',self.now)['bucket'],'week')
 def test_visa_evidence_must_not_be_assumed(self):
  u=hiring_opportunity(self.support,self.west)
  self.assertEqual(u['tier'],'unconfirmed_germany')
  self.assertTrue(u['can_inquire'])
  self.assertFalse(u['confirmed_assistance'])
  s=dict(self.support,visa={'status':'not_offered'})
  self.assertEqual(hiring_opportunity(s,self.west)['tier'],'visa_not_offered')
  s=dict(self.support,visa={'status':'explicit'})
  self.assertTrue(hiring_opportunity(s,self.west)['confirmed_assistance'])
 def test_inclusive_visa_search_not_equal_explicit_visa(self):
  job={'market':self.west,'score':66,'published_at':'2026-10-25',
       'hiring_support':self.support,'qualification':{'status':'review'},
       'immigration_opportunity':hiring_opportunity(self.support,self.west),'career_track':'Manufacturing'}
  settings=validate_request({'support':'visa_possible','min_score':35,'freshness':'all'})
  self.assertTrue(eligible_job(job,settings))
  strict=validate_request({'support':'visa','min_score':35})
  self.assertFalse(eligible_job(job,strict))
  explicit=dict(job,hiring_support=dict(self.support,visa={'status':'explicit'}))
  self.assertTrue(eligible_job(explicit,strict))
  no=dict(job,immigration_opportunity=hiring_opportunity(dict(self.support,visa={'status':'not_offered'}),self.west))
  self.assertFalse(eligible_job(no,settings))
 def test_capable_technician_even_if_title_score_weak(self):
  job={'title':'Technischer Mitarbeiter','score':22,'market':self.west,
       'capability':{'open_to_junior_roles':True,'capability_score':74},
       'qualification':{'status':'review'},'hiring_support':self.support,'career_track':'Industrial Technical'}
  self.assertTrue(eligible_job(job,validate_request({'min_score':35})))
  job['qualification']={'status':'excluded'}
  self.assertFalse(eligible_job(job,validate_request({'min_score':35})))
 def test_more_than_500_roles_across_industries(self):
  catalog=json.loads((ROOT/'role_catalog.json').read_text())['roles']
  self.assertGreaterEqual(len(catalog),500)
  self.assertGreaterEqual(len({x['track'] for x in catalog}),20)
  self.assertIn('medical_industry',ROLE_GROUPS)
  self.assertIn('rail',ROLE_GROUPS)
 def test_transferable_non_design_role_can_pass_minimum_score(self):
  job={'score':28,'capability':{'transferable':True,'capability_score':68,'open_to_junior_roles':False},
       'qualification':{'status':'review'},'market':self.west,
       'hiring_support':self.support,'career_track':'Operations & Technical Delivery',
       'freshness':{'age_days':None,'bucket':'unknown'}}
  profile=validate_request({'min_score':45,'freshness':'all'})
  self.assertTrue(eligible_job(job,profile))
  job['qualification']={'status':'excluded'}
  self.assertFalse(eligible_job(job,profile))

 def test_12_additional_agents_are_executed(self):
  job={'title':'Production Technician','score':55,'market':self.west,
       'qualification':{'status':'review'},'published_at':'2026-10-24T10:00:00+00:00',
       'matched_skills':['Manufacturing'],'hiring_support':self.support}
  data=run_extended_agents(job)
  self.assertEqual(data['specialists_executed'],18)
  self.assertEqual(len(data['agent_findings']),18)
  self.assertEqual(sum(data['teams'].values()),18)
  from agent_engine import AGENTS
  existing={a.ident for a in AGENTS}
  self.assertEqual(set(AGENT_DEPENDENCIES),{str(i) for i in range(37,55)})
  for i in range(37,55):
   dependencies=AGENT_DEPENDENCIES[str(i)]
   self.assertTrue(dependencies)
   self.assertTrue(all(ref in existing or ref in {str(n) for n in range(37,i)} for ref in dependencies))
  self.assertEqual(data['agent_findings'][-1]['depends_on'],AGENT_DEPENDENCIES['54'])
  self.assertTrue(data['capability']['open_to_junior_roles'])
  self.assertEqual(data['teams']['career_expansion'],6)
  self.assertEqual(data['agent_findings'][-1]['agent'],'54')
 def test_nomado24_json_integration_mock(self):
  sample={'data':[{'title':'Manufacturing Project Engineer','url':'https://www.nomado24.com/job/industrial-123','company':{'name':'Sample GmbH'},
    'location':'Stuttgart, Germany','work_arrangement':'hybrid','description':'Factory project delivery',
    'published_at':'2026-10-26T07:00:00Z'}],'meta':{'page':1,'total':1}}
  with patch('public_source_adapters.request_json',return_value=sample) as mock,patch('public_source_adapters.time.sleep'):
   jobs=nomado24({'type':'nomado24','slug':'public-de-eu','company':'Nomado24'})
  self.assertEqual(len(jobs),1)
  self.assertEqual(jobs[0]['source'],'Nomado24')
  self.assertEqual(jobs[0]['company'],'Sample GmbH')
  self.assertFalse(jobs[0]['remote'])
  self.assertEqual(jobs[0]['source_attribution'],'Nomado24')
  self.assertIn('api/public/v2/jobs',mock.call_args.args[0])
if __name__=='__main__':unittest.main()
