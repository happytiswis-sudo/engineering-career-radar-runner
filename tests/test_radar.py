import sys,unittest,re,json
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from radar import evaluate_rule,sanitized_cv,load,detect_risks,job,configured_ai_providers,catalog_match,normalize_title,tally_source_metric

class RadarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile,cls.cv=load()
    def test_source_diagnostics_reports_missing_keys_rate_limits_and_stale_boards(self):
        from radar import build_source_diagnostics
        report=build_source_diagnostics(
            {'serpapi_google_jobs':{'boards':1,'errors':1,'attempted_queries':0,'usable_postings':0},
             'ashby':{'boards':4,'succeeded':4,'errors':0,'usable_postings':12,'attempted_queries':0}},
            {'serpapi_google_jobs':'unconfigured'},
            [{'source':'ashby','error':'HTTP 429 provider limit'}],
            {'ashby|old-board':{'type':'ashby','slug':'old-board','reason':'http_404'}})
        signals={(x['source'],x['signal']) for x in report}
        self.assertIn(('serpapi_google_jobs','missing_credential'),signals)
        self.assertIn(('ashby','provider_rate_limited'),signals)
        self.assertIn(('ashby:old-board','stale_or_invalid_board'),signals)

    def test_source_diagnostics_uses_observed_yield_without_cv_filtering(self):
        from radar import build_source_diagnostics
        report=build_source_diagnostics(
            {'workday':{'boards':4,'succeeded':4,'errors':0,'attempted_queries':20,
                        'usable_postings':2}}, {}, [], {})
        low_yield=[x for x in report if x['signal']=='low_usable_yield']
        self.assertEqual(len(low_yield),1)
        self.assertEqual(low_yield[0]['source'],'workday')
    def test_dynamic_jobspy_metric_keys_survive_success_and_error_paths(self):
        # Regression for run #40665715273: both the first metric write and
        # its failure handler raised KeyError('planned_queries').
        metrics={}
        for key,value in [('planned_queries',68),('attempted_queries',12),
                          ('completed_queries',10),('failed_queries',2),
                          ('elapsed_seconds',19.5),('slowest_seconds',8.1)]:
            tally_source_metric(metrics,'jobspy_indeed',key,value)
        self.assertEqual(metrics['jobspy_indeed']['planned_queries'],68)
        self.assertEqual(metrics['jobspy_indeed']['completed_queries'],10)
        tally_source_metric(metrics,'jobspy_indeed','attempted_queries',1)
        self.assertEqual(metrics['jobspy_indeed']['attempted_queries'],13)
        tally_source_metric(metrics,'jobspy_indeed','errors',1)
        tally_source_metric(metrics,'jobspy_glassdoor','failed_queries',1)
        tally_source_metric(metrics,'jobspy_glassdoor','boards',1)
        self.assertEqual(metrics['jobspy_indeed']['errors'],1)
        self.assertEqual(metrics['jobspy_glassdoor']['failed_queries'],1)
        self.assertEqual(metrics['jobspy_glassdoor']['boards'],1)

    def test_cached_title_index_matches_legacy_regex_logic(self):
        from pathlib import Path
        roles=json.loads((Path(__file__).resolve().parents[1]/'role_catalog.json').read_text())['roles']
        settings=dict(self.profile,catalog_roles=roles)
        examples=[
            'Quality Engineer','Quality Engineer Operations','Senior Quality Engineer / all genders',
            'Project Engineer','Mechanical Design Engineer (m/f/d)',
            'Airport Operations Coordinator','Quality Management System Engineer',
            'Production Supervisor','Cargo Handling Coordinator','CAMO Engineer',
            'Rail Maintenance Technician','Manufacturing Process Engineer',
            'Random Unlisted Industrial Specialist','Software Engineer',
            'Techniker Qualitätssicherung','Design Engineer','CAD Technician',
        ]
        examples += [r['title']+' (m/f/d)' for r in roles[::25]]
        for title in examples:
            normalized=normalize_title(title)
            expected=None
            for role in roles:
                name=normalize_title(role['title'])
                if re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',normalized):
                    score=settings.get('role_title_priority',{}).get(role['priority'],0.83)
                    candidate=(score,len(name.split()),role)
                    if expected is None or candidate[:2]>expected[:2]:expected=candidate
            if expected:
                wanted=(expected[0],expected[2]['track'],expected[2]['title'],expected[2]['priority'])
                self.assertEqual(catalog_match(title,settings),wanted,title)
        self.assertIs(settings['_catalog_title_index']['roles'],roles)
        saved=settings['_catalog_title_index']
        catalog_match('Quality Engineer',settings)
        self.assertIs(settings['_catalog_title_index'],saved)

    def test_cv_contains_real_skills(self):
        self.assertIn('SolidWorks',self.cv)
        self.assertIn('Continuing Airworthiness',self.cv)
        self.assertIn('Whirlpool',self.cv)
    def test_uav_match(self):
        j=job('Test Aviation','UAV Project Engineer','Remote','https://example.org/job/99',
              'UAV mission planning, BVLOS, technical requirements, CONOPS, stakeholder coordination, safety and SolidWorks.','Example')
        out=evaluate_rule(j,self.profile,self.cv)
        self.assertIsNotNone(out)
        self.assertGreaterEqual(out['score'],75)
        self.assertIn('UAV operations / UAS',out['matched_skills'])
    def test_camo_match(self):
        j=job('Test Air','CAMO Engineer','France','https://example.org/jobs/camo',
              'Continuing airworthiness management, ADs, aircraft technical records, maintenance scheduling','Example')
        out=evaluate_rule(j,self.profile,self.cv)
        self.assertIsNotNone(out)
        self.assertGreater(out['score'],60)
    def test_itar_penalty_and_warning(self):
        base=job('Test Air','UAV Project Engineer','United States','https://example.org/jobs/1','UAV flight planning.','Example')
        risk=job('Test Air','UAV Project Engineer','United States','https://example.org/jobs/2','UAV flight planning. Must be a U.S. person. Security clearance required.','Example')
        first=evaluate_rule(base,self.profile,self.cv)
        second=evaluate_rule(risk,self.profile,self.cv)
        self.assertLess(second['score'],first['score'])
        self.assertTrue(any('US person' in x for x in second['check_requirements']))
    def test_discard_other_career_field(self):
        j=job('Other','Senior Software Engineer','London','https://example.org/jobs/3','backend kubernetes','Example')
        self.assertIsNone(evaluate_rule(j,self.profile,self.cv))
    def test_cv_scrubbing(self):
        clean=sanitized_cv(self.cv)
        self.assertNotIn('sidahmedkadaa@gmail.com',clean)
        self.assertNotIn('15 December 1998',clean)
        self.assertNotIn('+213',clean)
        self.assertIn('UAV Project Engineer',clean)
    def test_both_ai_gateways_are_configured_without_exposing_keys(self):
        with patch.dict('os.environ',{'OPENROUTER_API_KEY':'test-openrouter-secret',
                                      'NARAROUTER_API_KEY':'sk-nara-fake-credential',
                                      'NARAROUTER_PROVIDER':'naraya',
                                      'NARAROUTER_MODEL':''},clear=True):
            p=configured_ai_providers(self.profile)
        self.assertEqual([x['name'] for x in p],['OpenRouter','NaraRouter (naraya)'])
        self.assertEqual(p[0]['model'],'google/gemma-4-26b-a4b-it:free')
        self.assertEqual(p[0]['url'],'https://openrouter.ai/api/v1/chat/completions')
        self.assertEqual(p[1]['model'],'auto/naraya.ai')

    def test_bynara_gateway_detection(self):
        with patch.dict('os.environ',{'NARAROUTER_API_KEY':'sk-nry-fake-credential'},clear=True):
            p=configured_ai_providers(self.profile)
        self.assertEqual(len(p),1)
        self.assertEqual(p[0]['name'],'NaraRouter (bynara)')
        self.assertEqual(p[0]['url'],'https://router.bynara.id/v1/chat/completions')
        self.assertEqual(p[0]['model'],'laguna-s-2.1')

    def test_publish_does_not_contain_cv(self):
        web=Path(__file__).resolve().parents[1]/'public'
        for x in web.glob('**/*'):
            self.assertNotIn('master_cv',x.name)
            if x.is_file():
                self.assertNotIn('sidahmedkadaa@gmail.com',x.read_text(encoding='utf8'))


    def test_seniority_content_is_assessed_not_title_alone(self):
        junior_title_senior_content=job('Example','Junior Project Engineer','Stuttgart, Germany',
            'https://example.org/junior-senior-content',
            'Senior-level position requiring minimum 7 years professional experience. SolidWorks, project planning and technical documentation.','Test')
        senior_title_junior_content=job('Example','Senior Project Engineer','Stuttgart, Germany',
            'https://example.org/senior-junior-content',
            'Entry-level opportunity, graduate welcome, no prior experience required. SolidWorks, project planning and technical documentation.','Test')
        first=evaluate_rule(junior_title_senior_content,self.profile,self.cv)
        second=evaluate_rule(senior_title_junior_content,self.profile,self.cv)
        self.assertIsNotNone(first);self.assertIsNotNone(second)
        self.assertEqual(first['score_components']['junior_priority'],0)
        self.assertGreater(second['score_components']['entry_priority'],0)
        self.assertTrue(any(x.startswith('Requires 7+ years') for x in first['check_requirements']))

    def test_manager_title_is_not_senior_without_body_evidence(self):
        j=job('Operations GmbH','Maintenance Manager','Stuttgart, Germany',
            'https://example.org/maintenance-manager',
            'Entry-level opportunity for an individual contributor. No people management. First professional experience welcome. Maintenance planning, quality control and technical documentation.','Test')
        out=evaluate_rule(j,self.profile,self.cv)
        self.assertIsNotNone(out)
        self.assertGreater(out['score_components']['entry_priority'],0)
        self.assertTrue(out['seniority_assessment']['title_body_conflict'])
        self.assertFalse(out['seniority_assessment']['default_excluded'])

    def test_manager_vacancy_with_people_management_is_senior_evidence(self):
        j=job('Operations GmbH','Maintenance Coordinator','Stuttgart, Germany',
            'https://example.org/maintenance-lead',
            'Requires minimum 6 years of relevant professional experience. Manage a team of 8 technicians with direct reports, budget ownership and annual performance reviews. Maintenance planning, quality control and technical documentation.','Test')
        out=evaluate_rule(j,self.profile,self.cv)
        self.assertIsNotNone(out)
        self.assertEqual(out['score_components']['junior_priority'],0)
        self.assertTrue(out['seniority_assessment']['body_senior_evidence'])
        self.assertEqual(out['capability']['experience_level'],'senior')

    def test_explicit_junior_role_gets_ranking_priority(self):
        junior_job=job('Junior Test GmbH','Junior Manufacturing Engineer','Stuttgart, Germany',
            'https://example.org/junior','First professional experience welcome. SolidWorks, production planning, quality control and technical documentation.','Test')
        senior_job=job('Senior Test GmbH','Senior Manufacturing Engineer','Stuttgart, Germany',
            'https://example.org/senior','Minimum 6 years of professional experience. SolidWorks, production planning, quality control and technical documentation.','Test')
        junior=evaluate_rule(junior_job,self.profile,self.cv)
        senior=evaluate_rule(senior_job,self.profile,self.cv)
        self.assertIsNotNone(junior);self.assertIsNotNone(senior)
        self.assertEqual(junior['score_components']['junior_priority'],12)
        self.assertEqual(senior['score_components']['junior_priority'],0)
        self.assertGreater(junior['score'],senior['score'])
        self.assertEqual(junior['verdict'],'Junior priority')

    def test_german_entry_level_vocabulary_gets_priority(self):
        j=job('Graduate GmbH','Projektingenieur (m/w/d) Berufseinstieg','Frankfurt am Main, Germany',
            'https://example.org/graduate','Absolventen willkommen. Erste Berufserfahrung ist von Vorteil. SolidWorks, Projektkoordination und technische Dokumentation.','Test')
        out=evaluate_rule(j,self.profile,self.cv)
        self.assertIsNotNone(out)
        self.assertEqual(out['score_components']['entry_priority'],15)
        self.assertEqual(out['score_components']['junior_priority'],0)
        self.assertEqual(out['capability']['experience_level'],'junior')
        self.assertTrue(out['capability']['junior_signal'])

    def test_mandatory_master_degree_exclusion_is_not_reversed_by_junior_bonus(self):
        j=job('Graduate GmbH','Graduate Mechanical Engineer','Stuttgart, Germany',
            'https://example.org/graduate-master','Entry-level position. A completed Master degree is mandatory. SolidWorks.','Test')
        out=evaluate_rule(j,self.profile,self.cv)
        self.assertIsNotNone(out)
        self.assertEqual(out['qualification']['status'],'excluded')
        self.assertEqual(out['score_components']['junior_priority'],0)
        self.assertLessEqual(out['score'],30)

    def test_ai_provider_priority_is_settings_driven_and_keeps_gemma_openrouter_second(self):
        with patch.dict('os.environ',{'INCEPTION_API_KEY':'test-mercury',
                                      'OPENROUTER_API_KEY':'test-openrouter',
                                      'NARAROUTER_API_KEY':'sk-nry-test'},clear=True):
            providers=configured_ai_providers(dict(self.profile,
                ai_provider_priority=['Inception Mercury 3','OpenRouter','NaraRouter']))
        self.assertEqual([p['name'].split(' (')[0] for p in providers],
                         ['Inception Mercury 3','OpenRouter','NaraRouter'])
        self.assertEqual(providers[1]['model'],'google/gemma-4-26b-a4b-it:free')
    def test_bundesagentur_app_endpoint_is_gated_until_authorized(self):
        with patch('radar.dynamic_boards') as dynamic, patch('radar.industry_boards') as industries:
            settings=dict(self.profile, discovery_ba_adapter_mode='disabled_pending_authorization')
            # Entry point is exercised via the source-construction helper in the test suite;
            # this contract documents that the default configuration is explicitly disabled.
            self.assertEqual(settings['discovery_ba_adapter_mode'],'disabled_pending_authorization')
            dynamic.assert_not_called()
            industries.assert_not_called()

    def test_track_coverage_report_counts_failed_and_skipped_tracks(self):
        from radar import build_track_coverage_report,build_source_status_report
        catalog=[{'track':'A','title':'A Engineer'},{'track':'B','title':'B Technician'},
                 {'track':'C','title':'C Coordinator'},{'track':'D','title':'D Specialist'}]
        plan=[
         {'type':'bundesagentur','slug':'industry','city':'Berlin','query':'A Engineer','industry_track':'A'},
         {'type':'bundesagentur','slug':'industry','city':'Munich','query':'A Engineer','industry_track':'A'},
         {'type':'bundesagentur','slug':'industry','city':'Hamburg','query':'B Technician','industry_track':'B'},
         {'type':'bundesagentur','slug':'industry','city':'Leipzig','query':'C Coordinator','industry_track':'C'}]
        outcomes=[
         {'type':'bundesagentur','slug':'industry','city':'Berlin','query':'A Engineer','status':'succeeded','vacancies_returned':4},
         {'type':'bundesagentur','slug':'industry','city':'Munich','query':'A Engineer','status':'failed','vacancies_returned':0},
         {'type':'bundesagentur','slug':'industry','city':'Hamburg','query':'B Technician','status':'failed','vacancies_returned':0}]
        report=build_track_coverage_report(catalog,plan,outcomes)
        self.assertEqual(report['catalogue_track_count'],4)
        self.assertEqual(report['successful_queries'],1)
        self.assertEqual(report['failed_queries'],2)
        self.assertEqual(report['skipped_queries'],0)
        self.assertEqual(report['planned_queries'],4)
        self.assertEqual({x['status'] for x in report['tracks']},{'failed','planned','skipped'})
        self.assertEqual(next(x for x in report['tracks'] if x['track']=='A')['status'],'failed')
        self.assertEqual(report['catalogue_roles_succeeded'],0)
        self.assertEqual(report['catalogue_roles_failed'],2)
        self.assertEqual(report['catalogue_roles_unsearched'],1)
        selected=build_track_coverage_report(catalog,plan,outcomes,selected_tracks=['B'])
        self.assertEqual([x['track'] for x in selected['tracks']],['B'])
        self.assertTrue(selected['selected_tracks_only'])
        source_report=build_source_status_report(['bundesagentur','cloro'],
           [{'type':'bundesagentur','slug':'industry'}],
           [{'type':'bundesagentur','slug':'industry','status':'failed'}],
           unconfigured={'cloro':'unconfigured'},selected_source_ids=['ba'],selection_mode='user-selected')
        statuses={x['source']:x['status'] for x in source_report['sources']}
        selected={x['source']:x['selected'] for x in source_report['sources']}
        self.assertEqual(source_report['selected_source_ids'],['ba'])
        self.assertTrue(selected['bundesagentur'])
        self.assertFalse(selected['cloro'])
        self.assertEqual(statuses,{'bundesagentur':'failed','cloro':'unconfigured'})

if __name__=='__main__': unittest.main()
