"""Regression for LinkedIn-only GitHub run 40842548410 (provider HTTP 429)."""
import json
import tempfile
import unittest
from pathlib import Path
from scan_failure import build_empty_scan_report,save_empty_scan_report


class ScanFailureTests(unittest.TestCase):
    def test_linkedin_429_reports_block_and_previous_results_preserved(self):
        failures=[{'source':'jobspy_linkedin','board':'approved-linkedin',
                   'company':'JobSpy / linkedin',
                   'error':'JobSpy linkedin: HTTP 429 / rate limited (provider logged)'}]
        metrics={'jobspy_linkedin':{
            'boards':1,'errors':1,'succeeded':0,'returned':0,
            'planned_queries':68,'attempted_queries':1,'completed_queries':0,
            'failed_queries':1,'provider_rows':0,'valid_postings':0}}
        report=build_empty_scan_report(
            failures,metrics,
            [{'type':'jobspy_linkedin','slug':'approved-linkedin','queries':['Quality Engineer']}],
            '40842548410')
        self.assertEqual(report['status'],'failed_no_usable_source_results')
        self.assertEqual(report['failure_categories'],{'rate_limited':1})
        self.assertEqual(report['source_query_metrics']['jobspy_linkedin']['attempted_queries'],1)
        self.assertEqual(report['source_query_metrics']['jobspy_linkedin']['planned_queries'],68)
        self.assertEqual(report['selected_source_tasks'],1)
        self.assertTrue(report['result_snapshot_preserved'])
        self.assertIn('HTTP 429',report['diagnosis'])
        self.assertNotIn('proxy',report['diagnosis'].lower())
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'scan-failure.json'
            summary=Path(folder)/'github-summary.md'
            save_empty_scan_report(report,path,summary)
            saved=json.loads(path.read_text(encoding='utf8'))
            self.assertEqual(saved['failed_board_count'],1)
            self.assertIn('rate-limited',summary.read_text(encoding='utf8').lower())
            self.assertIn('previous published snapshot preserved',
                          summary.read_text(encoding='utf8').lower())
            self.assertNotIn('CV content',str(saved))
            self.assertNotIn('jobs/view/',str(saved))
    def test_unconfigured_option_not_counted_as_failed_board(self):
        report=build_empty_scan_report([
            {'source':'jobspy_linkedin','board':'optional-linkedin',
             'error':'LinkedIn experiment offline'},
            {'source':'jobspy_google','board':'approved-google',
             'error':'provider returned no usable data for 68 searches'}],
            {'jobspy_google':{'boards':1,'errors':1,'no_data_queries':68}},
            [{'type':'jobspy_google'}], '40842548411')
        self.assertEqual(report['failure_categories'],{'no_usable_data':1})
        self.assertEqual(report['failed_board_count'],1)
        self.assertNotIn('429',report['diagnosis'])
    def test_no_sources_does_not_invent_block_or_jobs(self):
        report=build_empty_scan_report([],{},[],None)
        self.assertEqual(report['selected_source_tasks'],0)
        self.assertEqual(report['failure_categories'],{})
        self.assertTrue(report['no_vacancy_market_claim'])
        self.assertIn('no valid job URLs',report['diagnosis'])


if __name__=='__main__':unittest.main()
