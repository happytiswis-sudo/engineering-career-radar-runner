import io
import json
import unittest
from unittest.mock import patch
from radar import ai_assess


class ProviderJsonModeCompatibilityTests(unittest.TestCase):
    def test_mercury_request_uses_json_mode(self):
        assessment = {
            "fit_score": 72, "recommendation": "Stretch",
            "summary": "Relevant engineering work.", "strengths": ["CAD"],
            "gaps": [], "work_authorization_note": "Not stated.",
            "degree_requirement": "bachelor accepted", "requirement_evidence": [],
            "confidence": "medium"
        }
        captured = {}
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *args): return False
        def fake_urlopen(request, timeout=0):
            captured["body"] = json.loads(request.data.decode())
            return Response(json.dumps({"choices":[{"message":{"content":json.dumps(assessment)}}]}).encode())
        provider = {"name":"Inception Mercury 3","url":"https://example.invalid/v1/chat/completions",
                    "model":"mercury-3","key":"test"}
        job = {"title":"Project Engineer","company":"Example","description":"Project engineering"}
        with patch("radar.urllib.request.urlopen",side_effect=fake_urlopen):
            result=ai_assess(job,"anonymized CV",{},"test",provider)
        self.assertEqual(captured["body"]["response_format"],{"type":"json_object"})
        self.assertEqual(result["score"],72)

    def test_nararouter_request_avoids_incompatible_json_mode(self):
        assessment = {
            "fit_score": 72, "recommendation": "Stretch",
            "summary": "Relevant engineering work.", "strengths": ["CAD"],
            "gaps": [], "work_authorization_note": "Not stated.",
            "degree_requirement": "bachelor accepted", "requirement_evidence": [],
            "confidence": "medium"
        }
        captured = {}
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *args): return False
        def fake_urlopen(request, timeout=0):
            captured["body"] = json.loads(request.data.decode())
            return Response(json.dumps({"choices":[{"message":{"content":json.dumps(assessment)}}]}).encode())
        provider = {"name":"NaraRouter (bynara)","url":"https://example.invalid/v1/chat/completions",
                    "model":"test-model","key":"test"}
        job = {"title":"Project Engineer","company":"Example","description":"Project engineering"}
        with patch("radar.urllib.request.urlopen",side_effect=fake_urlopen):
            result=ai_assess(job,"anonymized CV",{},"test",provider)
        self.assertNotIn("response_format",captured["body"])
        self.assertEqual(result["score"],72)

    def test_settings_select_free_gemma_26b_a4b_for_openrouter(self):
        with open("settings.json", encoding="utf8") as handle:
            settings = json.load(handle)
        self.assertEqual(settings["ai_model"], "google/gemma-4-26b-a4b-it:free")

    def test_openrouter_gemma_uses_json_mode_and_model_id(self):
        assessment = {
            "fit_score": 80, "recommendation": "Apply", "summary": "Relevant.",
            "strengths": ["CAD"], "gaps": [], "work_authorization_note": "Not stated.",
            "degree_requirement": "bachelor accepted", "requirement_evidence": [],
            "confidence": "high"
        }
        captured = {}
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *args): return False
        def fake_urlopen(request, timeout=0):
            captured["body"] = json.loads(request.data.decode())
            return Response(json.dumps({"choices":[{"message":{"content":json.dumps(assessment)}}]}).encode())
        provider = {"name":"OpenRouter","url":"https://example.invalid/v1/chat/completions",
                    "model":"google/gemma-4-26b-a4b-it:free","key":"test"}
        job = {"title":"Manufacturing Engineer","company":"Example","description":"Manufacturing engineering"}
        with patch("radar.urllib.request.urlopen",side_effect=fake_urlopen):
            result=ai_assess(job,"anonymized CV",{},"test",provider)
        self.assertEqual(captured["body"]["model"],"google/gemma-4-26b-a4b-it:free")
        self.assertEqual(captured["body"]["response_format"],{"type":"json_object"})
        self.assertEqual(result["model"],"google/gemma-4-26b-a4b-it:free")

if __name__ == "__main__":
    unittest.main()
