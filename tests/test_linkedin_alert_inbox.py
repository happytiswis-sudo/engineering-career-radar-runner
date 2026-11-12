"""LinkedIn user job-alert inbox: no LinkedIn HTTP requests or fabricated freshness."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from linkedin_alert_inbox import canonical_linkedin_job_url,inbox_postings
from radar import fetch_board,evaluate_rule,load
from discovery_quality import freshness_counts

class LinkedInInboxTests(unittest.TestCase):
 def test_only_canonical_direct_linkedin_job_urls_allowed(self):
  self.assertEqual(canonical_linkedin_job_url(
   'https://de.linkedin.com/jobs/view/1234567890/?trackingId=hello'),
   'https://www.linkedin.com/jobs/view/1234567890/')
  self.assertEqual(canonical_linkedin_job_url(
   'https://www.linkedin.com/comm/jobs/view/1234567890/'),
   'https://www.linkedin.com/jobs/view/1234567890/')
  for bad in ('https://linkedin.com.evil.example/jobs/view/1234567890/',
   'http://www.linkedin.com/jobs/view/1234567890/',
   'https://linkedin.com/in/example',
   'https://www.linkedin.com/jobs/view/not-a-job/',
   'https://evil.example/?next=https://linkedin.com/jobs/view/1234567890/'):
   self.assertEqual(canonical_linkedin_job_url(bad),'',bad)
 def test_imported_records_are_cv_screenable_and_never_claim_posted_today(self):
  raw={'schema_version':1,'jobs':[
   {'title':'Quality Engineer','company':'Example Works',
    'location':'Hamburg, Germany','url':'https://linkedin.com/jobs/view/1234567890/',
    'description':'ISO 9001 inspection and supplier quality',
    'imported_at':'2026-10-28T14:00:00Z'},
   {'title':'Quality Engineer','company':'Example Works',
    'location':'Hamburg, Germany','url':'https://www.linkedin.com/jobs/view/1234567890/?trk=feed'},
   {'title':'Bad','company':'Bad','location':'Anywhere',
    'url':'https://linkedin.com.evil.example/jobs/view/1234567890/'}]}
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'linkedin_alerts.json'
   path.write_text(json.dumps(raw),encoding='utf-8')
   with patch('linkedin_alert_inbox.Path.read_text',return_value=path.read_text(encoding='utf-8')):
    jobs=fetch_board({'type':'linkedin_alerts','slug':'personal-job-alert-inbox','company':'My alerts'})
  self.assertEqual(len(jobs),1)
  self.assertEqual(jobs[0]['published_at'],'')
  self.assertEqual(jobs[0]['alert_imported_at'],'2026-10-28T14:00:00Z')
  self.assertTrue(jobs[0]['imported_from_user_alert'])
  self.assertIn('no_employer_posting_date',jobs[0]['posting_date_basis'])
  self.assertEqual(freshness_counts(jobs)['date_unknown'],1)
  settings,cv=load()
  settings['catalog_roles']=json.loads((Path(__file__).parents[1]/'role_catalog.json').read_text())['roles']
  scored=evaluate_rule(jobs[0],settings,cv)
  self.assertIsNotNone(scored)
  self.assertEqual(scored['source'],'LinkedIn Job Alerts (user imported)')
 def test_file_missing_is_empty_and_invalid_payload_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'missing.json'
   self.assertEqual(inbox_postings(path),[])
   path.write_text('{"jobs":"not an array"}',encoding='utf-8')
   with self.assertRaisesRegex(ValueError,'Invalid private'):
    inbox_postings(path)

if __name__=='__main__':unittest.main()
