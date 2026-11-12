import unittest
import json
import io
import urllib.error
from unittest.mock import patch
from radar import assess_queue_parallel, ai_assess, sanitized_provider_http_error


class AIProviderReliabilityTests(unittest.TestCase):
    def provider(self, name):
        return {"name": name, "url": "https://example.invalid", "model": "test",
                "key": "not-a-real-key"}

    def run_queue(self, providers, behavior, queue=None):
        def fake_assess(job, cv, settings, key, provider, timeout_seconds=55):
            return behavior(job, provider)
        with patch("radar.ai_assess", side_effect=fake_assess):
            return assess_queue_parallel(
                queue or [{"id": 1}, {"id": 2}, {"id": 3}],
                "anonymized", {}, providers, deadline=__import__("time").monotonic()+30,
                workers=1)

    def test_narrouter_request_omits_incompatible_json_mode_and_validates_assessment(self):
        assessment = {"fit_score": 72, "recommendation": "Stretch", "summary": "Relevant technical work.",
            "strengths": ["CAD"], "gaps": [], "work_authorization_note": "Not stated.",
            "degree_requirement": "bachelor accepted", "requirement_evidence": [], "confidence": "medium"}
        payload = {"choices": [{"message": {"content": json.dumps(assessment)}}]}
        captured = {}
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *args): return False
        def fake_urlopen(request, timeout=0):
            captured["request"] = request
            return Response(json.dumps(payload).encode())
        provider = {"name": "NaraRouter (naraya)", "url": "https://router.naraya.ai/v1/chat/completions",
            "model": "auto/naraya.ai", "key": "test"}
        job = {"title": "Project Engineer", "company": "Example", "description": "Project engineering"}
        with patch("radar.urllib.request.urlopen", side_effect=fake_urlopen):
            result = ai_assess(job, "anonymized CV", {}, "test", provider)
        body = json.loads(captured["request"].data.decode())
        self.assertNotIn("response_format", body)
        self.assertEqual(result["score"], 72)
        self.assertEqual(result["provider"], "NaraRouter (naraya)")

    def test_http_400_detail_is_included_in_provider_failure_metrics(self):
        a, b = self.provider("Nara"), self.provider("Backup")
        def behavior(job, provider):
            if provider["name"] == "Nara":
                body = io.BytesIO(json.dumps({"error": {"message": "model payload invalid"}}).encode())
                raise urllib.error.HTTPError("https://example.invalid", 400, "Invalid", {}, body)
            return {"score": 70}
        results = self.run_queue([a, b], behavior)
        self.assertIn("HTTP 400 · model payload invalid", [x[1] for row in results for x in row[3]])
    def test_sanitized_provider_http_error_extracts_detail_and_redacts_secrets(self):
        body = json.dumps({"error": {"message":
            "Invalid model request; bearer sk-secret123456789 api_key=topsecret"}}).encode()
        exc = urllib.error.HTTPError("https://example.invalid", 400, "Invalid",
            {"Content-Type": "application/json"}, io.BytesIO(body))
        detail = sanitized_provider_http_error(exc)
        self.assertIn("Invalid model request", detail)
        self.assertNotIn("sk-secret123456789", detail)
        self.assertNotIn("topsecret", detail)
        self.assertIn("[REDACTED]", detail)

    def test_rate_limited_provider_cools_down_and_fallback_provider_succeeds(self):
        a, b = self.provider("Provider A"), self.provider("Provider B")
        calls = []
        def behavior(job, provider):
            calls.append((job["id"], provider["name"]))
            if provider["name"] == "Provider A":
                raise urllib.error.HTTPError(
                    "https://example.invalid", 429, "rate limited",
                    {"Retry-After": "120"}, None)
            return {"score": 80}
        results = self.run_queue([a, b], behavior)
        self.assertEqual(len(results), 3)
        self.assertIn((1, "Provider A"), calls)
        self.assertTrue(any(
            outcome[0] == "Provider A" and outcome[1] == "HTTP 429"
            for row in results for outcome in row[3]))
        self.assertGreaterEqual(sum(bool(row[1]) for row in results), 1)
        self.assertTrue(any(row[2] == "Provider B" for row in results))
        self.assertTrue(all(row[2] != "Provider A" for row in results if row[1] is not None))
        self.assertGreater(a["cooldown_until"], __import__("time").monotonic())

    def test_invalid_json_is_job_local_and_provider_remains_available(self):
        provider = self.provider("Provider A")
        calls = []
        def behavior(job, _provider):
            calls.append(job["id"])
            if job["id"] == 1:
                raise ValueError("AI did not return valid assessment JSON")
            return {"score": 75}
        results = self.run_queue([provider], behavior)
        self.assertIsNone(results[0][1])
        self.assertTrue(results[1][1])
        self.assertTrue(results[2][1])
        self.assertFalse(provider.get("disabled", False))
        self.assertEqual(calls, [1, 2, 3])


    def test_invalid_provider_payload_falls_back_without_disabling_provider(self):
        a, b = self.provider("Malformed"), self.provider("Backup")
        def behavior(job, provider):
            if provider["name"] == "Malformed":
                raise ValueError("AI did not return valid assessment JSON")
            return {"score": 72}
        results = self.run_queue([a, b], behavior)
        self.assertTrue(all(row[1] for row in results))
        self.assertTrue(all(row[2] == "Backup" for row in results))
        self.assertFalse(a.get("disabled", False))

    def test_forbidden_provider_is_disabled_and_fallback_takes_over(self):
        blocked, backup = self.provider("Blocked"), self.provider("Backup")
        def behavior(job, provider):
            if provider["name"] == "Blocked":
                raise urllib.error.HTTPError(
                    "https://example.invalid", 403, "forbidden", {}, None)
            return {"score": 70}
        results = self.run_queue([blocked, backup], behavior)
        self.assertTrue(blocked["disabled"])
        self.assertTrue(all(row[1] for row in results))
        self.assertTrue(all(row[2] == "Backup" for row in results))


if __name__ == "__main__":
    unittest.main()
