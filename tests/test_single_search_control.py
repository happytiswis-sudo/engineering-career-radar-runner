import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class SingleSearchControlTests(unittest.TestCase):
 def test_one_primary_start_cancel_button(self):
  html=(ROOT/'public/index.html').read_text(encoding='utf8')
  js=(ROOT/'public/frontend-v3.js').read_text(encoding='utf8')
  self.assertIn('data-route="search"',html)
  self.assertIn('id="launch"',js)
  self.assertIn('id="check"',js)
  self.assertIn('id="cancel"',js)
  self.assertIn("api('/search','POST',p)",js)
  self.assertIn("api('/cancel','POST',{run_id:S.activeRun})",js)
  self.assertIn("api('/status?started_after='",js)
 def test_dashboard_exposes_shared_capacity_profile(self):
  js=(ROOT/'public/frontend-v3.js').read_text(encoding='utf8')
  self.assertIn('maximum_safe',js)
  self.assertIn("capacity:$('capacity').value",js)
  self.assertIn("depth:$('depth').value",js)
 def test_cancel_is_safe_and_persisted(self):
  js=(ROOT/'public/ui-v2.js').read_text(encoding='utf8')
  self.assertIn("!activeRun?.id",js)
  self.assertIn("'/cancel','POST',{run_id:run.id}",js)
  self.assertIn("rememberRun()",js)
  self.assertIn("restoreRun()",js)
  self.assertIn("run_id",js)
if __name__=='__main__':unittest.main()
