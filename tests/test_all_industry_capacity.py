import json,unittest
from datetime import date
from pathlib import Path
from industry_search import (TRACK_TERMS,industry_boards,career_track_queries,
    allocate_track_queries,allocate_historical_boards,rotating_workday_terms,rotating_nomado_queries)
from deep_search import validate_request,dynamic_boards

class IndustryCapacityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=json.loads(Path('role_catalog.json').read_text(encoding='utf8'))['roles']
 def test_every_existing_catalog_track_gets_real_query(self):
  current={x['track'] for x in self.catalog}
  self.assertEqual(len(current),34)
  self.assertTrue(current.issubset(TRACK_TERMS))
  boards=industry_boards([],self.catalog,when=date(2026,10,27),limit=44)
  self.assertEqual(len(boards),44)
  self.assertEqual({b['industry_track'] for b in boards},current)
  self.assertEqual(len({(b['city'],b['query']) for b in boards}),44)
  self.assertTrue(all(b['pages']==2 and b['type']=='bundesagentur' for b in boards))
 def test_undercovered_tracks_include_broader_german_search_synonyms(self):
  self.assertIn('Rechenzentrum Instandhaltung',TRACK_TERMS['Data Centers, Telecom & Critical Facilities'])
  self.assertIn('Krankenhaustechnik',TRACK_TERMS['Healthcare Facilities & Medical Logistics'])
  self.assertIn('TGA Projektkoordinator',TRACK_TERMS['Construction, Property & Building Services'])
  self.assertIn('Kläranlagen Betrieb',TRACK_TERMS['Energy, Water & Public Utilities Operations'])
  self.assertIn('Gepäcksystem Techniker',TRACK_TERMS['Airport Technical Systems & Infrastructure'])
  self.assertIn('Luftfracht Logistikplaner',TRACK_TERMS['Airport Cargo, Freight & Logistics'])
  self.assertIn('Lebensmitteltechniker',TRACK_TERMS['Food, Packaging & Consumer Production'])

 def test_track_title_sampling_covers_entire_long_catalog_track(self):
  many=[{'track':'Wide Industrial Track','title':'Specialist Title '+str(i),'priority':'Medium'}
        for i in range(24)]
  result=career_track_queries(many)['Wide Industrial Track']
  selected=[x for x in result if x.startswith('Specialist Title ')]
  self.assertEqual(len(selected),10)
  self.assertIn('Specialist Title 23',selected)
  self.assertGreater(max(int(x.rsplit(' ',1)[-1]) for x in selected),15)

 def test_deep_catalogue_query_map_contains_every_title_and_track_alias(self):
  alias_catalog=[
   {'track':'Alias Track','title':'Primary Engineer','aliases':['German Ingenieur','Technical Specialist']},
   {'track':'Alias Track','title':'Junior Engineer','aliases':['Berufseinsteiger Ingenieur']}
  ]
  result=career_track_queries(alias_catalog,include_all_titles=True)
  self.assertEqual(set(result),{'Alias Track'})
  self.assertTrue({'Primary Engineer','German Ingenieur','Technical Specialist',
                   'Junior Engineer','Berufseinsteiger Ingenieur'}.issubset(set(result['Alias Track'])))

 def test_track_allocator_reserves_each_track_before_fair_extras(self):
  catalog=[
   {'track':'Track A','title':'A Engineer'},
   {'track':'Track B','title':'B Technician'},
   {'track':'Track C','title':'C Coordinator'}
  ]
  result=allocate_track_queries(catalog,cap=8,when=date(2026,11,8))
  self.assertEqual(len(result),8)
  self.assertEqual({x['industry_track'] for x in result[:3]},
                   {'Track A','Track B','Track C'})
  counts={track:sum(x['industry_track']==track for x in result) for track in ('Track A','Track B','Track C')}
  self.assertLessEqual(max(counts.values())-min(counts.values()),1)

 def test_track_allocator_respects_selected_only_and_capacity(self):
  catalog=[
   {'track':'Track A','title':'A Engineer'},
   {'track':'Track B','title':'B Technician'},
   {'track':'Track C','title':'C Coordinator'}
  ]
  selected=allocate_track_queries(catalog,cap=10,selected=['Track B'],when=date(2026,11,8))
  self.assertEqual({x['industry_track'] for x in selected},{'Track B'})
  tiny=allocate_track_queries(catalog,cap=2,when=date(2026,11,8))
  self.assertEqual(len(tiny),2)
  self.assertEqual(len({x['industry_track'] for x in tiny}),2)

 def test_maximum_safe_rotation_expands_beyond_the_balanced_44_tasks(self):
  result=industry_boards([],self.catalog,when=date(2026,10,27),limit=220)
  self.assertEqual(len(result),220)
  self.assertEqual({x['industry_track'] for x in result},
                   {x['track'] for x in self.catalog})
  self.assertGreater(len({(x['city'],x['query']) for x in result}),180)
 def test_daily_rotation_changes_actual_term_city_pairs(self):
  a=industry_boards([],self.catalog,when=date(2026,10,27),limit=44)
  b=industry_boards([],self.catalog,when=date(2026,10,28),limit=44)
  old={(x['city'],x['query']) for x in a}
  self.assertGreater(len(old-{(x['city'],x['query']) for x in b}),20)
 def test_new_user_track_is_searched_without_developer_update(self):
  modified=self.catalog+[{'track':'New User-Defined Sector','title':'Industrial Hydroponics Technician','priority':'Medium'}]
  result=industry_boards([],modified,when=date(2026,10,27),limit=44)
  self.assertTrue(any(x['industry_track']=='New User-Defined Sector' and
      x['query']=='Industrial Hydroponics Technician' for x in result))
 def test_prior_recent_success_gets_bounded_reuse(self):
  orig=industry_boards([],self.catalog,when=date(2026,10,27))
  item=orig[0]
  prior=[{'industry_track':item['industry_track'],'city':item['city'],'query':item['query'],
          'unseen_recent_cv_matches':3,'cv_matches':5}]
  result=industry_boards([],self.catalog,prior_metrics=prior,when=date(2026,10,28),limit=44)
  self.assertTrue(any(x['feedback_reused'] for x in result))
  self.assertLessEqual(sum(x['feedback_reused'] for x in result),6)
 def test_historical_ats_all_seen_in_two_day_rotation(self):
  pool=[{'type':'greenhouse','slug':'employer'+str(i)} for i in range(420)]
  a=allocate_historical_boards(pool,when=date(2026,10,27),cap=360)
  b=allocate_historical_boards(pool,when=date(2026,10,28),cap=360)
  self.assertEqual(len(a),360)
  self.assertEqual(len(b),360)
  self.assertEqual(len({x['slug'] for x in a+b}),420)
 def test_confirmed_404_historical_boards_are_cooled_then_return(self):
  from datetime import datetime,timezone
  pool=[{'type':'greenhouse','slug':'employer'+str(i)} for i in range(12)]
  failures={'greenhouse|employer0':{
      'type':'greenhouse','slug':'employer0','reason':'http_404',
      'retry_after':'2026-11-26T00:00:00+00:00'}}
  current=datetime(2026,10,30,tzinfo=timezone.utc)
  selected=allocate_historical_boards(pool,when=date(2026,10,30),cap=12,
      prior_failures=failures,now=current)
  self.assertEqual(len(selected),11)
  self.assertNotIn('employer0',{x['slug'] for x in selected})
  after=datetime(2026,11,27,tzinfo=timezone.utc)
  restored=allocate_historical_boards(pool,when=date(2026,11,27),cap=12,
      prior_failures=failures,now=after)
  self.assertEqual(len(restored),12)

 def test_rate_limited_historical_boards_are_cooled_then_return(self):
  from datetime import datetime,timezone
  pool=[{'type':'greenhouse','slug':'employer'+str(i)} for i in range(12)]
  failures={'greenhouse|employer0':{
      'type':'greenhouse','slug':'employer0','reason':'http_429',
      'retry_after':'2026-11-03T12:00:00+00:00'}}
  current=datetime(2026,11,3,10,0,tzinfo=timezone.utc)
  selected=allocate_historical_boards(pool,when=date(2026,11,3),cap=12,
      prior_failures=failures,now=current)
  self.assertEqual(len(selected),11)
  self.assertNotIn('employer0',{x['slug'] for x in selected})
  after=datetime(2026,11,3,12,1,tzinfo=timezone.utc)
  restored=allocate_historical_boards(pool,when=date(2026,11,3),cap=12,
      prior_failures=failures,now=after)
  self.assertEqual(len(restored),12)
 def test_attractive_employer_is_pinned_without_excluding_discovery(self):
  pool=[{'type':'lever','slug':'company'+str(i)} for i in range(420)]
  prior=[{'type':'lever','slug':'company419','unseen_recent_cv_matches':5,'cv_matches':8}]
  planned=allocate_historical_boards(pool,prior,when=date(2026,10,27),cap=360)
  self.assertEqual(planned[0]['slug'],'company419')
  self.assertEqual(len({x['slug'] for x in planned}),360)
 def test_on_demand_track_generates_relevant_first_search(self):
  profile=validate_request({'region':'germany','sources':['ba'],'tracks':['Airport Cargo, Freight & Logistics'],
     'depth':'focused'})
  plan=dynamic_boards(profile)
  self.assertEqual(len(plan),60)
  self.assertNotIn('Ingenieur',[x['query'] for x in plan[:15]])
  self.assertTrue(any(x['query'] in TRACK_TERMS['Airport Cargo, Freight & Logistics']
          for x in plan[:15]))
 def test_nomado_queries_rotate_technical_and_new_industry_topics(self):
  old=rotating_nomado_queries(date(2026,10,27))
  new=rotating_nomado_queries(date(2026,10,28))
  self.assertEqual(len(old),6)
  self.assertEqual(len(set(old)),6)
  self.assertEqual(old[:3],new[:3])
  self.assertNotEqual(old[3:],new[3:])
 def test_lever_public_creation_is_usable_but_not_called_publication(self):
  from radar import fetch_board
  from unittest.mock import patch
  board={'type':'lever','slug':'test-lever','company':'Example'}
  posting={'text':'Facility Maintenance Coordinator',
      'categories':{'location':'Frankfurt'},'hostedUrl':'https://jobs.lever.co/test-lever/123',
      'descriptionPlain':'Technical maintenance facility project support',
      'createdAt':1793000000000,'workplaceType':'hybrid'}
  with patch('radar.read_json_url',return_value=[posting]):
   jobs=fetch_board(board)
  self.assertEqual(len(jobs),1)
  self.assertTrue(jobs[0]['published_at'].startswith('2026-'))
  self.assertEqual(jobs[0]['posting_date_basis'],'lever_created_at_not_publish_date')
  self.assertFalse(jobs[0]['remote'])
 def test_workday_keywords_differ_day_to_day_with_same_budget(self):
  board={'slug':'airbus'}
  one=rotating_workday_terms(board,date(2026,10,27))
  two=rotating_workday_terms(board,date(2026,10,28))
  self.assertEqual(len(one),8)
  self.assertEqual(len(two),8)
  self.assertEqual(len(set(one)),8)
  self.assertEqual(one[:5],two[:5])
  self.assertNotEqual(one[5:],two[5:])

if __name__=='__main__':unittest.main()
