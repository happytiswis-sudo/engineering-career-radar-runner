"""Regression tests for Oct 28 AI performance and malformed model responses."""
import threading
import time
import unittest
from unittest.mock import patch
from radar import assess_queue_parallel,parse_structured_assessment

class AIEnrichmentTests(unittest.TestCase):
 def test_fenced_json_and_prose_wrapped_json(self):
  data='Notice: {"debug":"metadata"}\n```json\n{"fit_score":82,"recommendation":"Apply","summary":"Relevant"}\n```'
  result=parse_structured_assessment(data)
  self.assertEqual(result['fit_score'],82)
  self.assertEqual(result['recommendation'],'Apply')
  self.assertEqual(parse_structured_assessment([{'type':'text','text':data}]),result)
  with self.assertRaisesRegex(ValueError,'JSON'):
   parse_structured_assessment('not valid at all')
 def test_two_workers_preserve_every_job_and_scores(self):
  jobs=[{'title':str(i),'rule_score':75,'score':75} for i in range(5)]
  guard=threading.Lock();running=0;peak=0
  def fake(job,cv,settings,key,provider,timeout_seconds=55):
   nonlocal running,peak
   with guard:
    running+=1;peak=max(peak,running)
   time.sleep(.015)
   with guard:running-=1
   return {'score':88,'recommendation':'Apply'}
  with patch('radar.ai_assess',side_effect=fake):
   results=assess_queue_parallel(jobs,'cv',{},[{'name':'Provider','key':'x'}],time.monotonic()+5,workers=2)
  self.assertEqual(len(results),5)
  self.assertTrue(all(result[1]['score']==88 for result in results))
  self.assertEqual(peak,2)
  self.assertEqual([result[0]['title'] for result in results],[str(i) for i in range(5)])
  self.assertEqual([job['score'] for job in jobs],[75]*5)
 def test_invalid_primary_can_use_valid_backup_without_removing_jobs(self):
  jobs=[{'title':'A','rule_score':60,'score':60},{'title':'B','rule_score':75,'score':75}]
  providers=[{'name':'Malformed','key':'x'},{'name':'Backup','key':'y'}]
  def fake(job,cv,settings,key,provider,timeout_seconds=55):
   if provider['name']=='Malformed':raise ValueError('AI did not return valid assessment JSON')
   return {'score':80,'recommendation':'Apply'}
  with patch('radar.ai_assess',side_effect=fake):
   results=assess_queue_parallel(jobs,'cv',{},providers,time.monotonic()+5)
  self.assertEqual(len(results),2)
  self.assertTrue(all(result[2]=='Backup' for result in results))
  self.assertEqual(results[0][3][0][1],'invalid_assessment_json')
  self.assertEqual(results[1][3][0][1],'success')
  self.assertEqual([job['score'] for job in jobs],[60,75])

if __name__=='__main__':unittest.main()
