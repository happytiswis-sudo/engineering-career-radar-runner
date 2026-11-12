import unittest
from unittest.mock import patch
from deep_search import validate_request, exclusion_reasons, eligible_job
from radar import fetch_board

class SearchLossAuditTests(unittest.TestCase):
 def test_multicausal_rejections_report_every_blocker(self):
  p=validate_request({'region':'west','min_score':65,'support':'international','freshness':'30'})
  j={'title':'Manufacturing Engineer','score':54,
   'market':{'germany':True,'west':False},'hiring_support':{'international':{'status':'not_stated'}},
   'published_at':'2026-06-15','qualification':{'status':'eligible'}}
  reasons=exclusion_reasons(j,p)
  self.assertEqual(reasons,['location','score','freshness','support'])
  self.assertFalse(eligible_job(j,p))
 def test_overqualified_transferability_can_pass_score(self):
  p=validate_request({'region':'germany','min_score':65,'support':'visa_possible','freshness':'all'})
  j={'score':52,'market':{'west':True,'germany':True},
   'hiring_support':{},'qualification':{'status':'eligible'},
   'capability':{'open_to_junior_roles':True,'capability_score':82}}
  self.assertEqual(exclusion_reasons(j,p),[])
  self.assertTrue(eligible_job(j,p))
 def test_explicit_international_only_rejects_unknown_evidence(self):
  p=validate_request({'region':'world','min_score':0,'support':'international'})
  j={'score':85,'market':{},'hiring_support':{'international':{'status':'not_stated'}}}
  self.assertEqual(exclusion_reasons(j,p),['support'])
  p['support']='visa_possible'
  self.assertEqual(exclusion_reasons(j,p),[])
 def test_uk_no_key_feed_parses_verified_public_shape(self):
  sample={'data':[{'company_name':'Test Factory','title':'Manufacturing Engineer',
    'location':'Manchester','url':'https://www.arbeitnow.co.uk/jobs/test-factory/engineering-123',
    'description':'Manufacturing operations and test support','created_at':1793000000,
    'remote':False}]}
  with patch('radar.read_json_url',side_effect=[sample,{'data':[]}]) as mock:
   results=fetch_board({'type':'arbeitnow_uk','slug':'uk-public','company':'Arbeitnow UK'})
  self.assertEqual(len(results),1)
  self.assertEqual(results[0]['source'],'Arbeitnow UK')
  self.assertFalse(results[0].get('visa_sponsorship_feed'))
  self.assertTrue(mock.call_args_list[0].args[0].startswith('https://www.arbeitnow.co.uk/api/job-board-api?page=1'))
 def test_audit_survives_history_archive(self):
  from search_history import create_snapshot
  out={'generated_at':'2026-10-26T12:00:00+00:00','jobs':[],
    'discovery_audit':{'unique_collected':900,'before_user_filters':60,'after_user_filters':0,
    'rejection_counts':{'support':60}},'source_failure_counts':{'workday':2}}
  summary,snapshot=create_snapshot(out,40338598825,event='push')
  self.assertEqual(summary['event'],'push')
  self.assertEqual(snapshot['discovery_audit']['rejection_counts']['support'],60)
  self.assertEqual(snapshot['source_failure_counts']['workday'],2)

if __name__=='__main__': unittest.main()
