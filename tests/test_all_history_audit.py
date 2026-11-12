import unittest
from audit_all_history import analyze

class CompleteHistoryAuditTests(unittest.TestCase):
 def test_all_history_unique_recency_and_missing_archives(self):
  rows={'runs':[
   {'run_id':'11111111','published_at':'2026-10-20T09:00:00Z','archive_file':'history/run-11111111.json'},
   {'run_id':'22222222','published_at':'2026-10-27T09:00:00Z','archive_file':'history/run-22222222.json'},
   {'run_id':'33333333','published_at':'2026-10-27T10:00:00Z','archive_file':'history/run-33333333.json'}
  ]}
  one={'title':'Airport Cargo Operator','company':'Cargo A','url':'https://example.org/1',
       'source':'Bundesagentur','career_track':'Air Cargo','published_at':'2026-10-20',
       'remote':False,'score':65}
  two={**one,'published_at':'2026-10-27','score':72}
  new={'title':'Quality Technician','company':'Factory B','url':'https://example.org/2',
       'source':'Greenhouse','career_track':'Quality','published_at':'2026-10-26','score':62}
  index={
   'history/run-11111111.json':{'run_id':'11111111','generated_at':'2026-10-20T09:00:00Z','jobs':[one]},
   'history/run-22222222.json':{'run_id':'22222222','generated_at':'2026-10-27T09:00:00Z','jobs':[two,new]}
  }
  def loader(path):
   if path not in index:raise OSError('Not retrievable')
   return index[path]
  out=analyze(rows,loader)
  self.assertEqual(out['runs_available_in_index'],3)
  self.assertEqual(out['runs_analyzed'],2)
  self.assertEqual(out['public_job_appearances'],3)
  self.assertEqual(out['distinct_public_job_identities'],2)
  self.assertEqual(out['source_statistics']['Bundesagentur']['first_seen_unique'],1)
  self.assertEqual(out['source_statistics']['Greenhouse']['recent_7d_first_seen'],1)
  self.assertEqual(len(out['missing_archives']),1)
 def test_reject_corrupt_run_id(self):
  rows={'runs':[{'run_id':'10000000','archive_file':'history/run-10000000.json'}]}
  out=analyze(rows,lambda p:{'run_id':'99999999','jobs':[]})
  self.assertEqual(out['runs_analyzed'],0)
  self.assertEqual(len(out['missing_archives']),1)

if __name__=='__main__':unittest.main()
