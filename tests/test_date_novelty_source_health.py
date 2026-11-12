import json
import os
import unittest
from unittest.mock import patch
from date_evidence import jsonld_jobposting_date,public_pinpoint_date
from source_novelty_summary import shortlist_novelty_by_source,categorize_failure,classify_board_failures
from public_source_adapters import pinpoint,workday

class DateAndNoveltyTests(unittest.TestCase):
 def test_real_jsonld_posting_date_not_other_schema(self):
  page='<script type="application/ld+json">'+json.dumps({'@graph':[
   {'@type':'Organization','datePosted':'2026-01-01'},
   {'@type':'JobPosting','datePosted':'2026-10-27'}]})+'</script>'
  self.assertEqual(jsonld_jobposting_date(page),'2026-10-27')
  self.assertEqual(jsonld_jobposting_date('<script type="application/ld+json">{"@type":"JobPosting","datePosted":"invalid"}</script>'),'')
  self.assertEqual(jsonld_jobposting_date('<time datetime="2026-10-27">Today</time>'),'')
 def test_pinpoint_page_check_does_not_contact_other_hosts(self):
  with patch('date_evidence.urlopen') as network:
   self.assertEqual(public_pinpoint_date('https://notpinpoint.example/postings/7','company.pinpointhq.com'),'')
   network.assert_not_called()
 def test_pinpoint_verified_date_and_unknown_fallback(self):
  raw={'data':[{'id':'1','title':'Quality Engineer','url':'https://company.pinpointhq.com/en/postings/1',
               'location':{'name':'Berlin'}},
               {'id':'2','title':'Ground Operations Technician','url':'https://company.pinpointhq.com/en/postings/2',
                'location':{'name':'Hamburg'}}]}
  with patch.dict(os.environ,{'PINPOINT_DATE_VERIFY_LIMIT':'2'}):
   with patch('public_source_adapters.request_json',return_value=raw):
    with patch('date_evidence.public_pinpoint_date',side_effect=['2026-10-27','']):
     jobs=pinpoint({'slug':'company','company':'Company'})
  self.assertEqual(len(jobs),2)
  self.assertEqual(jobs[0]['published_at'],'2026-10-27')
  self.assertEqual(jobs[0]['posting_date_basis'],'pinpoint_employer_jobposting_jsonld_datePosted')
  self.assertEqual(jobs[1]['published_at'],'')
  self.assertEqual(jobs[1]['posting_date_basis'],'pinpoint_public_feed_no_publication_date')
 def test_workday_date_basis_is_not_claimed_first_publication(self):
  board={'host':'foo.wd3.myworkdayjobs.com','site':'External','company':'Factory'}
  listing={'total':1,'jobPostings':[{'title':'Quality Engineer','locationsText':'Berlin',
     'postedOn':'Posted 4 Days Ago','externalPath':'/job/Berlin/Quality-Engineer_10'}]}
  detail={'jobPostingInfo':{'location':'Berlin','startDate':'2026-10-20'}}
  with patch('public_source_adapters.request_json',side_effect=[listing,detail,
    {'total':0,'jobPostings':[]}] * 4):
   jobs=workday(board)
  self.assertEqual(jobs[0]['published_at'],'2026-10-20')
  self.assertEqual(jobs[0]['posting_date_basis'],
      'workday_employer_detail_start_date_not_verified_first_publication')
 def test_novelty_by_source_counts_only_final_shortlist_with_dated_evidence(self):
  jobs=[{'source':'Workday','novelty_status':'new_to_history','freshness':{'age_days':1}},
        {'source':'Workday','novelty_status':'previously_seen','freshness':{'age_days':2}},
        {'source':'Pinpoint','novelty_status':'new_to_history','freshness':{'age_days':None}}]
  result=shortlist_novelty_by_source(jobs)
  self.assertEqual(result['Workday']['new_within_7d'],1)
  self.assertEqual(result['Workday']['previously_seen'],1)
  self.assertEqual(result['Pinpoint']['new_unknown_date'],1)
  self.assertEqual(sum(v['new_to_history'] for v in result.values()),2)
 def test_individual_failed_board_categories(self):
  rows=classify_board_failures([{'source':'greenhouse','board':'a','error':'HTTP 404'},
    {'source':'ashby','board':'b','error':'HTTP 403'},
    {'source':'lever','board':'c','error':'TimeoutError'}])
  self.assertEqual([x['category'] for x in rows],['board_not_found','access_blocked','timeout'])

if __name__=='__main__':unittest.main()
