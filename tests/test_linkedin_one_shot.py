"""Offline-only one-query pilot tests: no actual LinkedIn network requests."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from linkedin_one_shot import single_linkedin_pilot,validate_pilot_inputs


ENV={'JOBSPY_AUTHORIZED_SITES':'linkedin',
     'JOBSPY_LINKEDIN_MODE':'live',
     'LINKEDIN_RETRIEVAL_AUTHORIZED':'yes'}

class OneQueryLinkedInTests(unittest.TestCase):
    def test_one_query_10_results_and_cv_pipeline_when_mock_retrieves_jobs(self):
        boards=[]
        def fake_jobspy(board):
            boards.append(board)
            board['jobspy_run_stats']={
                'attempted_queries':1,'completed_queries':1,'provider_rows':1}
            return [{
                'title':'Quality Engineer','company':'Fictional Factory',
                'location':'Hamburg, Germany','url':'https://careers.example.org/job/1',
                'description':'Quality supplier inspection','published_at':'2026-10-28',
                'application_url_unverified':False
            }]
        def fake_score(job,settings,cv):
            self.assertEqual(cv,'PRIVATE CV FIXTURE')
            self.assertEqual(job['title'],'Quality Engineer')
            return {**job,'score':82,'verdict':'Apply priority',
                    'qualification':{'status':'eligible'}}
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'public'/'linkedin-pilot.json'
            with patch.dict(os.environ,ENV,clear=True):
                with patch('linkedin_one_shot.jobspy_for_board',side_effect=fake_jobspy):
                    with patch('linkedin_one_shot.load',return_value=({},'PRIVATE CV FIXTURE')):
                        with patch('linkedin_one_shot.evaluate_rule',side_effect=fake_score):
                            result=single_linkedin_pilot('Quality Engineer','Germany',target)
            self.assertEqual(len(boards),1)
            self.assertEqual(boards[0]['queries'],['Quality Engineer'])
            self.assertEqual(result['requested_results'],10)
            self.assertEqual(result['status'],'retrieved')
            self.assertEqual(result['provider_rows'],1)
            self.assertEqual(result['cv_qualified_matches'],1)
            self.assertEqual(result['jobs'][0]['score'],82)
            self.assertTrue(target.exists())
            self.assertNotIn('PRIVATE CV FIXTURE',target.read_text())
            self.assertEqual(json.loads(target.read_text())['status'],'retrieved')

    def test_rate_limited_stops_after_one_provider_attempt_and_writes_report(self):
        calls=[]
        def fake_block(board):
            calls.append(board)
            board['jobspy_run_stats']={'attempted_queries':1,'completed_queries':0,
                                       'provider_rows':0}
            raise ValueError('JobSpy linkedin: HTTP 429 / rate limited (provider logged)')
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'report.json'
            with patch.dict(os.environ,ENV,clear=True):
                with patch('linkedin_one_shot.jobspy_for_board',side_effect=fake_block):
                    outcome=single_linkedin_pilot('Quality Engineer','Germany',target)
            self.assertEqual(len(calls),1)
            self.assertEqual(outcome['status'],'rate_limited')
            self.assertEqual(outcome['provider_queries_attempted'],1)
            self.assertEqual(outcome['valid_postings'],0)
            self.assertEqual(outcome['jobs'],[])
            self.assertTrue(target.exists())

    def test_checkbox_or_offline_setting_alone_does_not_authorize_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            for env in ({'JOBSPY_AUTHORIZED_SITES':'linkedin'},
                        {'JOBSPY_AUTHORIZED_SITES':'linkedin',
                         'LINKEDIN_RETRIEVAL_AUTHORIZED':'yes'}):
                with patch.dict(os.environ,env,clear=True):
                    with patch('linkedin_one_shot.jobspy_for_board') as call:
                        result=single_linkedin_pilot(output_path=Path(tmp)/'report.json')
                        call.assert_not_called()
                        self.assertEqual(result['status'],'not_authorized')

    def test_input_rejects_newlines_and_shell_metacharacters(self):
        for role in ('Quality Engineer\nUnexpected',
                     'Engineer; curl something',
                     '', 'A'*90):
            with self.assertRaises(ValueError):validate_pilot_inputs(role,'Germany')
        self.assertEqual(validate_pilot_inputs('Ground Operations Technician','Frankfurt, Germany'),
                         ('Ground Operations Technician','Frankfurt, Germany'))

if __name__=='__main__':unittest.main()
