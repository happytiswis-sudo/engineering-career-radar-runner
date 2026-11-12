import unittest
from retrieval_intelligence import canonical_url, measure_source_outcomes, allocate_query_capacity, diagnose_sources


class RetrievalIntelligenceTests(unittest.TestCase):
    def test_canonical_url_strips_tracking_but_preserves_requisition_ids(self):
        a = "https://www.example.com/jobs/1?job_id=42&utm_source=google"
        b = "https://example.com/jobs/1?job_id=42&fbclid=abc"
        c = "https://example.com/jobs/1?job_id=43"
        self.assertEqual(canonical_url(a), canonical_url(b))
        self.assertNotEqual(canonical_url(a), canonical_url(c))

    def test_url_funnel_counts_raw_unique_usable_and_new_separately(self):
        outcomes = [{"source": "ats", "family": "ats", "attempted_queries": 2,
            "completed_queries": 2, "raw_urls": [
                "https://www.example.com/job/1?utm_source=x",
                "https://example.com/job/1", "https://example.com/job/2"],
            "postings": [
                {"title": "Engineer", "company": "A", "url": "https://example.com/job/1"},
                {"title": "Missing employer", "url": "https://example.com/job/2"},
            ]}]
        measured = measure_source_outcomes(outcomes, previously_seen={"https://example.com/job/1"})
        self.assertEqual(measured["totals"]["raw_urls_encountered"], 3)
        self.assertEqual(measured["totals"]["unique_canonical_urls"], 2)
        self.assertEqual(measured["totals"]["usable_postings"], 1)
        self.assertEqual(measured["totals"]["newly_discovered_vacancies"], 0)

    def test_adaptive_allocation_keeps_family_floor_and_rewards_yield(self):
        result = allocate_query_capacity([
            {"source": "google", "family": "aggregator", "attempted_queries": 20,
             "usable_postings": 20, "max_queries": 20},
            {"source": "ats", "family": "employer_ats", "attempted_queries": 20,
             "usable_postings": 1, "max_queries": 20},
            {"source": "public_feed", "family": "public_feed", "attempted_queries": 20,
             "usable_postings": 0, "max_queries": 20},
        ], total_budget=12, family_floor=1)
        allocations = result["allocations"]
        self.assertEqual(sum(allocations.values()), 12)
        self.assertGreater(allocations["google"], allocations["ats"])
        self.assertGreaterEqual(allocations["ats"], 1)
        self.assertGreaterEqual(allocations["public_feed"], 1)

    def test_missing_credentials_stale_boards_and_errors_are_actionable(self):
        findings = diagnose_sources([
            {"source": "serpapi", "family": "aggregator", "credential_required": True,
             "credential_present": False, "status": "unconfigured"},
            {"source": "old_board", "family": "ats", "last_success_days": 30,
             "error_code": "404", "attempted_queries": 5, "usable_postings": 0},
            {"source": "slow_feed", "family": "feed", "attempted_queries": 10,
             "usable_postings": 0},
        ])
        signals = {x["signal"] for x in findings}
        self.assertIn("missing_credential", signals)
        self.assertIn("stale_or_invalid_board", signals)
        self.assertIn("stale_source", signals)
        self.assertIn("low_usable_yield", signals)


    def test_cross_source_overlap_is_not_double_counted_in_global_funnel(self):
        outcomes = [
            {"source": "ats", "attempted_queries": 1, "raw_urls": ["https://a.example/jobs/1"],
             "postings": [{"title": "Engineer", "company": "A", "url": "https://a.example/jobs/1"}]},
            {"source": "aggregator", "attempted_queries": 1, "raw_urls": ["https://www.a.example/jobs/1?utm_source=x"],
             "postings": [{"title": "Engineer", "company": "A", "url": "https://www.a.example/jobs/1?utm_source=x"}]},
        ]
        measured = measure_source_outcomes(outcomes)
        self.assertEqual(measured["totals"]["raw_urls_encountered"], 2)
        self.assertEqual(measured["totals"]["unique_canonical_urls"], 1)
        self.assertEqual(measured["totals"]["usable_postings"], 1)
        self.assertEqual(measured["totals"]["newly_discovered_vacancies"], 1)

if __name__ == "__main__":
    unittest.main()
