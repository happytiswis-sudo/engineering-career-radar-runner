import unittest
from unittest.mock import patch
from pathlib import Path
import json
from public_source_adapters import (
    fetch_public_source, request_json, smartrecruiters, workday, workable, jobicy, remotive, himalayas
)
from deep_search import validate_request
from radar import source_identity

ROOT=Path(__file__).resolve().parents[1]

class PublicSourceAdaptersTests(unittest.TestCase):
    def test_serpapi_google_jobs_paginates_and_deduplicates_tracking_urls(self):
        pages=[
          {'search_metadata':{'status':'Success'},'jobs_results':[{'title':'Manufacturing Engineer','company_name':'Example GmbH',
            'location':'Stuttgart, Germany','description':'Production engineering.','via':'Example',
            'detected_extensions':{'posted_at':'2 days ago'},
            'apply_options':[{'title':'Apply','link':'https://careers.example.com/jobs/123?utm_source=one'}]}],
           'serpapi_pagination':{'next_page_token':'page-two'}},
          {'search_metadata':{'status':'Success'},'jobs_results':[
            {'title':'Manufacturing Engineer','company_name':'Example GmbH','location':'Stuttgart, Germany',
             'share_link':'https://careers.example.com/jobs/123?utm_source=two'},
            {'title':'Quality Engineer','company_name':'Example GmbH','location':'Stuttgart, Germany',
             'apply_options':[{'link':'https://careers.example.com/jobs/456'}]}]}]
        board={'type':'serpapi_google_jobs','slug':'google-jobs','company':'Google Jobs',
               'queries':['manufacturing engineer'],'query_budget':1,'pages_per_query':2}
        with patch.dict('os.environ',{'SERPAPI_API_KEY':'test-key'}), patch('public_source_adapters.request_json',side_effect=pages) as request:
            jobs=fetch_public_source(board)
        self.assertEqual(len(request.call_args_list),2)
        self.assertIn('next_page_token=page-two',request.call_args_list[1].args[0])
        self.assertEqual(len(jobs),2)
        self.assertEqual(board['serpapi_run_stats']['completed_queries'],1)
        self.assertEqual(board['serpapi_run_stats']['pagination_pages'],1)
        self.assertEqual(board['serpapi_run_stats']['provider_rows'],3)
        self.assertEqual(board['serpapi_run_stats']['valid_postings'],2)
    def test_serpapi_google_jobs_requires_secret(self):
        board={'type':'serpapi_google_jobs','slug':'google-jobs','company':'Google Jobs'}
        with patch.dict('os.environ',{},clear=True):
            with self.assertRaisesRegex(ValueError,'SERPAPI_API_KEY'):
                fetch_public_source(board)

    def test_smartrecruiters_and_public_detail(self):
        company={'type':'smartrecruiters','slug':'RobertBosch','company':'Bosch Group','germany_first':True}
        listing={'totalFound':1,'content':[{'id':'123456','name':'Manufacturing Engineer',
          'location':{'city':'Stuttgart','country':'de'},'releasedDate':'2026-10-21'}]}
        details={'postingUrl':'https://jobs.smartrecruiters.com/RobertBosch/123456',
          'jobAd':{'sections':{'jobDescription':{'text':'Industrial manufacturing and 5S'}}}}
        with patch('public_source_adapters.request_json',side_effect=[listing,details]) as request:
            jobs=smartrecruiters(company)
        self.assertEqual(len(jobs),1)
        self.assertEqual(jobs[0]['title'],'Manufacturing Engineer')
        self.assertIn('Stuttgart',jobs[0]['location'])
        self.assertIn('Industrial manufacturing',jobs[0]['description'])
        self.assertIn('country=de',request.call_args_list[0].args[0])

    def test_workday_public_cxs(self):
        board={'type':'workday','slug':'airbus','company':'Airbus',
               'host':'ag.wd3.myworkdayjobs.com','site':'Airbus'}
        listings={'total':1,'jobPostings':[{'title':'Manufacturing Engineer',
                'locationsText':'Germany','externalPath':'/job/Hamburg/Manufacturing-Engineer_123'}]}
        detail={'jobPostingInfo':{'jobDescription':'Aircraft manufacturing','location':'Hamburg Area'}}
        with patch('public_source_adapters.request_json',
                   side_effect=[listings,detail,
                    {'total':0,'jobPostings':[]},
                    {'total':0,'jobPostings':[]},
                    {'total':0,'jobPostings':[]},
                    {'total':0,'jobPostings':[]},
                    {'total':0,'jobPostings':[]},
                    {'total':0,'jobPostings':[]},
                    {'total':0,'jobPostings':[]}]) as get:
            jobs=workday(board)
        self.assertEqual(len(jobs),1)
        self.assertEqual(jobs[0]['source'],'Workday')
        self.assertIn('/Airbus/job/',jobs[0]['url'])
        self.assertIn('Aircraft manufacturing',jobs[0]['description'])
        self.assertEqual(get.call_args_list[0].kwargs['method'] if 'method' in get.call_args_list[0].kwargs else get.call_args_list[0].args[1],'POST')

    def test_workday_rejects_untrusted_host(self):
        with self.assertRaises(ValueError):
            workday({'type':'workday','company':'Test','host':'example.com','site':'Career','slug':'test'})
    def test_jobicy_v2_deduplicates_across_keyword_queries(self):
        sample={'jobs':[{'url':'https://jobicy.com/jobs/one','jobTitle':'Production Engineer',
              'companyName':'Industrial One','jobGeo':'Europe','jobExcerpt':'Lean production'}]}
        with patch('public_source_adapters.request_json',return_value=sample) as req,patch('public_source_adapters.time.sleep'):
            jobs=jobicy({'type':'jobicy','slug':'global','company':'Jobicy'})
        self.assertEqual(len(jobs),1)
        self.assertEqual(req.call_count,5)
        self.assertIn('/api/v2/remote-jobs',req.call_args.args[0])
    def test_workable_employer_public_jobs(self):
        sample={'name':'Test Industrial','jobs':[{
            'title':'Manufacturing Project Engineer','country':'Germany','city':'Stuttgart',
            'application_url':'https://apply.workable.com/test/j/A1234567',
            'description':'Project planning and factory operations',
            'published_on':'2026-10-26','workplace_type':'hybrid'}]}
        with patch('public_source_adapters.request_json',return_value=sample) as request:
            jobs=workable({'type':'workable','slug':'test','company':'Test Industrial'})
        self.assertEqual(len(jobs),1)
        self.assertEqual(jobs[0]['source'],'Workable')
        self.assertIn('Stuttgart',jobs[0]['location'])
        self.assertIn('accounts/test',request.call_args.args[0])

    def test_remotive_source_attribution(self):
        sample={'jobs':[{'url':'https://remotive.com/remote-jobs/one','title':'CAD Engineer',
            'company_name':'Test','candidate_required_location':'Europe'}]}
        with patch('public_source_adapters.request_json',return_value=sample):
            jobs=remotive({'type':'remotive','slug':'global','company':'Remotive'})
        self.assertEqual(len(jobs),1)
        self.assertEqual(jobs[0]['source'],'Remotive (24h delay)')
    def test_himalayas_requires_correct_application_url(self):
        sample={'jobs':[{'companyName':'Example','title':'Project Engineer',
            'applicationLink':'https://himalayas.app/companies/example/jobs/engineer',
            'guid':'https://himalayas.app/companies/example/jobs/engineer',
            'locationRestrictions':['Germany'],'excerpt':'Planning',
            'pubDate':1790000000}],'nextCursor':None,'totalCount':1}
        with patch('public_source_adapters.request_json',return_value=sample) as req:
            jobs=himalayas({'type':'himalayas','slug':'remote','company':'Himalayas'})
        self.assertEqual(len(jobs),1)
        self.assertEqual(jobs[0]['source'],'Himalayas')
        self.assertEqual(jobs[0]['url'],sample['jobs'][0]['applicationLink'])
        self.assertIn('Remote restricted: Germany',jobs[0]['location'])
        self.assertIn('limit=20',req.call_args_list[0].args[0])
        self.assertIn('/jobs/api/search?',req.call_args_list[-1].args[0])
    def test_tracking_dedup_keeps_job_identifiers(self):
        first='https://example.org/careers/engineer?job_id=42&utm_source=linkedin'
        second='https://EXAMPLE.org/careers/engineer?job_id=42&utm_source=google'
        other='https://example.org/careers/engineer?job_id=43'
        self.assertEqual(source_identity(first),source_identity(second))
        self.assertNotEqual(source_identity(first),source_identity(other))

    def test_free_sources_all_allowed(self):
        request=validate_request({'sources':['ba','ats','arbeitnow','smartrecruiters',
            'workday','workable','jobicy','remotive','himalayas','linkedin-scraper','adzuna']})
        self.assertEqual(len(request['sources']),9)
        self.assertNotIn('adzuna',request['sources'])
        boards=json.loads((ROOT/'additional_job_boards.json').read_text())['public_sources']
        self.assertGreaterEqual(len(boards),10)
        self.assertEqual({x['type'] for x in boards},
             {'smartrecruiters','workday','workable','jobicy','remotive','himalayas','nomado24','arbeitnow_uk','themuse','personio','pinpoint','jobspy_linkedin'})
if __name__=='__main__':unittest.main()
