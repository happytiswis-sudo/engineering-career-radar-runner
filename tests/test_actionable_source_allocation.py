import unittest
from datetime import date,datetime,timedelta,timezone
from unittest.mock import patch
from urllib.parse import parse_qs,urlparse
from discovery_quality import rotating_airport_boards,review_candidates
from public_source_adapters import himalayas,workday

class FreshSourceAllocationTests(unittest.TestCase):
 def test_himalayas_queries_worldwide_and_germany_with_less_broad_paging(self):
  postings={'jobs':[{'title':'Airport Cargo Coordinator','companyName':'Test Airport',
     'applicationLink':'https://himalayas.app/companies/test/jobs/airport-cargo',
     'guid':'https://himalayas.app/companies/test/jobs/airport-cargo',
     'locationRestrictions':[],'pubDate':1793000000}],'nextCursor':None}
  with patch('public_source_adapters.request_json',return_value=postings) as get,patch('public_source_adapters.time.sleep'):
   rows=himalayas({'type':'himalayas','company':'Himalayas','slug':'remote'})
  self.assertEqual(len(rows),1)
  urls=[c.args[0] for c in get.call_args_list]
  self.assertLessEqual(len(urls),12)
  self.assertTrue(any('/jobs/api/search?' in url and 'worldwide=true' in url for url in urls))
  self.assertTrue(any('/jobs/api/search?' in url and 'country=DE' in url for url in urls))
  self.assertEqual(rows[0]['url'],postings['jobs'][0]['applicationLink'])
 def test_workday_real_detail_date_and_requirement_are_preserved(self):
  board={'type':'workday','slug':'external','site':'Jobs','host':'factory.wd3.myworkdayjobs.com','company':'Airport Supplier'}
  sample={'total':1,'jobPostings':[{'title':'Airport Equipment Maintenance Technician',
         'externalPath':'/job/Frankfurt/Technician_JR101','locationsText':'Frankfurt','postedOn':'Posted 3 Days Ago'}]}
  detail={'jobPostingInfo':{'location':'Frankfurt am Main','jobDescription':'Aerospace and maintenance testing.',
       'startDate':'2026-10-22','endDate':'2026-11-30','jobReqId':'JR101'}}
  with patch('public_source_adapters.request_json',side_effect=[sample,detail]+[{'total':0,'jobPostings':[]}]*7):
   rows=workday(board)
  self.assertEqual(len(rows),1)
  self.assertEqual(rows[0]['published_at'],'2026-10-22')
  self.assertEqual(rows[0]['expires_at'],'2026-11-30')
  self.assertEqual(rows[0]['employer_posting_id'],'JR101')
 def test_workday_deep_search_extra_pages_are_bounded(self):
  board={'type':'workday','slug':'external','site':'Jobs',
         'host':'factory.wd3.myworkdayjobs.com','company':'Airport Supplier',
         'workday_extra_page_budget':1,
         'queries':['Quality Engineer '+str(i) for i in range(13)]}
  requests=[]
  def respond(url,method='GET',body=None,**kwargs):
   if url.endswith('/jobs'):
    offset=int((body or {}).get('offset') or 0)
    requests.append(offset)
    listings=[{'title':'Quality Engineer','locationsText':'Frankfurt',
       'externalPath':f'/job/Frankfurt/Quality-Engineer_{offset+i}'}
       for i in range(20)]
    return {'total':45,'jobPostings':listings}
   return {'jobPostingInfo':{'location':'Frankfurt','jobDescription':'ISO and supplier quality'}}
  with patch('public_source_adapters.request_json',side_effect=respond):
   with patch('public_source_adapters.time.sleep'):
    jobs=workday(board)
  self.assertEqual(len(jobs),40)
  self.assertEqual(len([x for x in requests if x==0]),13)
  self.assertEqual(len([x for x in requests if x==20]),1)
  self.assertEqual(board['workday_page_stats']['extra_pages_attempted'],1)
  self.assertEqual(board['workday_page_stats']['extra_pages_succeeded'],1)
  self.assertEqual(board['workday_page_stats']['extra_page_budget'],1)
 def test_airport_query_feedback_exploits_only_recent_productive_queries(self):
  baseline=rotating_airport_boards([],when=date(2026,10,27),limit=24)
  winner=baseline[0];loser=baseline[1]
  metrics=[
   {'city':winner['city'],'query':winner['query'],'rotating_search':True,
    'unseen_recent_cv_matches':2,'cv_matches':3},
   {'city':loser['city'],'query':loser['query'],'rotating_search':True,
    'unseen_recent_cv_matches':0,'cv_matches':0}
  ]
  nextday=rotating_airport_boards([],when=date(2026,10,28),limit=24,prior_metrics=metrics)
  self.assertEqual((nextday[0]['city'],nextday[0]['query']),(winner['city'],winner['query']))
  self.assertNotIn((loser['city'],loser['query']),
     {(row['city'],row['query']) for row in nextday})
  self.assertEqual(len(nextday),24)
 def test_ai_respects_recent_relevance_but_keeps_restricted_in_catalog(self):
  now=datetime.now(timezone.utc)
  new=now.isoformat()
  j=lambda name,title,restriction,score:{'title':title,'company':name,
   'url':'https://jobs.example/'+name,'published_at':new,'score':score,
   'remote':True,'remote_location_restriction':restriction,'market':{}}
  posts=[j('us','Systems Engineer',['United States'],92),
         j('world','Airport Technical Coordinator',[],67),
         j('de','Quality Engineer',['Germany'],69)]
  chosen=review_candidates(posts,1,prior_keys=set())
  self.assertEqual(chosen[0]['company'],'world')
  self.assertEqual(len(posts),3)

if __name__=='__main__':unittest.main()
