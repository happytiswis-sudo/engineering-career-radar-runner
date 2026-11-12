import json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deep_search import validate_request,dynamic_boards,current_request,eligible_job,exclusion_reasons,default_cities_for_region,DEFAULT_CITIES
class DeepSearchTests(unittest.TestCase):
 def test_all_germany_blank_city_search_adds_national_rotation_without_losing_west(self):
  from datetime import date,timedelta
  day=date(2026,10,28)
  west=default_cities_for_region('west',day)
  country=default_cities_for_region('germany',day)
  next_day=default_cities_for_region('germany',day+timedelta(days=1))
  self.assertEqual(west,DEFAULT_CITIES)
  self.assertTrue(set(DEFAULT_CITIES).issubset(country))
  covered={city for i in range(10) for city in default_cities_for_region('germany',day+timedelta(days=i))}
  self.assertIn('Berlin',covered)
  self.assertGreater(len(country),len(west))
  self.assertNotEqual(country,next_day)
  p=validate_request({'region':'germany','sources':['ba'],'depth':'deep'})
  rows=dynamic_boards(p)
  self.assertEqual(len(rows),220)
  self.assertTrue(any(x['city'] not in DEFAULT_CITIES for x in rows))
 def test_capacity_profile_is_validated_and_controls_deep_query_budget(self):
  maximum=validate_request({'region':'germany','sources':['ba'],'depth':'deep'})
  balanced=validate_request({'region':'germany','sources':['ba'],'depth':'deep','capacity':'balanced'})
  self.assertEqual(maximum['capacity'],'maximum_safe')
  self.assertEqual(balanced['capacity'],'balanced')
  self.assertEqual(len(dynamic_boards(maximum)),220)
  self.assertEqual(len(dynamic_boards(balanced)),120)
  focused=validate_request({'sources':['ba'],'depth':'focused','capacity':'balanced'})
  self.assertEqual(len(dynamic_boards(focused)),40)
  invalid=validate_request({'capacity':'unlimited'})
  self.assertEqual(invalid['capacity'],'maximum_safe')
 def test_deep_all_track_mode_reserves_coverage_for_every_catalogue_track(self):
  catalog=json.loads((Path(__file__).resolve().parents[1]/'role_catalog.json').read_text(encoding='utf8'))['roles']
  expected={r['track'] for r in catalog if r.get('track')}
  profile=validate_request({'region':'germany','sources':['ba'],'depth':'deep','roles':['manufacturing']})
  plan=dynamic_boards(profile)
  actual={b.get('industry_track') for b in plan if b.get('industry_track')}
  self.assertEqual(len(plan),220)
  self.assertEqual(actual,expected)
  self.assertTrue(all(sum(1 for b in plan if b.get('industry_track')==track)>=1 for track in expected))
  self.assertIn('Fertigungsingenieur',{b['query'] for b in plan})
 def test_deep_selected_tracks_are_strict_allow_list(self):
  profile=validate_request({'region':'germany','sources':['ba'],'depth':'deep',
      'tracks':['Project Engineering & Delivery','Airline Ground Support & Flight Operations Administration']})
  plan=dynamic_boards(profile)
  actual={b.get('industry_track') for b in plan if b.get('industry_track')}
  self.assertEqual(actual,set(profile['tracks']))
  self.assertEqual(len(plan),220)
 def test_bespoke_city_role_queries(self):
  p=validate_request({'region':'west','cities':['Esslingen','Hanau'],'roles':['manufacturing'],'sources':['ba','ats'],'depth':'deep'})
  arr=dynamic_boards(p)
  self.assertTrue(any(b['city']=='Hanau' for b in arr))
  self.assertTrue(any(b['query']=='Fertigungsingenieur' for b in arr))
  self.assertGreaterEqual(len(arr),6)
 def test_cap_and_validated_search(self):
  p=validate_request({'cities':['Esslingen']*30,'roles':['engineering']*40,'radius':1200,'min_score':400})
  self.assertEqual(p['radius'],100);self.assertEqual(p['min_score'],95)
  self.assertLessEqual(len(p['cities']),12)
 def test_zero_input_defaults_to_schedule(self):
  with patch.dict('os.environ',{'SEARCH_REQUEST':''}):
   self.assertEqual(current_request(),{})
 def test_entry_junior_default_excludes_content_confirmed_senior_only(self):
  p=validate_request({'sources':['ats']})
  self.assertEqual(p['seniority'],'entry_junior')
  senior={'score':90,'market':{'west':True,'germany':True},'description':'Minimum 7 years experience. People management and direct reports.',
      'seniority_assessment':{'body_senior_evidence':True,'body_junior_evidence':False},'career_track':'Project Engineering & Delivery','published_at':'2026-11-01'}
  junior={'score':65,'market':{'west':True,'germany':True},'seniority_assessment':{'body_senior_evidence':False,'body_junior_evidence':True},'career_track':'Project Engineering & Delivery','published_at':'2026-11-01'}
  self.assertIn('seniority',exclusion_reasons(senior,p))
  title_senior={'score':90,'market':{'west':True,'germany':True},'seniority_assessment':{'title_signal':True,'body_senior_evidence':False,'body_junior_evidence':False},'career_track':'Project Engineering & Delivery','published_at':'2026-11-01'}
  self.assertIn('seniority',exclusion_reasons(title_senior,p))
  junior_title_senior={'score':65,'market':{'west':True,'germany':True},'seniority_assessment':{'title_signal':True,'body_senior_evidence':False,'body_junior_evidence':True},'career_track':'Project Engineering & Delivery','published_at':'2026-11-01'}
  self.assertNotIn('seniority',exclusion_reasons(junior_title_senior,p))
  self.assertNotIn('seniority',exclusion_reasons(junior,p))
  all_levels=validate_request({'seniority':'all','sources':['ats']})
  self.assertNotIn('seniority',exclusion_reasons(senior,all_levels))
 def test_unauthorized_worldwide_must_not_be_shown_as_germany(self):
  profile=validate_request({'region':'west','min_score':45})
  job={'score':92,'market':{'west':False,'germany':False},'hiring_support':{}}
  self.assertFalse(eligible_job(job,profile))
 def test_explicit_visa_support_filter(self):
  p=validate_request({'region':'world','support':'visa'})
  unknown={'score':82,'market':{},'hiring_support':{'visa':{'status':'not_stated'}}}
  explicit={'score':82,'market':{},'hiring_support':{'visa':{'status':'explicit'}}}
  self.assertFalse(eligible_job(unknown,p));self.assertTrue(eligible_job(explicit,p))
 def test_visa_not_inferred_from_blue_card_mention(self):
  p=validate_request({'region':'world','support':'visa'})
  j={'score':90,'market':{},'hiring_support':{'blue_card':{'status':'mentioned'},'visa':{'status':'not_stated'}}}
  self.assertFalse(eligible_job(j,p))
 def test_unknown_sources_discarded(self):
  p=validate_request({'sources':['ba','linkedin-scraper','google-maps-scraper','ats']})
  self.assertEqual(p['sources'],['ba','ats'])
if __name__=='__main__':unittest.main()
