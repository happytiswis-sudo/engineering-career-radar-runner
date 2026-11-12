import unittest
from pathlib import Path

JS=(Path(__file__).resolve().parents[1]/'public/ui-v2.js').read_text(encoding='utf-8')

class StandaloneLaunchCompatibilityTests(unittest.TestCase):
 def test_old_worker_404_does_not_block_search(self):
  self.assertIn("const checked=await call('/runs?limit=35')",JS)
  self.assertIn("historyWarning=e.httpStatus===404?",JS)
  self.assertIn("const result=await call('/search','POST',p)",JS)
  self.assertIn("error.httpStatus=response.status",JS)
  # Confirm no unconditional /runs request immediately before /search dispatch.
  start=JS.index("  let liveRuns=null,historyWarning=''")
  end=JS.index("  const result=await call('/search','POST',p)",start)
  block=JS[start:end]
  self.assertIn("try{",block)
  self.assertIn("}catch(e){",block)
  self.assertIn("historyWarning=e.httpStatus===404?",block)
 def test_wrong_password_does_not_trigger_dispatch(self):
  self.assertIn("if(e.httpStatus===401||e.httpStatus===403||e.httpStatus===503)",JS)
 def test_explicit_standalone_starts_in_search(self):
  self.assertIn("url.hash='search'",JS)
  self.assertIn("const requested=location.hash.slice(1)",JS)
  self.assertIn("if(requested&&Object.prototype.hasOwnProperty.call(names,requested))initialView=requested",JS)

if __name__=='__main__':unittest.main()
