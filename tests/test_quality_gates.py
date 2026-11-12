import unittest
from datetime import datetime, timezone
from quality_gates import freshness_gate, geographic_gate, employer_evidence_state, record_http_cooldown


class QualityGateTests(unittest.TestCase):
    def test_fresh_posting_kept(self):
        now = datetime(2026, 11, 5, tzinfo=timezone.utc)
        result = freshness_gate({"published_at": "2026-11-02"}, now=now)
        self.assertEqual(result["action"], "keep")

    def test_unknown_date_is_review_not_recent(self):
        result = freshness_gate({"published_at": ""})
        self.assertEqual(result["action"], "review")
        self.assertIsNone(result["age_days"])

    def test_old_posting_requires_verification_and_hard_gate_at_90_days(self):
        now = datetime(2026, 11, 5, tzinfo=timezone.utc)
        self.assertEqual(freshness_gate({"published_at": "2026-10-01"}, now)["action"], "verify")
        self.assertEqual(freshness_gate({"published_at": "2026-07-01"}, now)["action"], "exclude")

    def test_source_active_verification_can_keep_old_posting(self):
        now = datetime(2026, 11, 5, tzinfo=timezone.utc)
        result = freshness_gate({"published_at": "2026-07-01", "source_active_verified": True}, now)
        self.assertEqual(result["action"], "keep")

    def test_explicit_source_expiry_always_excludes(self):
        result = freshness_gate({"published_at": "2026-11-01", "listing_status": "expired_by_source_date"})
        self.assertEqual(result["action"], "exclude")
        self.assertEqual(result["reason"], "source_expiry_confirmed")

    def test_verified_inactive_page_always_excludes(self):
        result = freshness_gate({"published_at": "2026-10-01", "source_verification": {"status": "inactive"}})
        self.assertEqual(result["action"], "exclude")
        self.assertEqual(result["reason"], "source_page_inactive")

    def test_germany_location_kept_by_default(self):
        self.assertTrue(geographic_gate({"location": "Stuttgart"}, {"germany": True})["keep"])

    def test_global_remote_without_germany_evidence_rejected(self):
        self.assertFalse(geographic_gate({"location": "Remote", "remote": True}, {"germany": False})["keep"])

    def test_germany_restricted_remote_kept(self):
        self.assertTrue(geographic_gate({"location": "Remote", "remote": True,
            "remote_location_restriction": ["Germany"]}, {"germany": False})["keep"])

    def test_world_search_relaxes_geographic_gate(self):
        self.assertTrue(geographic_gate({"location": "London"}, {"germany": False}, world_search=True)["keep"])

    def test_retry_after_rate_limit_cooldown_is_bounded_and_source_specific(self):
        from datetime import datetime, timezone
        now = datetime(2026, 11, 5, tzinfo=timezone.utc)
        state = {}
        record_http_cooldown(state, {"type": "arbeitnow", "slug": "europe"}, 429, "120", now)
        entry = state["arbeitnow|europe"]
        self.assertEqual(entry["reason"], "http_429")
        self.assertEqual(entry["retry_after"], "2026-11-05T00:02:00+00:00")

    def test_stale_ats_board_404_uses_30_day_cooldown(self):
        from datetime import datetime, timezone
        now = datetime(2026, 11, 5, tzinfo=timezone.utc)
        state = {}
        record_http_cooldown(state, {"type": "lever", "slug": "old-board"}, 404, now=now)
        self.assertEqual(state["lever|old-board"]["retry_after"], "2026-12-05T00:00:00+00:00")

    def test_employer_evidence_levels_are_not_conflated(self):
        self.assertEqual(employer_evidence_state({"verification_status": "not_checked"})["state"], "discovery_only")
        self.assertEqual(employer_evidence_state({"verification_status": "website_verified"})["state"], "official_website_checked")
        self.assertEqual(employer_evidence_state({"verification_status": "website_and_careers_checked",
            "career_status": "vacancies_found", "vacancy_urls": ["https://example.de/jobs/1"]})["state"],
            "vacancy_links_verified")


if __name__ == "__main__":
    unittest.main()
