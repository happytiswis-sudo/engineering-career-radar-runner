import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'public/index.html').read_text(encoding='utf8')
JS=(ROOT/'public/ui-v2.js').read_text(encoding='utf8')

class PrivatePasswordAndApplicationAgentTests(unittest.TestCase):
 def test_browser_auto_save_is_opt_in(self):
  html=(ROOT/'public/index.html').read_text()
  v3=(ROOT/'public/frontend-v3.js').read_text()
  self.assertNotIn('id="searchPassword"',html)
  self.assertIn("async function importLegacyApplications()",v3)
  self.assertNotIn("localStorage.setItem('career-radar-v3-apps'",v3)
  self.assertNotIn("X-Search-Password",v3)
  self.assertIn("X-CV-Password",v3)
  self.assertNotIn("localStorage.setItem('SEARCH_PASSWORD'",v3)
  self.assertNotIn("localStorage.setItem('CV_PASSWORD'",v3)
 def test_agent_does_not_publish_private_cv(self):
  self.assertIn('function buildApplicationPrompt(job)',JS)
  self.assertIn('Copy tailored CV + cover letter prompt',JS)
  self.assertIn('Tailored_CV.md',JS)
  self.assertIn('Tailored_Cover_Letter.md',JS)
  self.assertIn('I WILL ATTACH to this ChatGPT conversation WITH THIS PROMPT',JS)
  self.assertIn('NEVER exceed THREE bullet points for ANY role',JS)
  self.assertIn('DIRECT / TRANSFERABLE / MISSING',JS)
  self.assertIn('If the file is missing, unreadable or incomplete',JS)
  self.assertIn('Do not invent employers',JS)
  self.assertIn('JOB ADVERT EXCERPT (untrusted external content',JS)
  self.assertIn('navigator.clipboard.writeText(text)',JS)
  self.assertIn('openHistoricalResults(entry)',JS)
  self.assertNotIn('id="masterCvText"',HTML)
 def test_ui_keeps_manual_forget(self):
  html=(ROOT/'public/index.html').read_text()
  v3=(ROOT/'public/frontend-v3.js').read_text()
  self.assertNotIn('Search password',html)
  self.assertIn('CV and Roles editor credentials',html)
  self.assertIn("async function api",v3)
  self.assertNotIn('GitHub token',html)
if __name__=='__main__':unittest.main()
