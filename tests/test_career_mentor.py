import unittest
from career_mentor import build_mentor_review


class CareerMentorTests(unittest.TestCase):
    def test_separates_non_design_source_supply_from_shortlist_results(self):
        snapshot={"run_id":"test-run","jobs":[
            {"career_track":"Project Engineering & Delivery"},
            {"career_track":"Project Engineering & Delivery"}],
            "source_query_metrics":[
                {"industry_track":"Operations & Technical Delivery","raw_postings":12,"cv_matches":0,"unseen_recent_cv_matches":0},
                {"industry_track":"Supply Chain, Planning & Procurement","raw_postings":0,"cv_matches":0,"unseen_recent_cv_matches":0}],
            "source_failures":[],"source_metrics":{},"ai_evaluated":1,
            "ai_review_jobs_attempted":2,"ai_review_sample_size":4,
            "ai_provider_health":{"Provider A":{"attempts":3,"success":1,"failed":2}}}
        review=build_mentor_review(snapshot,{})
        by_track={x["track"]:x for x in review["track_coverage"]}
        self.assertEqual(by_track["Operations & Technical Delivery"]["status"],"source_returned_jobs_but_none_shortlisted")
        self.assertEqual(by_track["Supply Chain, Planning & Procurement"]["status"],"searched_no_raw_results")
        self.assertEqual(review["summary"]["non_design_tracks_with_results"],0)
        self.assertEqual(review["summary"]["ai_provider_attempts"],3)
        self.assertEqual(review["summary"]["ai_valid_provider_responses"],1)
        self.assertEqual(review["summary"]["ai_valid_response_rate"],0.3333)
        self.assertEqual(review["summary"]["ai_jobs_with_provider_attempts"],2)
        self.assertEqual(review["track_coverage_scope"]["query_and_raw_posting_telemetry"],
                         "Federal Employment Agency (BA) industry queries only")
        self.assertGreaterEqual(len(review["recommendations"]),2)

    def test_ai_rate_counts_provider_calls_not_attempted_jobs(self):
        review=build_mentor_review({"jobs":[],"ai_evaluated":2,
            "ai_review_jobs_attempted":2,"ai_review_sample_size":3,
            "ai_provider_health":{"A":{"attempts":2,"success":2,"failed":0},
                                  "B":{"attempts":4,"success":0,"failed":4}}},{})
        self.assertEqual(review["summary"]["ai_provider_attempts"],6)
        self.assertEqual(review["summary"]["ai_valid_provider_responses"],2)
        self.assertEqual(review["summary"]["ai_valid_response_rate"],0.3333)

    def test_mentor_surfaces_provider_failure_reasons(self):
        review=build_mentor_review({"jobs":[],"ai_evaluated":1,
            "ai_review_sample_size":2,
            "ai_provider_health":{"OpenRouter":{"attempts":3,"success":1,"failed":2}},
            "ai_failure_counts":{"OpenRouter · invalid_assessment_json":2,
                                 "OpenRouter · HTTP 429":1}}, {})
        self.assertEqual(review["ai_provider_failure_reasons"][0]["reason"],
                         "OpenRouter · invalid_assessment_json")
        self.assertEqual(review["summary"]["ai_failure_reason_count"],3)

    def test_official_international_source_is_not_called_sponsorship(self):
        review=build_mentor_review({"jobs":[]},{})
        self.assertIn("not proof of visa sponsorship",review["official_international_source"]["relationship"])


if __name__=="__main__":
    unittest.main()
