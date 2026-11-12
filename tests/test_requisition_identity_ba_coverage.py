import unittest
from datetime import date
from discovery_quality import AIRPORT_ROTATING_TERMS, rotating_airport_boards
from novelty import job_key


class VacancyIdentityAndBACoverageTests(unittest.TestCase):
    def test_distinct_requisitions_on_generic_url_remain_distinct(self):
        base = {
            "title": "Quality Engineer",
            "company": "Example GmbH",
            "url": "https://careers.example/jobs",
            "source": "Example ATS",
        }
        req1 = {**base, "employer_posting_id": "REQ-100"}
        req2 = {**base, "employer_posting_id": "REQ-200"}
        self.assertNotEqual(job_key(req1), job_key(req2))
        self.assertEqual(job_key(req1), job_key({**req1, "employer_posting_id": "req-100"}))

    def test_requisition_id_is_provider_scoped(self):
        base = {
            "title": "Quality Engineer",
            "company": "Example GmbH",
            "url": "https://careers.example/jobs",
            "employer_posting_id": "REQ-100",
        }
        self.assertNotEqual(job_key({**base, "source": "Provider A"}),
                           job_key({**base, "source": "Provider B"}))

    def test_ba_query_vocabulary_contains_recovery_terms(self):
        for term in ("Ingenieur", "Maschinenbau", "Elektrotechnik",
                     "Qualitätssicherung", "Fertigung", "Instandhaltung",
                     "Luftfahrttechnik", "Automatisierungstechnik",
                     "Supply Chain"):
            self.assertIn(term, AIRPORT_ROTATING_TERMS)

    def test_ba_rotation_emits_bounded_queries_without_existing_duplicates(self):
        existing = [{"type": "bundesagentur", "city": "Stuttgart",
                     "query": "Ingenieur"}]
        added = rotating_airport_boards(existing, when=date(2026, 11, 6), limit=18)
        self.assertLessEqual(len(added), 18)
        keys = {(b["city"].casefold(), b["query"].casefold()) for b in added}
        self.assertEqual(len(keys), len(added))
        self.assertNotIn(("stuttgart", "ingenieur"), keys)
        self.assertTrue(all(b["type"] == "bundesagentur" and b["pages"] <= 2
                            for b in added))


if __name__ == "__main__":
    unittest.main()
