"""Regression for scan 40601633365: mandatory degree exclusions must not abort job search."""
import unittest
from unittest.mock import patch

from career_intelligence import capability_assessment,run_extended_agents
from radar import evaluate_rule

class MandatoryIneligibleCapabilityTests(unittest.TestCase):
 def test_ineligible_capability_has_stable_fields(self):
  job={'title':'Quality Technician','qualification':{'status':'excluded'},
       'matched_skills':['CAD'],'score_components':{'role':38}}
  result=capability_assessment(job)
  self.assertEqual(result['tier'],'mandatory_ineligible')
  self.assertEqual(result['capability_score'],0)
  self.assertFalse(result['transferable'])
  self.assertIs(result['open_to_junior_roles'],False)

 def test_extended_agent_review_does_not_crash_for_excluded_job(self):
  job={'title':'Production Technician','qualification':{'status':'excluded'},
       'published_at':'2026-10-28','hiring_support':{},
       'market':{'germany':True},'matched_skills':['Manufacturing']}
  result=run_extended_agents(job)
  self.assertEqual(result['specialists_executed'],18)
  self.assertEqual(result['capability']['tier'],'mandatory_ineligible')
  self.assertEqual(result['agent_findings'][9]['status'],'standard')
  self.assertEqual(result['agent_findings'][-1]['status'],'design_adjacent_or_limited_evidence')

 def test_full_evaluate_rule_keeps_qualification_exclusion_without_exception(self):
  settings={'catalog_roles':[],'role_patterns':[],
   'skills':[{'label':'CAD','aliases':['solidworks'],'weight':4},
             {'label':'Project coordination','aliases':['project coordination'],'weight':4}],
   'candidate_education':{'highest_completed':'bachelor'},'west_germany':{}}
  job={'title':'Factory Operator','company':'Example Factory',
       'description':'The factory uses solidworks and project coordination for production maintenance. '+
                     ('Manufacturing quality and production safety. '*5),
       'location':'Stuttgart, Germany','url':'https://example.org/jobs/1',
       'source':'Sample employer','remote':False}
  with patch('radar.qualification_gate',return_value={
       'status':'excluded','reason':'Completed higher degree is mandatory'}):
   evaluated=evaluate_rule(job,settings,'Solidworks CAD and project coordination experience')
  self.assertIsNotNone(evaluated)
  self.assertEqual(evaluated['qualification']['status'],'excluded')
  self.assertEqual(evaluated['capability']['tier'],'mandatory_ineligible')
  self.assertEqual(evaluated['capability']['capability_score'],0)
  self.assertNotEqual(evaluated.get('application_path'),'capable_for_adjacent_or_junior')
  self.assertFalse(evaluated['capability']['open_to_junior_roles'])

if __name__=='__main__':unittest.main()
