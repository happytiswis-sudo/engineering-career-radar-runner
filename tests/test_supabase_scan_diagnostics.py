import unittest

from publish_supabase_jobs import build_diagnostics, normalize_source_metrics


class ScanDiagnosticsPublisherTests(unittest.TestCase):
    def test_bounded_diagnostics_capture_filters_and_ai_fallback(self):
        data = {
            "target_vacancies": 1500, "target_met": False,
            "search_request": {"region": "germany", "min_score": 70, "support": "all",
                "freshness": "all", "depth": "deep", "capacity": "maximum_safe",
                "cities": [], "roles": [], "tracks": [], "sources": ["ba", "ats"]},
            "discovery_audit": {"unique_collected": 19144, "rule_screen_rejected": 14518,
                "preliminary_score_rejected": 0, "directory_non_germany_skipped": 12276,
                "geography_rejected": 1858, "before_user_filters": 2768,
                "after_user_filters": 167, "rejection_counts": {"score": 2600, "location": 2},
                "first_blocker_counts": {"score": 2599, "location": 2},
                "multiple_rejections": 1, "examples": [{"private": "omit"}]},
            "freshness_gate_diagnostics": {"excluded_older_than_90d": 27},
            "source_failure_counts": {"personio": 2, "arbeitnow_cooldown": 1},
            "source_failures": [{"source": "arbeitnow", "error": "HTTP 429 cooldown"}],
            "source_metrics": [{"source": "BA", "boards": 5, "succeeded": 4,
                                "returned": 12, "errors": 1, "queries": ["Berlin"]}],
            "source_query_metrics": [{"city": "Frankfurt", "unseen_cv_matches": 0}],
            "source_board_metrics": [{"board": "example-board", "cv_matches": 0}],
            "duplicate_suppression": {"registry_available": True, "active": False,
                "candidates_matching_registry": 138, "suppressed": 0},
            "ai_provider_usage": {"Inception Mercury 3": 32},
            "ai_failure_counts": {"NaraRouter · HTTP 400": 21},
            "ai_error_details": [{"provider": "NaraRouter", "error": "HTTP 400 · invalid model"}],
            "ai_provider_health": {"NaraRouter": {"valid": 0, "failures": 23}},
            "ai_review_sample_size": 50, "ai_review_jobs_attempted": 32,
            "ai_review_deadline_exhausted": False, "ai_review_coverage": 0.2286,
            "runtime_metrics": {"scanner_seconds": 800}, "sources_attempted": 760,
            "sources_succeeded": 758, "sources_with_postings": 665,
            "catalog_track_count": 34, "ai_cv_content": "must not be copied"}
        jobs = [{"career_track": "Mechanical Design"}, {"career_track": "Manufacturing"}]
        result = build_diagnostics(data, jobs)
        self.assertEqual(result["search_request_summary"]["min_score"], 70)
        self.assertEqual(result["discovery_audit"]["before_user_filters"], 2768)
        self.assertEqual(result["filter_diagnostics"]["rejection_counts"]["score"], 2600)
        self.assertEqual(result["freshness_gate_diagnostics"]["excluded_older_than_90d"], 27)
        self.assertEqual(result["ai_failure_counts"]["NaraRouter · HTTP 400"], 21)
        self.assertEqual(result["ai_error_details"][0]["error"], "HTTP 400 · invalid model")
        self.assertEqual(result["ai_provider_usage"]["Inception Mercury 3"], 32)
        self.assertEqual(result["tracks_with_results"], 2)
        self.assertNotIn("examples", result["discovery_audit"])
        self.assertNotIn("ai_cv_content", result)
        self.assertNotIn("jobs", result)

    def test_normalize_source_metrics_accepts_scanner_provider_dictionary(self):
        # radar.py emits source_metrics as a provider-keyed dict, not a row list.
        source_metrics = {
            "bundesagentur": {
                "boards": 12, "succeeded": 11, "errors": 1,
                "returned": 345, "elapsed_seconds": 10.25,
                "slowest_seconds": 2.4,
            },
            "greenhouse": {
                "boards": 8, "succeeded": 8, "errors": 0,
                "returned": 52,
            },
        }
        result = normalize_source_metrics(source_metrics)
        self.assertEqual(len(result), 2)
        ba = next(row for row in result if row["provider"] == "bundesagentur")
        gh = next(row for row in result if row["provider"] == "greenhouse")
        self.assertEqual(ba["queries_attempted"], 12)
        self.assertEqual(ba["successful_responses"], 11)
        self.assertEqual(ba["jobs_found"], 345)
        self.assertEqual(ba["failures"], 1)
        self.assertEqual(ba["details"]["elapsed_seconds"], 10.25)
        self.assertEqual(ba["details"]["slowest_seconds"], 2.4)
        self.assertEqual(gh["queries_attempted"], 8)
        self.assertEqual(gh["successful_responses"], 8)
        self.assertEqual(gh["jobs_found"], 52)

    def test_normalize_source_metrics(self):
        rows = [
            {"source": "BA", "boards": 5, "succeeded": 4, "returned": 12,
             "errors": 1, "queries": ["Berlin"]},
            {"provider": "Mercury", "engine": "model-a", "queries_attempted": 2,
             "successful_responses": 2, "jobs_found": 7, "credits_used": 0.5}]
        result = normalize_source_metrics(rows)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["provider"], "BA")
        self.assertEqual(result[0]["queries_attempted"], 5)
        self.assertEqual(result[0]["successful_responses"], 4)
        self.assertEqual(result[0]["jobs_found"], 12)
        self.assertEqual(result[0]["details"]["queries"], ["Berlin"])
        self.assertEqual(result[1]["engine"], "model-a")
        self.assertEqual(result[1]["credits_used"], 0.5)
        self.assertEqual(len(normalize_source_metrics([{"source": str(i)} for i in range(600)])), 500)


if __name__ == "__main__":
    unittest.main()
