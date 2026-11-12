import os
import sys
import types
import unittest
from unittest.mock import patch
from jobspy_optional import SITES,SITE_TYPES,authorized_sites,jobspy_board_status,jobspy_for_board,catalog_search_terms,requested_results_per_query,zip_location_country,indeed_city_sweep
from deep_search import validate_request

class JobSpyMultiPlatformTests(unittest.TestCase):
 def test_all_nine_sources_are_selectable_from_request(self):
  sources=list(SITE_TYPES)
  p=validate_request({'region':'world','sources':sources})
  self.assertEqual(p['sources'],sources)
 def test_no_platform_is_enabled_by_checkbox_alone(self):
  with patch.dict(os.environ,{},clear=True):
   self.assertEqual(authorized_sites(),set())
   for kind in SITE_TYPES:
    self.assertEqual(jobspy_board_status(kind),'disabled_permission_required')
    with self.assertRaisesRegex(ValueError,'authorization'):
     jobspy_for_board({'type':kind})
 def test_individual_authorization_never_enables_unlisted_platform(self):
  env={'JOBSPY_AUTHORIZED_SITES':'indeed,google,invalid_site'}
  self.assertEqual(authorized_sites(env),{'indeed','google'})
  self.assertNotIn('linkedin',authorized_sites({'JOBSPY_AUTHORIZED_SITES':'linkedin'}))
  self.assertNotIn('linkedin',authorized_sites({'JOBSPY_AUTHORIZED_SITES':'linkedin',
      'LINKEDIN_RETRIEVAL_AUTHORIZED':'yes'}))
  self.assertEqual(authorized_sites({'JOBSPY_AUTHORIZED_SITES':'linkedin',
      'LINKEDIN_RETRIEVAL_AUTHORIZED':'yes','JOBSPY_LINKEDIN_MODE':'live'}),{'linkedin'})
 def test_readiness_separates_linkedin_permission_from_zip_geography(self):
  env={'JOBSPY_AUTHORIZED_SITES':'linkedin,indeed,zip_recruiter'}
  germany={'region':'germany','cities':[]}
  self.assertEqual(jobspy_board_status('jobspy_linkedin',env,germany),
                   'offline_test_ready')
  self.assertEqual(jobspy_board_status('jobspy_zip_recruiter',env,germany),
                   'unsupported_geography')
  self.assertEqual(jobspy_board_status('jobspy_indeed',env,germany),
                   'configured_unverified')
  worldwide={'region':'world','cities':['Toronto, Canada']}
  self.assertEqual(zip_location_country(worldwide),'Canada')
  self.assertEqual(jobspy_board_status('jobspy_zip_recruiter',env,worldwide),
                   'configured_unverified')
  self.assertEqual(zip_location_country({'region':'world','cities':['Berlin, Germany']}),'')
  self.assertEqual(jobspy_board_status('jobspy_linkedin',
    {**env,'LINKEDIN_RETRIEVAL_AUTHORIZED':'yes'},germany),
    'offline_test_ready')
  self.assertEqual(jobspy_board_status('jobspy_linkedin',
    {**env,'JOBSPY_LINKEDIN_MODE':'live'},germany),
    'requires_independent_authorization')
  self.assertEqual(jobspy_board_status('jobspy_linkedin',
    {**env,'LINKEDIN_RETRIEVAL_AUTHORIZED':'yes','JOBSPY_LINKEDIN_MODE':'live'},germany),
    'configured_unverified')
 def test_indeed_city_sweep_supplements_only_deep_german_scans(self):
  profile={'region':'germany','depth':'deep','roles':[],'cities':[]}
  first=indeed_city_sweep(profile,run_rotation=40700820113)
  second=indeed_city_sweep(profile,run_rotation=40700820114)
  self.assertEqual(len(first),2)
  self.assertEqual(len(first[0]['queries']),4)
  self.assertNotEqual(first,second)
  self.assertTrue(all(x['city'] and x['queries'] for x in first))
  self.assertEqual(indeed_city_sweep({'region':'germany','depth':'focused'}),[])
  self.assertEqual(indeed_city_sweep({'region':'world','depth':'deep'}),[])
  self.assertEqual(indeed_city_sweep({**profile,'roles':['Quality Engineer']}),[])
  specified=indeed_city_sweep({**profile,'cities':['Berlin','Leipzig']},run_rotation=1)
  self.assertEqual({x['city'] for x in specified},{'Berlin','Leipzig'})
 def test_authorized_sites_are_bounded_without_proxies(self):
  calls=[]
  class FakeFrame:
   def to_dict(self,kind):
    assert kind=='records'
    return [{'company':'Plant A','title':'Airport Technical Coordinator',
      'location':'Frankfurt, Germany','job_url':'https://de.indeed.com/viewjob?jk=123',
      'date_posted':'2026-10-27','description':'Airport GSE maintenance project technician',
      'is_remote':False}]
  def scrape_jobs(**kwargs):
   calls.append(kwargs)
   return FakeFrame()
  mock=types.ModuleType('jobspy');mock.scrape_jobs=scrape_jobs
  with patch.dict(os.environ,{'JOBSPY_AUTHORIZED_SITES':'indeed'},clear=True):
   with patch.dict(sys.modules,{'jobspy':mock}):
    found=jobspy_for_board({'type':'jobspy_indeed','queries':['airport','maintenance','ignored'],
      'location':'Frankfurt','country':'Germany'})
  self.assertEqual(len(calls),3)
  self.assertTrue(all(c['site_name']==['indeed'] and c['proxies'] is None and
     c['results_wanted']==50 and c['hours_old']==168 for c in calls))
  self.assertEqual(calls[0]['country_indeed'],'Germany')
  self.assertEqual(len(found),1)
  self.assertEqual(found[0]['jobspy_site'],'indeed')
  self.assertEqual(found[0]['source'],'JobSpy / indeed')
  self.assertEqual(found[0]['url'],'https://de.indeed.com/viewjob?jk=123')
 def test_ziprecruiter_germany_is_explicitly_rejected(self):
  with patch.dict(os.environ,{'JOBSPY_AUTHORIZED_SITES':'zip_recruiter'},clear=True):
   with self.assertRaisesRegex(ValueError,'USA/Canada'):
    jobspy_for_board({'type':'jobspy_zip_recruiter','country':'Germany'})
 def test_invalid_site_never_imports_package(self):
  with self.assertRaises(ValueError):jobspy_for_board({'type':'jobspy_fake'})
 def test_jobspy_high_capacity_is_bounded_and_user_configurable(self):
  self.assertEqual(requested_results_per_query({}),50)
  self.assertEqual(requested_results_per_query({'JOBSPY_RESULTS_PER_QUERY':'60'}),60)
  self.assertEqual(requested_results_per_query({'JOBSPY_RESULTS_PER_QUERY':'900'}),75)
  self.assertEqual(requested_results_per_query({'JOBSPY_RESULTS_PER_QUERY':'invalid'}),50)
 def test_every_catalog_track_gets_a_query_on_each_authorized_platform(self):
  from pathlib import Path
  import json
  catalog=json.loads((Path(__file__).parents[1]/'role_catalog.json').read_text())['roles']
  tracks={x['track'] for x in catalog}
  for site in ('indeed','google','glassdoor'):
   plan=catalog_search_terms(site,catalog,when=__import__('datetime').date(2026,10,28))
   self.assertGreaterEqual(len(plan),len(tracks))
   self.assertTrue(all(isinstance(query,str) and query for query in plan))
 def test_all_requested_roles_are_used_not_just_first_two(self):
  from datetime import date
  roles=['quality engineer','cargo technician','maintenance planner','operations coordinator']
  plan=catalog_search_terms('indeed',[],requested_roles=roles,when=date(2026,10,28))
  self.assertEqual(plan,roles)
 def test_new_catalog_track_is_automatically_searched(self):
  from datetime import date
  catalog=[{'track':'New User Industrial Track','title':'Industrial Repair Coordinator'},
           {'track':'New User Industrial Track','title':'Workshop Technician'}]
  plan=catalog_search_terms('indeed',catalog,when=date(2026,10,28))
  self.assertIn('Industrial Repair Coordinator',plan)
  self.assertIn('Workshop Technician',plan)
 def test_one_empty_query_does_not_cancel_all_role_queries(self):
  calls=[]
  class Fake:
   def to_dict(self,kind):return []
  def search(**kwargs):
   calls.append(kwargs['search_term'])
   if kwargs['search_term']=='unknown role':raise ValueError('no job data returned')
   return Fake()
  mod=types.ModuleType('jobspy');mod.scrape_jobs=search
  board={'type':'jobspy_indeed','queries':['unknown role','quality engineer'],
         'location':'Germany','country':'Germany'}
  with patch.dict(os.environ,{'JOBSPY_AUTHORIZED_SITES':'indeed'},clear=True):
   with patch.dict(sys.modules,{'jobspy':mod}):
    self.assertEqual(jobspy_for_board(board),[])
  self.assertEqual(calls,['unknown role','quality engineer'])
  self.assertEqual(board['jobspy_run_stats']['completed_queries'],1)
  self.assertEqual(board['jobspy_run_stats']['failed_queries'],1)
 def test_google_jobs_is_marked_unsupported_in_jobspy_and_directs_to_serpapi(self):
  env={'JOBSPY_AUTHORIZED_SITES':'google'}
  self.assertEqual(jobspy_board_status('jobspy_google',env,{'region':'germany'}),
                   'unsupported_provider')
  with patch.dict(os.environ,env,clear=True):
   with self.assertRaisesRegex(ValueError,'SerpApi Google Jobs'):
    jobspy_for_board({'type':'jobspy_google','queries':['Quality Inspector'],
                      'location':'Stuttgart'})

 def test_workday_and_nomado_do_not_truncate_track_queries(self):
  from public_source_adapters import workday,nomado24
  queries=['technical engineer '+str(i) for i in range(14)]
  calls=[]
  def request(url,method='GET',body=None,**kwargs):
   if '/wday/cxs/' in url:
    calls.append(body['searchText'])
    return {'jobPostings':[],'total':0}
   calls.append(url.split('q=')[-1].split('&')[0])
   return {'data':[],'meta':{'hasNext':False}}
  with patch('public_source_adapters.request_json',side_effect=request):
   with patch('public_source_adapters.time.sleep',return_value=None):
    self.assertEqual(workday({'host':'company.wd5.myworkdayjobs.com','site':'External',
          'company':'Company','queries':queries}),[])
    self.assertEqual(nomado24({'type':'nomado24','queries':queries}),[])
  self.assertEqual(len(calls),len(queries)*2)
  self.assertEqual(calls[:len(queries)],queries)
 def test_himalayas_uses_entire_supplied_track_plan(self):
  from public_source_adapters import himalayas
  queries=['engineer '+str(i) for i in range(12)]
  searches=[]
  def response(url,**kwargs):
   if '/api/search?' in url:searches.append(url);return {'jobs':[]}
   return {'jobs':[]}
  with patch('public_source_adapters.request_json',side_effect=response):
   with patch('public_source_adapters.time.sleep',return_value=None):
    self.assertEqual(himalayas({'type':'himalayas','queries':queries}),[])
  self.assertEqual(len(searches),len(queries))

if __name__=='__main__': unittest.main()
