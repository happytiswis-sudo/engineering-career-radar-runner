import unittest
from radar import evaluate_rule

SETTINGS={'catalog_roles':[],'role_patterns':[],
 'skills':[{'label':'CAD','aliases':['solidworks'],'weight':4},
           {'label':'Project coordination','aliases':['project coordination'],'weight':4}],
 'west_germany':{},'candidate_education':{'highest_completed':'bachelor'}}

def job(title,description):
 return {'company':'Example Factory','title':title,'description':description,
   'location':'England, UK','url':'https://example.org/jobs/123','source':'Employer', 'remote':False}

class AdjacentEvidenceRecoveryTests(unittest.TestCase):
 def test_uncatalogued_lower_level_role_with_two_cv_skills_is_reviewed(self):
  advert='The factory team supports solidworks mechanical changes and project coordination for operational engineering. '+('Safety and documented review procedures. '*3)
  result=evaluate_rule(job('Factory Operator',advert),SETTINGS,'Solidworks CAD design, project coordination')
  self.assertIsNotNone(result)
  self.assertEqual(result['career_track'],'CV-evidenced adjacent industrial role')
  self.assertEqual(len(result['matched_skills']),2)
 def test_single_matching_skill_does_not_trigger_broad_recall(self):
  advert='The factory team operates and maintains equipment using solidworks as a documented tool. '+('Safety and procedural compliance. '*4)
  self.assertIsNone(evaluate_rule(job('Factory Operator',advert),SETTINGS,'Solidworks CAD design, project coordination'))
 def test_unrelated_title_not_promoted_by_generic_description(self):
  advert='Solidworks and project coordination used to manage a restaurant social marketing campaign. '+('Support. '*20)
  self.assertIsNone(evaluate_rule(job('Restaurant Host',advert),SETTINGS,'Solidworks CAD design, project coordination'))

if __name__=='__main__':unittest.main()
