import io
import json
import unittest
from unittest.mock import patch
from datetime import date, timedelta
from types import SimpleNamespace
import sys
import logging
from public_source_adapters import personio,pinpoint
from ats_directory_discovery import parse_directory,choose_directory
from jobspy_optional import linkedin_jobspy, jobspy_for_board, catalog_search_terms, tidy_provider_description
from deep_search import validate_request

PERSONIO=b'''<?xml version="1.0" encoding="UTF-8"?>
<workzag-jobs><position><id>1102</id><office>Stuttgart</office>
<department>Quality</department><name>Quality Technician</name>
<jobDescriptions><jobDescription><name>Aufgaben</name><value><![CDATA[<p>Inspection and calibration support</p>]]></value></jobDescription></jobDescriptions>
<createdAt>2026-10-20T09:00:00+0200</createdAt></position></workzag-jobs>'''
class MockResponse:
 def __init__(self,data):self.data=data
 def __enter__(self):return self
 def __exit__(self,*a):return False
 def read(self,size=None):return self.data

class ATSIntegrationsTests(unittest.TestCase):
 def test_personio_xml_preserves_jobs_without_inventing_apply_url(self):
  with patch('public_source_adapters.urllib.request.urlopen',return_value=MockResponse(PERSONIO)) as get:
   jobs=personio({'type':'personio','slug':'knime','domain':'com','company':'KNIME'})
  self.assertEqual(len(jobs),1)
  self.assertIn('Stuttgart',jobs[0]['location'])
  self.assertIn('Inspection',jobs[0]['description'])
  self.assertEqual(jobs[0]['source'],'Personio')
  self.assertTrue(jobs[0]['application_url_unverified'])
  self.assertEqual(jobs[0]['url'],'https://knime.jobs.personio.com')
  self.assertEqual(jobs[0]['employer_posting_id'],'1102')
 def test_personio_blocks_dtd_and_bad_slugs(self):
  with self.assertRaises(ValueError):personio({'slug':'../bad','domain':'de','company':'Bad'})
  with patch('public_source_adapters.urllib.request.urlopen',
             return_value=MockResponse(b'<!DOCTYPE foo [<!ENTITY bar "unsafe">]><root/>')):
   with self.assertRaisesRegex(ValueError,'DTD'):personio({'slug':'knime','domain':'de','company':'Knime'})
 def test_personio_404_propagates_for_source_specific_cooldown(self):
  import urllib.error
  error=urllib.error.HTTPError('https://knime.jobs.personio.com/xml?language=de',404,'Not Found',{},None)
  with patch('public_source_adapters.urllib.request.urlopen',side_effect=error):
   with self.assertRaises(urllib.error.HTTPError) as caught:
    personio({'type':'personio','slug':'knime','domain':'com','company':'KNIME'})
  self.assertEqual(caught.exception.code,404)
 def test_pinpoint_new_postings_json_with_direct_employer_link_and_expiry(self):
  posting={'data':[{'id':'99','title':'Cargo Warehouse Coordinator','url':'https://workwithus.pinpointhq.com/postings/99',
      'description':'Cargo logistics testing','key_responsibilities':'Airport logistics',
      'skills_knowledge_expertise':'Warehouse documentation',
      'deadline_at':'2026-12-31','location':{'name':'Frankfurt'},
      'department':{'name':'Aviation Operations'}},
      {'id':'98','title':'Bad','url':'https://malicious.example/jobs/98','location':{'name':'Remote'}}]}
  with patch('public_source_adapters.request_json',return_value=posting) as get:
   jobs=pinpoint({'type':'pinpoint','slug':'workwithus','company':'Pinpoint'})
  self.assertEqual(len(jobs),1)
  self.assertEqual(jobs[0]['expires_at'],'2026-12-31')
  self.assertEqual(jobs[0]['url'],'https://workwithus.pinpointhq.com/postings/99')
  self.assertIn('Warehouse documentation',jobs[0]['description'])
  self.assertIn('/postings.json',get.call_args.args[0])
 def test_pinpoint_workplace_type_distinguishes_remote_and_hybrid(self):
  samples={'data':[
   {'id':'10','title':'Technical Support Coordinator','url':'https://workwithus.pinpointhq.com/en/postings/10',
    'location':{'name':'Germany'},'workplace_type':'remote','employment_type':'full_time'},
   {'id':'11','title':'Quality Coordinator','url':'https://workwithus.pinpointhq.com/en/postings/11',
    'location':{'name':'Berlin'},'workplace_type':'hybrid','employment_type':'permanent'}]}
  with patch('public_source_adapters.request_json',return_value=samples):
   jobs=pinpoint({'slug':'workwithus','company':'Pinpoint'})
  self.assertEqual(len(jobs),2)
  self.assertTrue(jobs[0]['remote'])
  self.assertEqual(jobs[0]['workplace_type_original'],'remote')
  self.assertFalse(jobs[1]['remote'])
  self.assertEqual(jobs[1]['workplace_type_original'],'hybrid')
  self.assertEqual(jobs[1]['employment_type_original'],'permanent')
 def test_directory_csv_rejects_untrusted_hosts_and_keeps_public_slugs(self):
  csv_text='platform,token,company,board_url,api_url,open_roles,count_basis,region\n'
  csv_text+='personio,solar-energy,Solar,https://solar-energy.jobs.personio.de,https://solar-energy.jobs.personio.de/xml,12,observed,\n'
  csv_text+='personio,hostile,Hostile,https://hostile.example,https://hostile.example/xml,200,observed,\n'
  found=parse_directory(csv_text,'personio')
  self.assertEqual(len(found),1)
  self.assertEqual(found[0]['slug'],'solar-energy')
 def test_directory_selects_new_entries_bounded_and_dedups(self):
  def response(req,timeout):
   fname=req.full_url.split('/')[-1]
   kind=fname.split('.')[0]
   if kind=='personio':
    text='platform,token,company,board_url,api_url,open_roles,count_basis,region\n'
    text+='personio,solar-energy,Solar Energy,https://solar-energy.jobs.personio.de,https://solar-energy.jobs.personio.de/xml,20,observed,\n'
   else:
    text='platform,token,company,board_url,api_url,open_roles,count_basis,region\n'
   return MockResponse(text.encode())
  with patch('ats_directory_discovery.urllib.request.urlopen',side_effect=response):
   chosen,report=choose_directory([],when=date(2026,10,28),per_family={'personio':2,'greenhouse':0,'ashby':0})
  self.assertEqual(len(chosen),1)
  self.assertEqual(chosen[0]['type'],'personio')
  self.assertEqual(report['personio']['new_boards_selected'],1)
 def test_jobspy_is_disabled_without_permission_and_no_network_or_import(self):
  with patch.dict('os.environ',{},clear=True):
   with self.assertRaisesRegex(ValueError,'authorization'):
    linkedin_jobspy({'type':'jobspy_linkedin'})
 def test_jobspy_description_decoding_preserves_normal_markup(self):
  raw='##### **I****n****s****i****d****e** and **Quality Engineer**'
  fixed=tidy_provider_description(raw)
  self.assertIn('Inside',fixed)
  self.assertIn('**Quality Engineer**',fixed)
  self.assertNotIn('**I**',fixed)
 def test_jobspy_queries_rotate_full_catalog_titles_per_day_and_platform(self):
  catalog=[{'track':'Airport Cargo, Freight & Logistics','title':'Cargo Inspector'},
           {'track':'Airport Cargo, Freight & Logistics','title':'Cargo Coordinator'},
           {'track':'Airport Cargo, Freight & Logistics','title':'Cargo Scheduler'},
           {'track':'Airport Cargo, Freight & Logistics','title':'Cargo Loader'}]
  when=date(2026,10,28)
  results=[catalog_search_terms('indeed',catalog,when=when+timedelta(days=i))
           for i in range(10)]
  self.assertTrue(any(x!=results[0] for x in results[1:]))
  self.assertTrue(any('Cargo Loader' in day for day in results))
  self.assertTrue(all(len(day)==2 for day in results))
 def test_jobspy_429_sets_terminal_provider_block_flag(self):
  calls=[]
  def blocked(**kwargs):
   calls.append(kwargs)
   raise ValueError('response status code 429 rate limit')
  with patch.dict('os.environ',{'JOBSPY_AUTHORIZED_SITES':'linkedin','LINKEDIN_RETRIEVAL_AUTHORIZED':'yes','JOBSPY_LINKEDIN_MODE':'live'},clear=True):
   with patch.dict(sys.modules,{'jobspy':SimpleNamespace(scrape_jobs=blocked)}):
    board={'type':'jobspy_linkedin','country':'Germany','queries':['quality engineer','cargo coordinator']}
    with self.assertRaisesRegex(ValueError,'HTTP 429 / rate limited'):
     jobspy_for_board(board)
  self.assertEqual(len(calls),1,'429 is terminal; do not retry or bypass')
  self.assertEqual(board['jobspy_run_stats']['attempted_queries'],1)
  self.assertTrue(board['jobspy_run_stats']['provider_blocked'])

 def test_jobspy_http403_is_safely_classified_without_retry(self):
  calls=[]
  def blocked(**kwargs):
   calls.append(kwargs)
   raise ValueError('response status code 403 (blocked: use a proxy)')
  with patch.dict('os.environ',{'JOBSPY_AUTHORIZED_SITES':'glassdoor'},clear=True):
   with patch.dict(sys.modules,{'jobspy':SimpleNamespace(scrape_jobs=blocked)}):
    with self.assertRaisesRegex(ValueError,'HTTP 403 / source blocked'):
     jobspy_for_board({'type':'jobspy_glassdoor','country':'Germany','queries':['quality engineer']})
  self.assertEqual(len(calls),1)
  self.assertIsNone(calls[0]['proxies'])
 def test_jobspy_logs_blocked_403_and_aborts_only_that_platform(self):
  import types
  from unittest.mock import patch
  calls=[]
  class EmptyFrame:
   def to_dict(self,format):return []
  def provider(**kwargs):
   calls.append(kwargs)
   logging.getLogger('jobspy.glassdoor').error('response status code 403 (blocked: use a proxy)')
   return EmptyFrame()
  board={'type':'jobspy_glassdoor','country':'Germany',
         'queries':['quality engineer','cargo coordinator','project engineer']}
  with patch.dict('os.environ',{'JOBSPY_AUTHORIZED_SITES':'glassdoor'},clear=True):
   with patch.dict(sys.modules,{'jobspy':types.SimpleNamespace(scrape_jobs=provider)}):
    with self.assertRaisesRegex(ValueError,'HTTP 403'):
     jobspy_for_board(board)
  self.assertEqual(len(calls),1)
  self.assertEqual(board['jobspy_run_stats']['attempted_queries'],1)
  self.assertEqual(board['jobspy_run_stats']['failed_queries'],1)
  self.assertIn('HTTP 403',board['jobspy_run_stats']['stop_reason'])
 def test_same_day_catalog_search_rotates_between_gitHub_runs(self):
  from datetime import date
  catalog=[{'track':'Aviation Operations','title':'Ramp Coordinator'},
           {'track':'Aviation Operations','title':'Cargo Inspector'},
           {'track':'Aviation Operations','title':'Baggage Coordinator'},
           {'track':'Aviation Operations','title':'Ground Operations Technician'}]
  today=date(2026,10,28)
  first=catalog_search_terms('indeed',catalog,when=today,run_rotation=40672442941)
  second=catalog_search_terms('indeed',catalog,when=today,run_rotation=40672442942)
  self.assertEqual(len(first),2)
  self.assertEqual(len(second),2)
  self.assertNotEqual(first,second)
  exact=['Airport Technician','Quality Coordinator','Maintenance Engineer']
  self.assertEqual(catalog_search_terms('indeed',catalog,requested_roles=exact,
      when=today,run_rotation=10),exact)

 def test_google_provider_logged_no_data_is_not_a_successful_query(self):
  import types
  from unittest.mock import patch
  calls=[]
  class EmptyFrame:
   def to_dict(self,format):return []
  def provider(**kwargs):
   calls.append(kwargs)
   logging.getLogger('jobspy.google').error('no job data returned')
   return EmptyFrame()
  board={'type':'jobspy_google','country':'Germany',
         'queries':['design engineer','airport operations','cargo coordinator']}
  with patch.dict('os.environ',{'JOBSPY_AUTHORIZED_SITES':'google'},clear=True):
   with patch.dict(sys.modules,{'jobspy':types.SimpleNamespace(scrape_jobs=provider)}):
    with self.assertRaisesRegex(ValueError,'no usable data'):
     jobspy_for_board(board)
  self.assertEqual(len(calls),3,'all catalog queries must still be attempted')
  self.assertEqual(board['jobspy_run_stats']['completed_queries'],0)
  self.assertEqual(board['jobspy_run_stats']['no_data_queries'],3)
  self.assertEqual(board['jobspy_run_stats']['failed_queries'],0)
  self.assertTrue(all(call['proxies'] is None for call in calls))

 def test_request_validation_accepts_new_optional_sources(self):
  p=validate_request({'sources':['personio','pinpoint','jobspy_linkedin'],'region':'world'})
  self.assertEqual(set(p['sources']),{'personio','pinpoint','jobspy_linkedin'})
if __name__=='__main__':unittest.main()
