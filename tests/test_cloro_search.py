import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cloro_search
from deep_search import validate_request, cloro_boards


class CloroSearchTests(unittest.TestCase):
    def test_cloro_is_accepted_as_search_source(self):
        request = validate_request({"sources": ["cloro", "ba"], "roles": ["Fertigungsingenieur"]})
        self.assertIn("cloro", request["sources"])

    def test_query_planner_is_bounded_and_track_relevant(self):
        boards = cloro_boards({"depth": "deep", "roles": ["UAV Engineer"],
                               "tracks": [], "cities": [], "region": "west"})
        self.assertLessEqual(len(boards), cloro_search.MAX_QUERIES)
        self.assertTrue(all(board["type"] == "cloro" for board in boards))
        self.assertTrue(all("UAV Engineer" in board["query"] for board in boards))

    def test_accepts_job_page_and_rejects_generic_company_page(self):
        self.assertTrue(cloro_search._is_job_result({
            "title": "Fertigungsingenieur Jobs", "snippet": "Apply now, requirements",
            "link": "https://example.de/jobs/fertigungsingenieur"
        }))
        self.assertFalse(cloro_search._is_job_result({
            "title": "Example GmbH Careers", "snippet": "We are hiring engineers",
            "link": "https://example.de/about/careers"
        }))

    def test_normalizes_google_organic_job_result(self):
        response = {"result": {"organicResults": [{
            "title": "Fertigungsingenieur (m/w/d) Jobs",
            "snippet": "Aufgaben und Anforderungen. Jetzt bewerben.",
            "link": "https://example.de/jobs/fertigungsingenieur",
            "position": 3
        }]}}
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): pass
        with patch.dict(os.environ, {"CLORO_API_KEY_1": "test-key"}), \
             patch("cloro_search.urllib.request.urlopen", return_value=FakeResponse()), \
             patch("cloro_search.json.load", return_value=response):
            jobs = cloro_search.fetch_cloro_jobs({"query": "Fertigungsingenieur", "country": "de"})
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["source"], "Cloro Google organic search")
        self.assertEqual(jobs[0]["cloro_rank"], 3)
        self.assertEqual(jobs[0]["url"], "https://example.de/jobs/fertigungsingenieur")

    def test_missing_key_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "cloro_api_keys_missing"):
                cloro_search.fetch_cloro_jobs({"query": "jobs"})


if __name__ == "__main__":
    unittest.main()
