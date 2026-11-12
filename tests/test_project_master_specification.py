"""Contract checks guarding the permanent Career Radar project specification.

Not a prose-quality test. Its purpose is to surface configuration drift after
new sources, agents, role families or retention caps are introduced, requiring
human revision of the master spec and the append-only decision ledger.
"""
from __future__ import annotations
import json
from pathlib import Path
import unittest

from deep_search import ROLE_GROUPS
from agent_engine import AGENTS
from career_intelligence import EXTENDED_TEAMS

ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/'PROJECT_MASTER_SPECIFICATION.md'
DECISIONS=ROOT/'PROJECT_DECISION_LOG.md'
README=ROOT/'README.md'

class ProjectContinuityContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master=MASTER.read_text(encoding='utf8')
        cls.decisions=DECISIONS.read_text(encoding='utf8')

    def test_master_exists_as_canonical_entrypoint(self):
        readme=README.read_text(encoding='utf8')
        self.assertIn('[PROJECT MASTER SPECIFICATION](PROJECT_MASTER_SPECIFICATION.md)',readme)
        self.assertIn('[PROJECT DECISION LOG](PROJECT_DECISION_LOG.md)',readme)
        self.assertIn('live implementation',readme)

    def test_role_and_agent_counts_are_kept_current(self):
        catalog=json.loads((ROOT/'role_catalog.json').read_text(encoding='utf8'))['roles']
        self.assertIn(f'{len(catalog)} mapped role titles across {len(set(x["track"] for x in catalog))} tracks',self.master)
        self.assertIn(f'{len(ROLE_GROUPS)} dynamic job-search families',self.master)
        extended=sum(len(v) for v in EXTENDED_TEAMS.values())
        self.assertIn(f'{len(AGENTS)+extended} deterministic evidence specialists in {6+len(EXTENDED_TEAMS)} teams',self.master)
        self.assertEqual(len(AGENTS),36)
        self.assertEqual(extended,18)

    def test_retrieval_and_caps_are_not_documentation_only_guesses(self):
        settings=json.loads((ROOT/'settings.json').read_text(encoding='utf8'))
        core=json.loads((ROOT/'sources.json').read_text(encoding='utf8'))['boards']
        additional=json.loads((ROOT/'additional_job_boards.json').read_text(encoding='utf8'))['public_sources']
        historic=json.loads((ROOT/'discovered_ats_boards.json').read_text(encoding='utf8'))['boards']
        for value,phrase in [
            (len(core),'configured source entries'),
            (len(additional),'additional public-board/feed entries'),
            (len(historic),'historical candidate ATS board records')]:
            self.assertIn(f'{value} {phrase}',self.master)
        self.assertIn(f'{settings["max_listings"]:,}',self.master)
        self.assertIn(f'{settings["minimum_target_vacancies"]:,}',self.master)
        self.assertIn('preliminary inclusion threshold **22**',self.master)

    def test_critical_design_and_privacy_rules_must_remain(self):
        for required in (
            'private/master_cv.md','Cloudflare','Hugging Face','GitHub Actions',
            'GITHUB_TOKEN','SEARCH_PASSWORD','HF_TOKEN','HIMALAYAS_API_KEY',
            'The Muse','Make it in Germany','EURES','Nomado24','Workday',
            'last 24h','source_metrics','search-history.json','/runs',
            '/cancel','manual', '1–3 bullets','BSc (Hons)',
            'localStorage','PROJECT_DECISION_LOG.md',
            'planned','implemented','live verified',
            'No local installation','not a guarantee'
        ):
            self.assertIn(required.casefold(),self.master.casefold(),
                          msg=f'Master specification missing mandatory continuity item: {required}')

    def test_full_21_sections_and_append_only_decisions(self):
        for number in range(1,22):
            self.assertIn(f'## {number}.',self.master)
        for number in range(1,20):
            self.assertIn(f'### DEC-{number:03d}',self.decisions)
        self.assertIn('Append only',self.decisions)
        self.assertIn('Manual activation',self.decisions)

    def test_workflow_documentation_is_present(self):
        for path in (
            '.github/workflows/scan-and-publish.yml',
            '.github/workflows/publish-interface.yml',
            '.github/workflows/verify.yml',
            '.github/workflows/source-probe.yml',
            'cloudflare/search-worker.js','radar.py','deep_search.py',
            'eligibility.py','agent_engine.py','career_intelligence.py',
            'public_source_adapters.py','bootstrap_history.py',
            'search_history.py','publish_history.py',
            'public/ui-v2.js','public/index.html'
        ):
            self.assertTrue((ROOT/path).exists(),f'Project file was removed: {path}')
            self.assertIn(Path(path).name,self.master,f'Project spec fails to mention: {path}')

if __name__=='__main__':
    unittest.main()
