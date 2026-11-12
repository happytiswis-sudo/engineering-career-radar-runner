import unittest
from pathlib import Path
import json
from career_intelligence import run_extended_agents
from agent_engine import AGENTS

ROOT=Path(__file__).resolve().parents[1]

class WholePipelineContractTests(unittest.TestCase):
 def test_end_to_end_filters_have_matching_fields(self):
  v3=(ROOT/'public/frontend-v3.js').read_text()
  html=(ROOT/'public/index.html').read_text()
  worker=(ROOT/'cloudflare/search-worker.js').read_text()
  backend=(ROOT/'deep_search.py').read_text()
  for feature in ('freshness','visa_possible','mobility_possible','nomado24'):
   self.assertIn(feature,worker)
   self.assertIn(feature,backend)
  self.assertIn('id="freshness"',v3)
  self.assertIn("freshness:$('freshness').value",v3)
  self.assertIn("support:$('support').value",v3)
  self.assertIn("capacity:$('capacity').value",v3)
  self.assertIn("min_score:Number($('score').value)",v3)
  self.assertIn('id="embedded-frontend-v3-js"',html)
 def test_extended_agents_are_persisted(self):
  radar=(ROOT/'radar.py').read_text()
  history=(ROOT/'search_history.py').read_text()
  self.assertEqual(len(AGENTS),36)
  self.assertIn("len(AGENTS)+12",radar)
  self.assertIn("'immigration_opportunity'",history)
  self.assertIn("'freshness'",history)
  self.assertIn("'capability'",history)
 def test_prompt_can_research_company_without_overclaim(self):
  ui=(ROOT/'public/ui-v2.js').read_text()
  start=ui.index('function buildApplicationPrompt(job){')
  end=ui.index('async function copyApplicationPrompt(',start)
  prompt=ui[start:end]
  for snippet in ['RESEARCH THIS REAL COMPANY','OFFICIAL website','hiring location/site',
                  'original vacancy','my attached CV','THREE bullet points']:
   self.assertIn(snippet,prompt)
  self.assertNotIn('private/master_cv.md',prompt)
 def test_new_source_registered(self):
  catalog=json.loads((ROOT/'additional_job_boards.json').read_text())
  self.assertTrue(any(s.get('type')=='nomado24' for s in catalog['public_sources']))
  adapters=(ROOT/'public_source_adapters.py').read_text()
  self.assertIn("'nomado24':nomado24",adapters)
  self.assertIn("'https://api.nomado24.de/api/public/v2/jobs'",adapters)
 def test_supabase_results_are_primary_persisted_pipeline(self):
  workflow=(ROOT/'.github/workflows/scan-and-publish.yml').read_text()
  publisher=(ROOT/'publish_supabase_jobs.py').read_text()
  worker=(ROOT/'cloudflare/search-worker.js').read_text()
  ui=(ROOT/'public/ui-v2.js').read_text()
  self.assertIn('Persist completed shortlist to Supabase (primary results store)',workflow)
  self.assertIn('run: python publish_supabase_jobs.py',workflow)
  self.assertIn('SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}',workflow)
  self.assertIn('/rpc/career_radar_upsert_scan_jobs',publisher)
  self.assertIn('p_run_id',publisher)
  self.assertIn("url.searchParams.get('run_id')",worker)
  self.assertIn('/rpc/career_radar_get_scan_jobs',worker)
  self.assertIn("call('/supabase-jobs?limit=100')",ui)
  self.assertIn("call('/supabase-jobs?run_id='+encodeURIComponent(runId)+'&limit=5000')",ui)
  self.assertIn('let jobsFullLoaded=false,jobsLoadInFlight=null,jobsLoadGeneration=0',ui)
  self.assertRegex(publisher,r'if\s+total\s*!=\s*len\(jobs\)\s*:')
 def test_workflow_supports_secure_publishing(self):
  workflow=(ROOT/'.github/workflows/scan-and-publish.yml').read_text()
  self.assertIn("run: python radar.py",workflow)
  self.assertIn("run: python publish_history.py",workflow)
  publisher=(ROOT/"publish_history.py").read_text()
  self.assertNotIn("X-Search-Password",publisher)
  self.assertNotIn("CARE_RADAR_BRIDGE_URL",publisher)
  self.assertIn("HIMALAYAS_API_KEY: ",workflow)
  self.assertNotIn('private/master_cv.md\'\'',workflow)

 def test_no_overview_route_and_search_is_default(self):
  ui=(ROOT/'public/frontend-v3.js').read_text()
  html=(ROOT/'public/index.html').read_text()
  self.assertIn("function route(k){if(k==='dashboard')k='search';",ui)
  self.assertIn("route('search');",ui)
  self.assertNotIn("lockWorkspace();",ui)
  self.assertNotIn("function home(){",ui)
  self.assertNotIn("dashboard:['Overview'",ui)
  self.assertIn('data-route="search"',html)

 def test_private_dashboard_proxy_includes_role_catalog(self):
  worker=(ROOT/'cloudflare/dashboard-lock-worker.js').read_text()
  self.assertIn('"/role_catalog.json"',worker)
  self.assertIn('HF_TOKEN',worker)
  self.assertIn('env.ASSETS.fetch(request)',worker)


 def test_sync_ui_workflow_checks_search_first_no_overview_contract(self):
  workflow=(ROOT/'.github/workflows/sync-space-ui.yml').read_text()
  self.assertIn('tests/dashboard_navigation_wiring.test.js',workflow)
  self.assertIn('tests/frontend_v3_contract.test.js',workflow)


 def test_dashboard_shell_is_visible_without_blocking_login_gate(self):
  html=(ROOT/'public/index.html').read_text()
  ui=(ROOT/'public/frontend-v3.js').read_text()
  self.assertIn('<div id="workspaceShell" class="layout">',html)
  self.assertNotIn('id="workspaceGate"',html)
  self.assertNotIn("lockWorkspace();",ui)
  self.assertIn('data-route="search"',html)
  self.assertIn('data-route="results"',html)
  self.assertIn('data-route="history"',html)
  self.assertIn('data-route="applications"',html)
  self.assertIn('data-route="cv"',html)
  self.assertIn('data-route="roles"',html)
  self.assertIn('data-route="companies"',html)
  self.assertNotIn("X-Search-Password",ui)
  self.assertIn("X-CV-Password",ui)

if __name__=='__main__':unittest.main()
