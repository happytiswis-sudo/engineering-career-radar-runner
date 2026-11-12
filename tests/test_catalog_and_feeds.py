import json,unittest
from pathlib import Path
from unittest.mock import patch
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from radar import load,evaluate_rule,job,fetch_board,sanitized_cv

class BroadCareerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings,cls.cv=load()
        cls.catalog=json.loads((ROOT/'role_catalog.json').read_text())['roles']
        cls.settings['catalog_roles']=cls.catalog

    def make(self,title,description='engineering drawings, technical documentation, safety, ISO 9001, lean manufacturing, risk assessments'):
        return job('Test Company',title,'Algiers, Algeria','https://example.com/job/'+str(abs(hash(title))),description,'Test')

    def test_more_than_60_distinct_career_roles(self):
        titles=[r['title'].casefold() for r in self.catalog]
        self.assertGreaterEqual(len(titles),60)
        self.assertEqual(len(titles),len(set(titles)))
        self.assertGreaterEqual(len(set(r['track'] for r in self.catalog)),10)

    def test_master_cv_exactly_latest_uploaded(self):
        self.assertIn('sid2.kada@hotmail.com',self.cv)
        self.assertIn('98% on-time delivery',self.cv)
        self.assertIn('German:** B1',self.cv)
        self.assertIn('18 production operators',self.cv)
        self.assertNotIn('sidahmedkadaa@gmail.com',self.cv)

    def test_manufacturing(self):
        e=evaluate_rule(self.make('Manufacturing Process Engineer','lean manufacturing, manufacturing, 5S, production, technical documentation, quality assurance'),self.settings,self.cv)
        self.assertIsNotNone(e)
        self.assertEqual(e['career_track'],'Manufacturing & Production')
        self.assertGreaterEqual(e['score'],68)

    def test_production_supervisor(self):
        e=evaluate_rule(self.make('Production Supervisor','production supervision of 18 operators, 5S, quality control, workplace safety and 98% delivery.'),self.settings,self.cv)
        self.assertIsNotNone(e)
        self.assertEqual(e['career_track'],'Manufacturing & Production')

    def test_quality(self):
        e=evaluate_rule(self.make('Quality Assurance Engineer','ISO 9001 quality assurance, continuous improvement, root cause analysis, audits'),self.settings,self.cv)
        self.assertIsNotNone(e)
        self.assertEqual(e['career_track'],'Quality, Process & Compliance')

    def test_project_coordination(self):
        e=evaluate_rule(self.make('Engineering Project Coordinator','technical projects, feasibility and stakeholders, risk assessments, engineering documentation'),self.settings,self.cv)
        self.assertIsNotNone(e)
        self.assertEqual(e['career_track'],'Project Engineering & Delivery')

    def test_software_qa_excluded(self):
        e=evaluate_rule(self.make('Quality Engineer','Selenium software testing unit testing CI/CD API automation Python microservices'),self.settings,self.cv)
        self.assertIsNone(e)

    def test_it_does_not_invent_eligibility(self):
        e=evaluate_rule(self.make('Mechanical Design Engineer','CATIA, SolidWorks, engineering design. Must be a U.S. person. No visa sponsorship'),self.settings,self.cv)
        self.assertTrue(e['check_requirements'])
        self.assertLess(e['score'],80)

    def test_company_watchlist_is_not_a_feed_claim(self):
        d=json.loads((ROOT/'company_targets.json').read_text())
        self.assertGreaterEqual(sum(len(s['companies']) for s in d['sectors']),60)
        self.assertIn('not necessarily scanned',d['note'])

    def test_multiple_job_sources(self):
        d=json.loads((ROOT/'sources.json').read_text())
        kinds=set(b['type'] for b in d['boards'])
        self.assertTrue({'lever','greenhouse','ashby','arbeitnow','jobicy','remotive'} <= kinds)
        self.assertGreater(len(d['boards']),25)

    def test_jobicy_adapter(self):
        fake={'success':True,'jobs':[{'companyName':'Any','jobTitle':'Production Planner','jobGeo':'Europe','url':'https://jobicy.com/jobs/test','jobDescription':'Production planning','pubDate':'2026-10-25T00:00:00Z'}], 'nextCursor':None}
        with patch('public_source_adapters.request_json',return_value=fake),patch('public_source_adapters.time.sleep'):
            jobs=fetch_board({'type':'jobicy','slug':'global','company':'Jobicy'})
        self.assertEqual(len(jobs),1)
        self.assertEqual(jobs[0]['location'],'Europe')
        self.assertEqual(jobs[0]['source'],'Jobicy')

    def test_remotive_attribution(self):
        fake={'jobs':[{'company_name':'Any','title':'Production Engineer','candidate_required_location':'Europe','url':'https://remotive.com/remote-jobs/test','description':'Lean production','publication_date':'2026-10-24T10:00:00Z'}]}
        with patch('public_source_adapters.request_json',return_value=fake):
            jobs=fetch_board({'type':'remotive','slug':'global','company':'Remotive'})
        self.assertEqual(jobs[0]['source'],'Remotive (24h delay)')
        self.assertIn('remotive.com',jobs[0]['url'])

    def test_anonymized_cv(self):
        clean=sanitized_cv(self.cv)
        self.assertNotIn('sid2.kada@hotmail.com',clean)
        self.assertNotIn('15 December 1998',clean)
        self.assertNotIn('Algiers, Algeria | +213',clean)
        self.assertIn('Continuing Airworthiness Management',clean)

    def test_published_assets_do_not_include_cv(self):
        for p in (ROOT/'public').iterdir():
            if p.is_file():
                self.assertNotIn('sid2.kada@hotmail.com',p.read_text())
                self.assertNotIn('15 December 1998',p.read_text())

if __name__=='__main__':unittest.main()
