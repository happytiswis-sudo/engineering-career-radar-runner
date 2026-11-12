import datetime as dt
import unittest
from unittest.mock import patch
from career_intelligence import (published_on,recent_enough,hiring_opportunity,
     capability_assessment,run_extended_agents,EXTENDED_TEAMS)
from deep_search import validate_request,eligible_job,ROLE_GROUPS
from public_source_adapters import nomado24

NOW=dt.datetime(2026,10,26,12,tzinfo=dt.timezone.utc)

class BroaderCareerIntelligenceTests(unittest.TestCase):
 def sample(self):
  return {'title':'Production Technician','company':'Example',
    'description':'Technical assembly and quality','published_at':'2026-10-25',
    'market':{'germany':True,'west':True,'small_city':True},
    'hiring_support':{'visa':{'status':'not_stated'},'relocation':{'status':'not_stated'}},
    'score':32,'score_components':{'role':24},'matched_skills':['Manufacturing','Quality'],
    'missing_skills':[],'check_requirements':[],
    'qualification':{'status':'review'},'career_track':'Adjacent Technical & Engineering Support'}
 def test_calendar_freshness_and_missing_date(self):
  self.assertEqual(published_on('2026-10-25',NOW)['bucket'],'week')
  self.assertEqual(published_on('2026-10-26',NOW)['bucket'],'day')
  self.assertEqual(published_on('2026-09-27',NOW)['bucket'],'month')
  self.assertEqual(published_on('',NOW)['bucket'],'unknown')
  self.assertIsNone(published_on('wrong',NOW)['age_days'])
  self.assertEqual(published_on('2030-01-01',NOW)['bucket'],'unknown')
 def test_unknown_freshness_not_marked_recent(self):
  job=self.sample()
  self.assertFalse(recent_enough({'published_at':'not known'},'7'))
  self.assertTrue(recent_enough({'published_at':''},'unknown'))
 def test_opportunity_without_claiming_visa(self):
  j=self.sample()
  x=hiring_opportunity(j['hiring_support'],j['market'])
  self.assertEqual(x['tier'],'unconfirmed_germany')
  self.assertFalse(x['confirmed_assistance'])
  self.assertTrue(x['can_inquire'])
  self.assertFalse(eligible_job(j,{**validate_request({'support':'visa'}),'min_score':0}))
  self.assertTrue(eligible_job(j,{**validate_request({'support':'visa_possible'}),'min_score':0}))
 def test_explicit_no_sponsorship_not_included(self):
  j=self.sample()
  j['hiring_support']['visa']={'status':'not_offered'}
  self.assertFalse(eligible_job(j,{**validate_request({'support':'visa_possible'}),'min_score':0}))
 def test_transferable_ability_for_lower_seniority(self):
  c=capability_assessment(self.sample())
  self.assertTrue(c['open_to_junior_roles'])
  self.assertGreater(c['capability_score'],50)
  x=run_extended_agents(self.sample())
  self.assertEqual(x['specialists_executed'],18)
  self.assertEqual(len(EXTENDED_TEAMS),3)
 def test_expanded_industries(self):
  for key in ('rail','medical_industry','automotive','industrial_support','inspection','testing','materials'):
   self.assertIn(key,ROLE_GROUPS)
 def test_nomado_parses_real_url_and_refuses_to_invent(self):
  fake={'data':[{'title':'Project Engineer','company':'Example Germany','url':'https://nomado24.com/jobs/real',
      'location':'Germany','published_at':'2026-10-24'},
      {'title':'Engineering Technician','company':'No Link'}], 'meta':{}}
  with patch('public_source_adapters.request_json',return_value=fake) as request,patch('public_source_adapters.time.sleep'):
   jobs=nomado24({'type':'nomado24','slug':'public-de-eu','company':'Nomado24'})
  self.assertEqual(len(jobs),1)
  self.assertEqual(jobs[0]['source'],'Nomado24')
  self.assertEqual(request.call_count,4)
  self.assertTrue(all('api/public/v2/jobs' in c.args[0] for c in request.call_args_list))
if __name__=='__main__':unittest.main()
