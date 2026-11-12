import json
import unittest
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from discovery_quality import (freshness_counts, review_candidates,
    rotating_airport_boards, load_prior_job_keys, load_prior_query_metrics)
from novelty import job_key
from public_source_adapters import ROLE_WORDS
from radar import evaluate_rule

ROOT=Path(__file__).resolve().parents[1]

class FreshAirportDiscoveryTests(unittest.TestCase):
 def test_previous_ba_feedback_keeps_all_254_samples(self):
  import tempfile
  with tempfile.TemporaryDirectory() as folder:
   filename=Path(folder)/'prior.json'
   metrics=[{'city':'Frankfurt','query':'engineering '+str(i),
             'unseen_recent_cv_matches':int(i%8==0)} for i in range(254)]
   filename.write_text(json.dumps({'source_query_metrics':metrics}),encoding='utf8')
   loaded=load_prior_query_metrics(filename)
  self.assertEqual(len(loaded),254)
  self.assertEqual(loaded[-1]['query'],'engineering 253')

 def test_dated_source_counts_are_cumulative_and_unknown_remains_unknown(self):
  now=datetime.now(timezone.utc)
  jobs=[{'published_at':(now-timedelta(hours=h)).isoformat()} for h in (5,70,250,1000)]
  jobs.append({'published_at':''})
  counts=freshness_counts(jobs)
  self.assertEqual(counts,{'within_24h':1,'within_7d':2,'within_30d':3,
                           'older_than_30d':1,'date_unknown':1})
 def test_airport_rotation_is_distinct_within_daily_budget(self):
  day_a=rotating_airport_boards([],when=date(2026,10,27))
  day_b=rotating_airport_boards([],when=date(2026,10,28))
  keys=lambda rows:{(x['city'],x['query']) for x in rows}
  self.assertEqual(len(day_a),24)
  self.assertEqual(len(keys(day_a)),len(day_a))
  self.assertNotEqual(keys(day_a),keys(day_b))
  self.assertTrue(all(r['type']=='bundesagentur' and r['pages']==2 for r in day_a))
 def test_rotation_avoids_existing_fixed_queries(self):
  first=rotating_airport_boards([],when=date(2026,10,27))[0]
  rows=rotating_airport_boards([first],when=date(2026,10,27))
  self.assertNotIn((first['city'],first['query']),{(r['city'],r['query']) for r in rows})
 def test_new_recent_employers_get_ai_reviews_without_changing_shortlist(self):
  now=datetime.now(timezone.utc)
  today=now.isoformat();old=(now-timedelta(days=70)).isoformat()
  postings=[
   {'title':'Test Engineer','company':'Incumbent','url':'https://jobs.example/old','published_at':old,'score':95,'market':{'west':True}},
   {'title':'Ramp Coordinator','company':'Airport A','url':'https://jobs.example/new','published_at':today,'score':69,'market':{'west':False}},
   {'title':'Cargo Coordinator','company':'Airport A','url':'https://jobs.example/cargo','published_at':today,'score':85,'market':{'west':False}},
   {'title':'Ground Support Technician','company':'Airport B','url':'https://jobs.example/gse','published_at':today,'score':70,'market':{'west':False}}
  ]
  old_keys={job_key(postings[0])}
  ranked=review_candidates(postings,2,old_keys)
  self.assertEqual(len(ranked),2)
  self.assertEqual(len({x['company'] for x in ranked}),2)
  self.assertTrue(all(job_key(x) not in old_keys for x in ranked))
  self.assertEqual(len(postings),4,'Ranking must never delete previously found postings')
 def test_unavailable_history_never_claims_new(self):
  jobs=[{'title':'Test','company':'Factory','url':'https://jobs.example/a',
         'published_at':'2026-01-01','score':80}]
  self.assertEqual(review_candidates(jobs,1,None),jobs)
  with patch('pathlib.Path.read_text',side_effect=OSError('missing')):
   self.assertIsNone(load_prior_job_keys('/private/unavailable.json'))
 def test_airport_titles_pass_first_stage_not_unrelated(self):
  for title in ['Ramp Coordinator','Cargo Warehouse Agent','Baggage Handling Technician',
                'Flughafen Vorfeldmitarbeiter','Airside Operations Coordinator']:
   self.assertRegex(title,ROLE_WORDS)
  self.assertNotRegex('Restaurant Chef',ROLE_WORDS)
 def test_uncatalogued_cargo_role_still_requires_cv_skill_evidence(self):
  settings={'catalog_roles':[],'role_patterns':[],
    'skills':[{'label':'CAD','aliases':['solidworks'],'weight':4},
              {'label':'Coordination','aliases':['project coordination'],'weight':4}],
    'candidate_education':{'highest_completed':'bachelor'},'west_germany':{}}
  advert='Cargo operations support using solidworks and project coordination. '+('Safety planning documented. '*8)
  j={'title':'Cargo Shift Assistant','description':advert,'location':'London, UK',
     'company':'Cargo A','url':'https://careers.example/job-1','source':'Public employer'}
  self.assertIsNotNone(evaluate_rule(dict(j),settings,'Solidworks, project coordination'))
  self.assertIsNone(evaluate_rule(dict(j),settings,'Solidworks only'))
 def test_verified_employer_links_are_leads_not_fabricated_vacancies(self):
  payload=json.loads((ROOT/'airport_employer_watchlist.json').read_text(encoding='utf8'))
  self.assertGreaterEqual(len(payload['employers']),8)
  for x in payload['employers']:
   self.assertTrue(x['careers_url'].startswith('https://'))
   self.assertEqual(x['source_status'],'official_careers_portal')
   self.assertNotIn('job_count',x)

if __name__=='__main__':unittest.main()
