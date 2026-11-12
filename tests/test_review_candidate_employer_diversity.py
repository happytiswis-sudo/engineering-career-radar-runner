import unittest
from discovery_quality import review_candidates


class ReviewCandidateEmployerDiversityTests(unittest.TestCase):
    def test_keeps_distinct_openings_at_same_employer(self):
        jobs = [
            {"title": f"Engineer Role {i}", "company": "Large Employer",
             "rule_score": 90-i, "published_at": "2026-11-05",
             "url": f"https://example.test/jobs/{i}"}
            for i in range(5)
        ]
        jobs += [
            {"title": "Quality Engineer", "company": "Other Employer",
             "rule_score": 70, "published_at": "2026-11-05",
             "url": "https://example.test/other"}
        ]
        selected = review_candidates(jobs, limit=4, prior_keys=set())
        self.assertEqual(len(selected), 4)
        self.assertEqual(sum(j["company"] == "Large Employer" for j in selected), 3)
        self.assertTrue(any(j["company"] == "Other Employer" for j in selected))


if __name__ == "__main__":
    unittest.main()
