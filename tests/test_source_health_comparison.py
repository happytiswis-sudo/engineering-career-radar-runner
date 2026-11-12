import unittest
from source_health import comparable_source_health

class SourceTrendTests(unittest.TestCase):
 def test_mismatched_search_not_comparable(self):
  a={'search_mode':'scheduled','search_request':{},'source_metrics':{'workday':{'returned':100}}}
  b={'search_mode':'on-demand','search_request':{'region':'west'},'source_metrics':{'workday':{'returned':0}}}
  self.assertFalse(comparable_source_health(a,b)['comparable'])
 def test_significant_drop_with_same_search(self):
  a={'search_mode':'scheduled','search_request':{},'run_id':123,'source_metrics':{
     'workday':{'returned':90,'succeeded':8},'nomado24':{'returned':3,'succeeded':1}}}
  b={'search_mode':'scheduled','search_request':{},'source_metrics':{
     'workday':{'returned':10,'succeeded':2},'nomado24':{'returned':0,'succeeded':1}}}
  report=comparable_source_health(a,b)
  self.assertTrue(report['comparable'])
  self.assertEqual(len(report['alerts']),1)
  self.assertEqual(report['alerts'][0]['source'],'workday')
 def test_zero_success_warning_even_if_zero_old_postings(self):
  a={'search_mode':'scheduled','source_metrics':{'provider':{'returned':0,'succeeded':5}}}
  b={'search_mode':'scheduled','source_metrics':{'provider':{'returned':0,'succeeded':0}}}
  self.assertEqual(comparable_source_health(a,b)['alerts'][0]['signal'],'source_unavailable')
 def test_no_claim_of_outage_from_small_sample(self):
  a={'search_mode':'scheduled','source_metrics':{'provider':{'returned':4,'succeeded':1}}}
  b={'search_mode':'scheduled','source_metrics':{'provider':{'returned':0,'succeeded':0}}}
  self.assertEqual(comparable_source_health(a,b)['alerts'],[])

if __name__=='__main__':unittest.main()
