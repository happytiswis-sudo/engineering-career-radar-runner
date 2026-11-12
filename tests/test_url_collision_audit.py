import unittest
from pathlib import Path

from audit_url_collisions import audit_url_collisions


class UrlCollisionAuditTests(unittest.TestCase):
    def test_same_url_across_sources_is_one_database_key(self):
        rows = [
            {
                "url": "https://jobs.example/req/1",
                "company": "Example GmbH",
                "title": "Project Engineer",
                "location": "Stuttgart",
                "source": "ATS A",
            },
            {
                "url": "HTTPS://JOBS.EXAMPLE/REQ/1 ",
                "company": "Example GmbH",
                "title": "Project Engineer",
                "location": "Stuttgart",
                "source": "ATS B",
            },
        ]
        result = audit_url_collisions(rows)
        self.assertEqual(result["url_key_groups"], 1)
        self.assertEqual(result["duplicate_url_groups"], 1)
        self.assertEqual(result["excess_records_collapsed_by_url_key"], 1)
        self.assertEqual(result["groups_with_multiple_vacancy_signatures"], 0)
        self.assertEqual(result["collisions"][0]["sources"], ["ATS A", "ATS B"])

    def test_same_url_with_different_vacancy_details_is_flagged(self):
        rows = [
            {
                "url": "https://jobs.example/apply",
                "company": "Example GmbH",
                "title": "Project Engineer",
                "location": "Stuttgart",
                "employer_posting_id": "REQ-1",
                "source": "ATS A",
            },
            {
                "url": "https://jobs.example/apply",
                "company": "Example GmbH",
                "title": "Maintenance Engineer",
                "location": "Darmstadt",
                "employer_posting_id": "REQ-2",
                "source": "ATS B",
            },
        ]
        result = audit_url_collisions(rows)
        self.assertEqual(result["groups_with_multiple_vacancy_signatures"], 1)
        self.assertEqual(result["groups_with_multiple_titles"], 1)
        self.assertEqual(result["groups_with_multiple_locations"], 1)
        self.assertEqual(result["groups_with_multiple_posting_ids"], 1)

    def test_url_key_matches_supabase_raw_lower_trim_expression(self):
        rows = [
            {"url": "https://jobs.example/req?utm_source=one", "company": "A", "title": "Engineer"},
            {"url": "https://jobs.example/req?utm_source=two", "company": "A", "title": "Engineer"},
            {"url": " https://jobs.example/REQ?utm_source=one ", "company": "A", "title": "Engineer"},
        ]
        result = audit_url_collisions(rows)
        self.assertEqual(result["url_key_groups"], 2)
        self.assertEqual(result["duplicate_url_groups"], 1)
        self.assertEqual(result["excess_records_collapsed_by_url_key"], 1)

    def test_missing_urls_are_counted_but_not_grouped(self):
        result = audit_url_collisions([
            {"company": "A", "title": "Engineer"},
            {"url": "", "company": "B", "title": "Technician"},
        ])
        self.assertEqual(result["missing_url_records"], 2)
        self.assertEqual(result["url_key_groups"], 0)
        self.assertEqual(result["duplicate_url_groups"], 0)

    def test_report_redacts_url_query_values(self):
        result = audit_url_collisions([
            {"url": "https://jobs.example/apply?token=secret", "title": "A"},
            {"url": "https://jobs.example/apply?token=secret", "title": "B"},
        ])
        collision = result["collisions"][0]
        self.assertNotIn("secret", collision["url_host"])
        self.assertNotIn("token", collision["url_host"])
        self.assertNotIn("/apply", collision["url_host"])
        self.assertEqual(len(collision["url_fingerprint"]), 16)


    def test_audit_workflow_is_read_only_and_does_not_invoke_ai(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "audit_url_collisions.py").read_text(encoding="utf-8")
        workflow = (root / ".github" / "workflows" / "audit-url-collisions.yml").read_text(encoding="utf-8")
        self.assertIn("hf_hub_download", script)
        self.assertNotIn("HfApi", script)
        self.assertNotIn("upload_file(", script)
        self.assertNotIn("upload_folder(", script)
        self.assertNotIn("execute_sql", script + workflow)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY", script + workflow)
        self.assertIn(".github/collision-audit-requests/**", workflow)
        self.assertIn("audit_url_collisions.py", workflow)


if __name__ == "__main__":
    unittest.main()
