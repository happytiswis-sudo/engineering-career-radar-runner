"""Offline LinkedIn JobSpy adapter contract. All provider calls are mocked.

Do not run real LinkedIn network calls or change authorization variables
outside temporary test contexts. Mock fixtures are NOT actual vacancies.
"""
import json
import logging
import os
import sys
import types
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from jobspy_optional import (
    authorized_sites,catalog_search_terms,jobspy_board_status,jobspy_for_board,
    linkedin_experiment_mode,requested_results_per_query,
)
from radar import evaluate_rule,load

ROOT=Path(__file__).parents[1]
LIVE_ENV={
    'JOBSPY_AUTHORIZED_SITES':'linkedin,indeed',
    'LINKEDIN_RETRIEVAL_AUTHORIZED':'yes',
    'JOBSPY_LINKEDIN_MODE':'live',
}

class MockFrame:
    def __init__(self,rows):self.rows=rows
    def to_dict(self,kind):
        assert kind=='records'
        return self.rows

class LinkedInJobSpyOfflineTests(unittest.TestCase):
    def test_selected_site_is_never_enough_to_make_a_request(self):
        with patch.dict(os.environ,{'JOBSPY_AUTHORIZED_SITES':'linkedin'},clear=True):
            self.assertEqual(linkedin_experiment_mode(),'offline')
            self.assertNotIn('linkedin',authorized_sites())
            self.assertEqual(jobspy_board_status('jobspy_linkedin'),'offline_test_ready')
            with self.assertRaisesRegex(ValueError,'authorization'):
                jobspy_for_board({'type':'jobspy_linkedin','queries':['Quality Engineer']})
        with patch.dict(os.environ,{
            'JOBSPY_AUTHORIZED_SITES':'linkedin',
            'LINKEDIN_RETRIEVAL_AUTHORIZED':'yes',
        },clear=True):
            self.assertNotIn('linkedin',authorized_sites())
        with patch.dict(os.environ,{
            'JOBSPY_AUTHORIZED_SITES':'linkedin','JOBSPY_LINKEDIN_MODE':'live',
        },clear=True):
            self.assertEqual(jobspy_board_status('jobspy_linkedin'),
                             'requires_independent_authorization')
            self.assertNotIn('linkedin',authorized_sites())

    def test_results_per_query_profile_and_operator_cap(self):
        self.assertEqual(requested_results_per_query(env={},override=75),75)
        self.assertEqual(requested_results_per_query(
            env={'JOBSPY_RESULTS_PER_QUERY':'60'},override=75),60)
        self.assertEqual(requested_results_per_query(env={},override=999),75)
        self.assertEqual(requested_results_per_query(env={},override=1),10)

    def test_synthetic_jobspy_results_use_normal_cv_engine(self):
        calls=[]
        rows=[
            {'company':'Fictional Engineering GmbH',
             'title':'Quality Engineer',
             'location':'Hamburg, Germany',
             'job_url':'https://www.linkedin.com/jobs/view/9876543210/',
             'job_url_direct':'https://careers.example.org/jobs/quality-001',
             'date_posted':date(2026,10,25),
             'description':'Supplier quality assurance, ISO 9001, manufacturing process and inspection.',
             'is_remote':False},
            {'company':'Fictional Engineering GmbH',
             'title':'Quality Engineer',
             'location':'Hamburg, Germany',
             'job_url':'https://www.linkedin.com/jobs/view/9876543210/',
             'job_url_direct':'https://careers.example.org/jobs/quality-001',
             'description':'duplicate fixture'},
            {'company':'','title':'','job_url':'not-a-url'}
        ]
        def provider(**kwargs):
            calls.append(kwargs)
            return MockFrame(rows)
        stub=types.ModuleType('jobspy')
        stub.scrape_jobs=provider
        board={'type':'jobspy_linkedin','slug':'approved-linkedin','country':'Germany',
               'location':'Germany','queries':['Quality Engineer','Airport Technician']}
        with patch.dict(os.environ,LIVE_ENV,clear=True),patch.dict(sys.modules,{'jobspy':stub}):
            found=jobspy_for_board(board)
        self.assertEqual(len(calls),2)
        self.assertEqual(len(found),1)
        self.assertTrue(all(x['site_name']==['linkedin'] and x['proxies'] is None
                     and x['fetch_description'] is False for x in calls))
        self.assertEqual(found[0]['source'],'JobSpy / linkedin')
        self.assertEqual(found[0]['date_posted'] if 'date_posted' in found[0] else
                         found[0]['published_at'],'2026-10-25')
        self.assertEqual(found[0]['url'],'https://careers.example.org/jobs/quality-001')
        self.assertEqual(found[0]['jobspy_aggregator_listing_url'],
                         'https://www.linkedin.com/jobs/view/9876543210/')
        self.assertTrue(found[0]['jobspy_direct_employer_link'])
        stats=board['jobspy_run_stats']
        self.assertEqual(stats['planned_queries'],2)
        self.assertEqual(stats['attempted_queries'],2)
        self.assertEqual(stats['completed_queries'],2)
        self.assertEqual(stats['cursor_advance_count'],2)
        self.assertEqual(stats['provider_rows'],6)
        self.assertEqual(stats['valid_postings'],1)
        self.assertEqual(stats['duplicate_rows'],3)
        self.assertEqual(stats['invalid_rows'],2)
        self.assertEqual(stats['description_present'],1)
        settings,cv=load()
        settings['catalog_roles']=json.loads((ROOT/'role_catalog.json').read_text(encoding='utf-8'))['roles']
        scored=evaluate_rule(found[0],settings,cv)
        self.assertIsNotNone(scored,'Synthetic LinkedIn quality fixture must enter CV scoring')
        self.assertEqual(scored['source'],'JobSpy / linkedin')
        self.assertIn('qualification',scored)

    def test_no_description_or_direct_url_does_not_fabricate_evidence(self):
        stub=types.ModuleType('jobspy')
        stub.scrape_jobs=lambda **kwargs:MockFrame([{
            'company':'Fictional Airport','title':'Cargo Technician',
            'location':'Frankfurt, Germany',
            'job_url':'https://www.linkedin.com/jobs/view/9876543211/',
            'date_posted':None,'description':None}])
        with patch.dict(os.environ,LIVE_ENV,clear=True),patch.dict(sys.modules,{'jobspy':stub}):
            job=jobspy_for_board({'type':'jobspy_linkedin','queries':['Cargo Technician']})[0]
        self.assertEqual(job['published_at'],'')
        self.assertTrue(job['application_url_unverified'])
        self.assertEqual(job['description_completeness'],'No job description supplied')

    def test_provider_block_is_terminal_for_linkedin_only(self):
        calls=[]
        def blocked(**kwargs):
            calls.append(kwargs)
            logging.getLogger('jobspy.linkedin').error('Response status code 403 denied')
            return MockFrame([])
        stub=types.ModuleType('jobspy')
        stub.scrape_jobs=blocked
        board={'type':'jobspy_linkedin','queries':['cargo','maintenance','quality']}
        with patch.dict(os.environ,LIVE_ENV,clear=True),patch.dict(sys.modules,{'jobspy':stub}):
            with self.assertRaisesRegex(ValueError,'HTTP 403'):
                jobspy_for_board(board)
        self.assertEqual(len(calls),1,'Never retry blocked LinkedIn site queries')
        self.assertEqual(board['jobspy_run_stats']['attempted_queries'],1)
        self.assertEqual(board['jobspy_run_stats']['stop_reason'],
                         'HTTP 403 / source blocked (provider logged)')

    def test_linkedin_query_pacing_is_applied_between_queries_only(self):
        calls=[]
        stub=types.ModuleType('jobspy')
        stub.scrape_jobs=lambda **kwargs:(calls.append(kwargs) or MockFrame([]))
        board={'type':'jobspy_linkedin','queries':['Quality Engineer','Cargo Technician'],
               'linkedin_query_delay_seconds':7}
        with patch.dict(os.environ,LIVE_ENV,clear=True),patch.dict(sys.modules,{'jobspy':stub}):
            with patch('jobspy_optional.time.sleep') as sleep:
                jobspy_for_board(board)
        sleep.assert_called_once_with(7)
        self.assertEqual(board['jobspy_run_stats']['cursor_advance_count'],2)
        self.assertEqual(board['jobspy_run_stats']['query_delay_seconds'],7)

    def test_linkedin_429_preserves_partial_rows_and_does_not_advance_blocked_term(self):
        calls=[]
        def provider(**kwargs):
            calls.append(kwargs)
            if len(calls)==2:
                logging.getLogger('jobspy.linkedin').error('Response status code 429 rate limited')
                return MockFrame([])
            return MockFrame([{
                'company':'Fixture Plant','title':'Quality Engineer',
                'location':'Hamburg, Germany',
                'job_url':'https://www.linkedin.com/jobs/view/9876543220/',
                'job_url_direct':'https://careers.example.org/jobs/qe-1',
                'date_posted':date(2026,10,29),'description':'Quality systems'
            }])
        stub=types.ModuleType('jobspy');stub.scrape_jobs=provider
        board={'type':'jobspy_linkedin','queries':['Quality Engineer','Cargo Technician','Maintenance Planner']}
        with patch.dict(os.environ,LIVE_ENV,clear=True),patch.dict(sys.modules,{'jobspy':stub}):
            found=jobspy_for_board(board)
        self.assertEqual(len(found),1)
        self.assertEqual(len(calls),2)
        stats=board['jobspy_run_stats']
        self.assertEqual(stats['attempted_queries'],2)
        self.assertEqual(stats['completed_queries'],1)
        self.assertEqual(stats['cursor_advance_count'],1)
        self.assertIn('429',stats['stop_reason'])

    def test_all_career_tracks_have_linkedin_plan_without_live_calls(self):
        catalog=json.loads((ROOT/'role_catalog.json').read_text(encoding='utf-8'))['roles']
        query_plan=catalog_search_terms('linkedin',catalog,depth='deep',
                                        when=date(2026,10,28),run_rotation=40701412415)
        self.assertGreaterEqual(len(query_plan),len({r['track'] for r in catalog}))
        requested=['Quality Engineer','Ground Operations Technician','Cargo Inspector']
        self.assertEqual(catalog_search_terms('linkedin',catalog,requested_roles=requested),
                         requested)

if __name__=='__main__':unittest.main()
