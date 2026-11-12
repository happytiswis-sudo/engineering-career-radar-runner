import json, unittest, sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from germany import location_signal,hiring_signals,fetch_german_jobs
from deep_search import validate_request, default_cities_for_region, dynamic_boards
from radar import load,evaluate_rule,job
ROOT=Path(__file__).resolve().parents[1]
class GermanyRadarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings,cls.cv=load()
    def test_small_industrial_town(self):
        v=location_signal('Böblingen, Baden-Württemberg, Deutschland',self.settings['west_germany'])
        self.assertTrue(v['west']);self.assertTrue(v['small_city']);self.assertEqual(v['cluster'],'Stuttgart region')
    def test_frankfurt_is_major(self):
        v=location_signal('Frankfurt am Main, Hessen',self.settings['west_germany'])
        self.assertTrue(v['west']);self.assertFalse(v['small_city'])
    def test_non_germany_is_not_falsely_local(self):
        v=location_signal('Seattle, WA, United States',self.settings['west_germany'])
        self.assertFalse(v['germany'])
    def test_blue_card_mention_is_not_support(self):
        status=hiring_signals('Eligible candidates may apply for the EU Blue Card.')
        self.assertEqual(status['blue_card']['status'],'mentioned')
        self.assertEqual(status['visa']['status'],'not_stated')
    def test_explicit_support_detection(self):
        s=hiring_signals('We offer visa sponsorship and relocation assistance. International applicants are welcome.')
        self.assertEqual(s['visa']['status'],'explicit')
        self.assertEqual(s['relocation']['status'],'explicit')
        self.assertEqual(s['international']['status'],'explicit')
    def test_negative_visa_overrides_mention(self):
        s=hiring_signals('No visa sponsorship. This role cannot sponsor visas.')
        self.assertEqual(s['visa']['status'],'not_offered')
    def test_german_support(self):
        s=hiring_signals('Wir bieten Visumsunterstützung und Umzugsunterstützung.')
        self.assertEqual(s['visa']['status'],'explicit')
        self.assertEqual(s['relocation']['status'],'explicit')
    def test_ranking_western_germany(self):
        self.settings['catalog_roles']=json.loads((ROOT/'role_catalog.json').read_text())['roles']
        berlin=evaluate_rule(job('Test','Fertigungsingenieur','Berlin, Deutschland','https://example.org/b','Produktionsplanung, SolidWorks, Fertigung, Qualitätskontrolle','Test'),self.settings,self.cv)
        west=evaluate_rule(job('Test','Fertigungsingenieur','Esslingen, Germany','https://example.org/e','Produktionsplanung, SolidWorks, Fertigung, Qualitätskontrolle','Test'),self.settings,self.cv)
        self.assertIsNotNone(west)
        self.assertTrue(west['market']['small_city'])
        self.assertGreaterEqual(west['score'],berlin['score'])
    def test_directory_has_300_plus_candidate_boards(self):
        boards=json.loads((ROOT/'discovered_ats_boards.json').read_text())['boards']
        self.assertGreaterEqual(len(boards),300)
        self.assertTrue(all(x.get('last_crawled') for x in boards))
    def test_german_titles_over_300(self):
        roles=json.loads((ROOT/'role_catalog.json').read_text())['roles']
        self.assertGreaterEqual(len(roles),300)
        self.assertIn('Fertigungsingenieur',[x['title'] for x in roles])
    def test_german_agency_parser(self):
        sample={'stellenangebote':[{'refnr':'10001-12345-S','titel':'Fertigungsingenieur','arbeitgeber':'Example GmbH','arbeitsort':{'ort':'Esslingen'},'aktuelleVeroeffentlichungsdatum':'2026-10-25'}]}
        class Fake:
            def __enter__(self):return self
            def __exit__(self,*args):pass
        with patch('germany.urllib.request.urlopen',return_value=Fake()),patch('germany.json.load',return_value=sample):
            x=fetch_german_jobs({'city':'Esslingen','query':'Fertigung','size':5})
        self.assertEqual(len(x),1)
        self.assertIn('arbeitsagentur.de',x[0]['url'])
        self.assertIn('Esslingen',x[0]['location'])
    def test_german_agency_bounded_detail_enrichment(self):
        sample={'stellenangebote':[{'refnr':'10001-12345-S','titel':'Fertigungsingenieur',
            'arbeitgeber':'Example GmbH','arbeitsort':{'ort':'Esslingen'},
            'aktuelleVeroeffentlichungsdatum':'2026-10-25'}]}
        class Fake:
            def __enter__(self):return self
            def __exit__(self,*args):pass
        with patch('germany.urllib.request.urlopen',return_value=Fake()), \
             patch('germany.json.load',return_value=sample), \
             patch('germany.german_job_detail',return_value='Vollständige Aufgaben und Anforderungen. '*30) as detail:
            x=fetch_german_jobs({'city':'Esslingen','query':'Fertigung','size':10,'detail_budget':1})
        self.assertEqual(detail.call_count,1)
        self.assertEqual(x[0]['reference'],'10001-12345-S')
        self.assertEqual(x[0]['published_at'],'2026-10-25')
        self.assertEqual(x[0]['description_completeness'],'BA public detail response')
        self.assertIn('Vollständige Aufgaben',x[0]['description'])

    def test_default_requested_ba_radius_is_90_km(self):
        profile=validate_request({'region':'germany','sources':['ba']})
        self.assertEqual(profile['radius'],90)
        boards=dynamic_boards(profile)
        self.assertTrue(boards)
        self.assertTrue(all(x['radius']==90 for x in boards))
        self.assertLessEqual(len(boards),220)
        self.assertTrue(all(x['pages']<=2 for x in boards))

    def test_explicit_radius_is_applied_to_all_dynamic_boards(self):
        profile=validate_request({'region':'germany','radius':90,'sources':['ba'],'depth':'deep'})
        boards=dynamic_boards(profile)
        self.assertEqual(len(boards),220)
        self.assertTrue(all(x['radius']==90 for x in boards))
        self.assertTrue(all(x['pages']==2 for x in boards))

    def test_national_city_rotation_expands_industrial_coverage(self):
        first=default_cities_for_region('germany',when=__import__('datetime').date(2026,11,8))
        later=default_cities_for_region('germany',when=__import__('datetime').date(2026,11,9))
        for city in ('Ulm','Duisburg','Saarbrücken','Kaiserslautern','Bremerhaven','Wolfsburg','Ingolstadt'):
            self.assertIn(city,NATIONAL_CITIES if False else __import__('deep_search').NATIONAL_CITIES)
        self.assertEqual(len(first),46)
        self.assertEqual(len(later),46)
        self.assertEqual(first[:34],DEFAULT_CITIES if False else __import__('deep_search').DEFAULT_CITIES)
        self.assertNotEqual(first[34:],later[34:])

    def test_ba_radius_request_is_used_and_recorded(self):
        sample={'stellenangebote':[{'refnr':'10001-12345-S','titel':'Fertigungsingenieur',
            'arbeitgeber':'Example GmbH','arbeitsort':{'ort':'Esslingen'},
            'aktuelleVeroeffentlichungsdatum':'2026-10-25'}]}
        class Fake:
            def __enter__(self):return self
            def __exit__(self,*args):pass
        captured=[]
        def fake_urlopen(request,timeout=14):
            captured.append(request.full_url)
            return Fake()
        with patch('germany.urllib.request.urlopen',side_effect=fake_urlopen), \
             patch('germany.json.load',return_value=sample):
            jobs=fetch_german_jobs({'city':'Esslingen','query':'Fertigung','radius':90,'size':10})
        self.assertIn('umkreis=90',captured[0])
        self.assertEqual(jobs[0]['search_radius_km'],90)
if __name__=='__main__':unittest.main()
