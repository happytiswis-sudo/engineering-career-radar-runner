import unittest
from unittest.mock import patch
from serpapi_google_jobs import fetch_google_jobs

class SerpApiPaginationTests(unittest.TestCase):
    def test_paginates_with_next_page_token_and_deduplicates_tracking_urls(self):
        calls = []
        pages = [
            {"search_metadata": {"status": "Success"}, "jobs_results": [
                {"title": "Engineer", "company_name": "A", "location": "Germany",
                 "share_link": "https://www.google.com/jobs?id=1&utm_source=x"}],
             "serpapi_pagination": {"next_page_token": "page-two"}},
            {"search_metadata": {"status": "Success"}, "jobs_results": [
                {"title": "Engineer", "company_name": "A", "location": "Germany",
                 "share_link": "https://www.google.com/jobs?id=1&utm_source=y"},
                {"title": "Technician", "company_name": "B", "location": "Germany",
                 "apply_options": [{"link": "https://jobs.example.com/2"}]}]},
        ]
        def request(url, retries=0):
            calls.append(url)
            return pages.pop(0)
        board = {"queries": ["mechanical engineer"], "query_budget": 1, "pages_per_query": 2}
        with patch.dict("os.environ", {"SERPAPI_API_KEY": "fake-secret"}):
            jobs = fetch_google_jobs(board, request)
        self.assertEqual(len(calls), 2)
        self.assertIn("next_page_token=page-two", calls[1])
        self.assertEqual(len(jobs), 2)
        self.assertEqual(board["serpapi_run_stats"]["pagination_pages"], 1)
        self.assertEqual(board["serpapi_run_stats"]["provider_rows"], 3)
        self.assertEqual(board["serpapi_run_stats"]["valid_postings"], 2)

    def test_requires_secret(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "SERPAPI_API_KEY"):
                fetch_google_jobs({"queries": ["engineer"]}, lambda *a, **k: {})

if __name__ == "__main__":
    unittest.main()