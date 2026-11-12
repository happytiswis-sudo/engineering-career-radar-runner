import unittest
from pathlib import Path
from unittest.mock import patch
from local_companies import (
    choose_towns,overpass_query,website_from,discover_local_companies,
    MAX_CITIES
)
ROOT=Path(__file__).resolve().parents[1]

class OSMUpgradeTests(unittest.TestCase):
 def test_blank_cities_sample_small_german_towns(self):
  towns=choose_towns([])
  self.assertEqual(len(towns),MAX_CITIES)
  self.assertIn('Esslingen am Neckar',towns)
  self.assertIn('Hanau',towns)
 def test_aliases_and_duplicates(self):
  self.assertEqual(choose_towns(['Esslingen','Esslingen am Neckar','Frankfurt']),
                   ['Esslingen am Neckar','Frankfurt am Main'])
 def test_query_is_bounded_to_german_city_and_named_sites(self):
  q=overpass_query('Esslingen am Neckar')
  self.assertIn('ISO3166-1',q)
  self.assertIn('Esslingen am Neckar',q)
  self.assertIn('man_made',q)
  self.assertIn('out tags center 90',q)
  self.assertLessEqual(len(q),1100)
 def test_no_malicious_websites(self):
  self.assertEqual(website_from({'website':'javascript:alert(1)'}),'')
  self.assertEqual(website_from({'website':'https://test.example/careers'}),'https://test.example/careers')
 def test_mocked_overpass_returns_leads_not_jobs(self):
  fake={'elements':[{'type':'way','id':101,'center':{'lat':48.74,'lon':9.31},
   'tags':{'name':'Example Engineering GmbH','man_made':'works',
     'website':'https://example-industrial.com/careers'}},
   {'type':'node','id':102,'lat':48.75,'lon':9.32,
    'tags':{'name':'Example Plant without website','industrial':'machinery'}}]}
  with patch('local_companies.request_json',return_value=fake) as request,patch('local_companies.time.sleep'):
   output=discover_local_companies([],enabled=True)
  self.assertEqual(output['queries_succeeded'],4)
  self.assertEqual(len(output['candidates']),5) # website deduped across towns; no-site per town
  self.assertFalse(output['jobs_verified'])
  self.assertFalse(output['career_sites_verified'])
  first=output['candidates'][0]
  self.assertFalse(first['jobs_verified'])
  self.assertTrue(first['osm_url'].startswith('https://www.openstreetmap.org/way/'))
  self.assertTrue(all(x['source']=='OpenStreetMap' for x in output['candidates']))
  self.assertEqual(request.call_count,4)
 def test_disabled_does_not_query_network(self):
  with patch('local_companies.request_json') as req:
   d=discover_local_companies(['Hanau'],enabled=False)
  req.assert_not_called()
  self.assertFalse(d['searched_on_demand'])
 def test_standalone_notification_and_in_page_fallback(self):
  v3=(ROOT/'public/frontend-v3.js').read_text()
  html=(ROOT/'public/index.html').read_text()
  self.assertIn('data-route="companies"',html)
  self.assertIn('These public employer leads are not guaranteed vacancies.',v3)
  self.assertIn("api('/published?file='+f)",v3)
  self.assertIn("function companies()",v3)
if __name__=='__main__':unittest.main()
