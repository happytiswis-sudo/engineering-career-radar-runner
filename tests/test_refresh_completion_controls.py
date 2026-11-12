import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class RefreshCompletionControlsTests(unittest.TestCase):
 def setUp(self):
  self.js=(ROOT/'public/ui-v2.js').read_text(encoding='utf8')
  self.css=(ROOT/'public/ui-v2.css').read_text(encoding='utf8')
 def test_locked_cancel_is_explained_and_unlockable(self):
  self.assertIn('Enter password to unlock Cancel #',self.js)
  self.assertIn('button.classList.toggle(\'unlock-mode\'',self.js)
  self.assertIn('button.disabled=false;',self.js)
  self.assertIn('startPassivePublishWatcher();',self.js)
  self.assertIn('.primary-action.unlock-mode',self.css)
 def test_completion_requires_matching_run_id(self):
  self.assertIn("String(latest.run_id||'')===String(run.id)",self.js)
  self.assertIn("published<started-5000",self.js)
  self.assertIn("Array.isArray(latest.jobs)",self.js)
  self.assertIn("await file('jobs.json')",self.js)
  self.assertIn("notifyCompletion('Career Radar search completed'",self.js)
 def test_no_password_stored_or_required_for_publication_watch(self):
  start=self.js.index('async function checkPublishedTrackedRun(){')
  end=self.js.index('function startPassivePublishWatcher(){',start)
  snippet=self.js[start:end]
  self.assertNotIn('srPassword',snippet)
  self.assertNotIn("call('/status",snippet)
  self.assertNotIn("localStorage.setItem('SEARCH_PASSWORD'",self.js)
 def test_history_and_new_search_remain_separate(self):
  self.assertIn("tab('results')",self.js)
  self.assertIn("loadHistory();",self.js)
if __name__=='__main__':unittest.main()
