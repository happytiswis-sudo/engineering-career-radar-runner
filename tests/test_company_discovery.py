import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import company_discovery as cd

class CompanyDiscoveryTests(unittest.TestCase):
    def test_query_plan_prioritizes_west_and_includes_nationwide_state(self):
        plan = cd.build_query_plan(run_rotation=0, budget=3)
        self.assertEqual(len(plan), 3)
        self.assertEqual(plan[0]["region_priority"], "west")
        self.assertEqual(plan[1]["region_priority"], "west")
        self.assertEqual(plan[2]["region_priority"], "national")
        self.assertTrue(all(x["state"] for x in plan))

    def test_normal_scan_pairs_one_western_and_one_national_state(self):
        plan = cd.build_query_plan(run_rotation=0, budget=2)
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0]["region_priority"], "west")
        self.assertEqual(plan[1]["region_priority"], "national")

    def test_rotation_changes_state_or_industry_coverage(self):
        a = cd.build_query_plan(run_rotation=1, budget=3)
        b = cd.build_query_plan(run_rotation=2, budget=3)
        self.assertNotEqual([(x["state"], x["industry"]) for x in a],
                            [(x["state"], x["industry"]) for x in b])

    def test_directory_and_social_results_are_not_company_websites(self):
        for url in ("https://www.linkedin.com/company/acme",
                    "https://www.gelbeseiten.de/gsbiz/acme",
                    "https://jobs.personio.de/acme",
                    "https://boards.greenhouse.io/acme"):
            self.assertIsNone(cd._candidate_from_result(
                {"title": "ACME GmbH", "link": url, "snippet": "Manufacturer"},
                {"state": "Hessen", "region_priority": "west",
                 "industry": "Maschinenbau", "industry_group": "engineering",
                 "query": "test"}, "2026-11-01T00:00:00Z"))

    def test_safe_url_rejects_http_and_local_hosts(self):
        self.assertEqual(cd._safe_http_url("http://example.com"), "")
        self.assertEqual(cd._safe_http_url("https://127.0.0.1"), "")
        self.assertEqual(cd._safe_http_url("https://example.com"), "https://example.com/")

    def test_missing_serpapi_key_preserves_existing_company_records(self):
        prior = [{"company": "Example GmbH", "domain": "example.de",
                  "verification_status": "website_verified"}]
        with patch.dict("os.environ", {"SERPAPI_API_KEY": "", "SERPER_API_KEY": "", "CLORO_API_KEY_1": "", "CLORO_API_KEY_2": "", "SEARXNG_BASE_URL": ""}):
            result = cd.discover_german_companies(existing=prior, api_key="")
        self.assertEqual(result["status"], "not_configured")
        self.assertEqual(result["companies"][0]["domain"], "example.de")

    def test_no_career_page_with_contact_is_a_hidden_opportunity_candidate(self):
        candidate = {"company": "Example GmbH", "website": "https://example.de/"}
        homepage = """<html><head><title>Example</title></head>
          <body><a href="/kontakt">Kontakt</a><p>Industrial products</p></body></html>"""
        with patch.object(cd, "_robots_allowed", return_value=True), \
             patch.object(cd, "_read_page", return_value=("https://example.de/", homepage)):
            result = cd.verify_company(candidate)
        self.assertEqual(result["career_status"], "no_public_careers_page")
        self.assertIsNone(result["open_vacancy_count"])
        self.assertTrue(result["hidden_opportunity_candidate"])

    def test_explicit_no_openings_is_a_hidden_opportunity_candidate(self):
        candidate = {"company": "Example GmbH", "website": "https://example.de/"}
        homepage = """<html><head><title>Example</title></head><body>
          <a href="/karriere">Karriere</a><a href="/kontakt">Kontakt</a></body></html>"""
        careers = """<html><body><h1>Karriere</h1>
          <p>Derzeit keine offenen Stellen.</p></body></html>"""
        with patch.object(cd, "_robots_allowed", return_value=True), \
             patch.object(cd, "_read_page", side_effect=[
                 ("https://example.de/", homepage),
                 ("https://example.de/kontakt", "<html><body>Kontakt</body></html>"),
                 ("https://example.de/karriere", careers)]):
            result = cd.verify_company(candidate)
        self.assertEqual(result["career_status"], "checked_no_openings")
        self.assertTrue(result["hidden_opportunity_candidate"])
        self.assertEqual(result["open_vacancy_count"], 0)

    def test_generic_mailbox_is_read_from_official_contact_page(self):
        candidate = {"company": "Example GmbH", "website": "https://example.de/"}
        homepage = """<html><body><a href="/karriere">Karriere</a>
          <a href="/kontakt">Kontakt</a></body></html>"""
        contact = """<html><body><a href="mailto:jobs@example.de">Jobs</a></body></html>"""
        careers = """<html><body><p>Derzeit keine offenen Stellen.</p></body></html>"""
        with patch.object(cd, "_robots_allowed", return_value=True), \
             patch.object(cd, "_read_page", side_effect=[
                 ("https://example.de/", homepage),
                 ("https://example.de/kontakt", contact),
                 ("https://example.de/karriere", careers)]):
            result = cd.verify_company(candidate)
        self.assertEqual(result["public_contact_email"], "jobs@example.de")
        self.assertEqual(result["contact_source_url"], "https://example.de/kontakt")

    def test_quality_metrics_keep_evidence_levels_separate(self):
        rows = [
            {"verification_status": "website_verified", "career_status": "no_public_careers_page",
             "hidden_opportunity_candidate": True, "contact_url": "https://example.de/kontakt"},
            {"verification_status": "website_and_careers_checked", "career_status": "vacancies_found",
             "vacancy_urls": ["https://example.de/jobs/1", "https://example.de/jobs/2"]},
            {"verification_status": "not_checked", "career_status": "not_checked",
             "hidden_opportunity_candidate": False}
        ]
        metrics = cd.company_quality_metrics(rows)
        self.assertEqual(metrics["verified_websites"], 2)
        self.assertEqual(metrics["verified_careers_pages"], 1)
        self.assertEqual(metrics["public_vacancy_links"], 2)
        self.assertEqual(metrics["contactable_hidden_opportunity_prospects"], 1)
        self.assertEqual(metrics["evidence_states"]["official_website_checked"], 1)
        self.assertEqual(metrics["evidence_states"]["vacancy_links_verified"], 1)
        self.assertEqual(metrics["evidence_states"]["discovery_only"], 1)

    def test_failed_crawl_never_means_no_openings(self):
        candidate = {"company": "Example GmbH", "website": "https://example.de/"}
        with patch.object(cd, "_robots_allowed", return_value=True), \
             patch.object(cd, "_read_page", side_effect=TimeoutError()):
            result = cd.verify_company(candidate)
        self.assertEqual(result["career_status"], "not_checked")
        self.assertIsNone(result.get("open_vacancy_count"))
        self.assertFalse(result["hidden_opportunity_candidate"])

    def test_serper_is_used_when_serpapi_rate_limited(self):
        import urllib.error
        error = urllib.error.HTTPError("https://serpapi.com/search.json", 429, "rate limited", {}, None)
        with patch.object(cd, "_serpapi_search", side_effect=error), \
             patch.object(cd, "_serper_search", return_value=[
                 {"title": "Example GmbH", "link": "https://example.de/", "snippet": "Industrial manufacturer"}]):
            results, provider = cd._search_company_query("Maschinenbau NRW", "primary", "fallback")
        self.assertEqual(len(results), 1)
        self.assertIn("Serper fallback", provider)

    def test_serper_can_run_without_serpapi_key(self):
        with patch.object(cd, "_serper_search", return_value=[
            {"title": "Example GmbH", "link": "https://example.de/", "snippet": "Manufacturer"}]):
            results, provider = cd._search_company_query("Maschinenbau Hessen", "", "fallback")
        self.assertEqual(provider, "Serper")
        self.assertEqual(results[0]["link"], "https://example.de/")

    def test_cloro_uses_google_serp_and_parses_organic_results(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,*args): return b'{"result":{"organicResults":[{"title":"Acme GmbH","link":"https://acme.de","snippet":"Engineering"}]}}'
        with patch.object(cd.urllib.request, "urlopen", return_value=FakeResponse()) as mocked:
            rows=cd._cloro_search("Maschinenbau NRW","secret-key")
        self.assertEqual(rows[0]["link"],"https://acme.de")
        req=mocked.call_args.args[0]
        self.assertEqual(req.get_header("Authorization"),"Bearer secret-key")

    def test_two_cloro_accounts_are_used_sequentially_when_first_exhausted(self):
        import urllib.error
        exhausted=urllib.error.HTTPError("https://api.cloro.dev",403,"Forbidden",{},None)
        exhausted.read=lambda n=-1:b'{"error":"Insufficient credits"}'
        with patch.object(cd,"_cloro_search",side_effect=[RuntimeError("cloro_credits_exhausted"),
                [{"title":"Acme","link":"https://acme.de","snippet":"Engineering"}]]) as call:
            rows,provider=cd._search_company_query("query","","",["key-one","key-two"])
        self.assertEqual(len(rows),1)
        self.assertIn("Cloro account",provider)
        self.assertEqual(call.call_count,2)

    def test_searxng_parses_json_results(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,*args): return b'{"results":[{"title":"Acme","url":"https://acme.de","content":"Engineering"}]}'
        with patch.object(cd.urllib.request,"urlopen",return_value=FakeResponse()) as mocked:
            rows=cd._searxng_search("query","https://search.example.org","test-token")
            req=mocked.call_args.args[0]
            self.assertEqual(req.get_header("Authorization"),"Bearer test-token")
        self.assertEqual(rows[0]["link"],"https://acme.de")

    def test_cloro_fallback_used_when_serper_is_rate_limited(self):
        import urllib.error
        error=urllib.error.HTTPError("https://google.serper.dev/search",429,"rate limited",{},None)
        with patch.object(cd,"_serper_search",side_effect=error), \
             patch.object(cd,"_cloro_search",return_value=[{"title":"Acme","link":"https://acme.de","snippet":"Engineering"}]):
            rows,provider=cd._search_company_query("query","","key",["cloro-key"])
        self.assertEqual(len(rows),1)
        self.assertIn("Cloro",provider)

if __name__ == "__main__":
    unittest.main()
