import unittest
from agent_engine import AGENTS, run_specialists
from radar import configured_ai_providers
from unittest.mock import patch
class AgentArchitectureTests(unittest.TestCase):
 def test_registry_relationships(self):
  self.assertEqual(len(AGENTS),36)
  seen=set()
  for agent in AGENTS:
   self.assertTrue(set(agent.depends_on).issubset(seen),agent.ident)
   seen.add(agent.ident)
  self.assertEqual(len({a.team for a in AGENTS}),6)
 def test_evidence_coordination(self):
  fake={'title':'Project Engineer','company':'Test Industrial','url':'https://example.org/job/1',
   'source':'Greenhouse','location':'Esslingen','description':'Project planning, SolidWorks, ISO 9001. Bachelor or Master degree acceptable.',
   'market':{'germany':True,'west':True,'small_city':True},
   'qualification':{'status':'review','evidence':[]},
   'hiring_support':{'visa':{'status':'not_stated'},'blue_card':{'status':'mentioned'}},
   'score':76,'matched_skills':['Project engineering'],'missing_skills':[],'check_requirements':[]}
  result=run_specialists(fake)
  self.assertEqual(result['specialists_executed'],36)
  self.assertEqual(result['degree_gate'],'review')
  self.assertEqual(result['priority'],'high_priority_review')
 def test_mercury_first_when_key_present(self):
  with patch.dict('os.environ',{'INCEPTION_API_KEY':'test-placeholder','OPENROUTER_API_KEY':'dummy','NARAROUTER_API_KEY':''},clear=True):
   configured=configured_ai_providers({})
  self.assertEqual(configured[0]['name'],'Inception Mercury 3')
  self.assertEqual(configured[0]['model'],'mercury-3')
  self.assertEqual(configured[0]['url'],'https://api.inceptionlabs.ai/v1/chat/completions')
if __name__=='__main__': unittest.main()
