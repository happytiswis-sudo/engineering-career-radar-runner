"""Live HTTP regression for the deployed dashboard's exact Hugging Face origin CORS policy."""

import urllib.error
import urllib.request
import unittest


ENDPOINT = "https://career-radar-dashboard.happytiswis.workers.dev/api/bridge/health"
APPROVED_ORIGIN = "https://sidmed-engineering-career-radar.static.hf.space"


def http_request(method, headers):
    request = urllib.request.Request(ENDPOINT, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, {key.lower(): value for key, value in response.headers.items()}, response.read()
    except urllib.error.HTTPError as error:
        return error.code, {key.lower(): value for key, value in error.headers.items()}, error.read()


class LiveDashboardCorsTests(unittest.TestCase):
    def test_huggingface_origin_preflight_and_health(self):
        status, headers, body = http_request("OPTIONS", {
            "Origin": APPROVED_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        })
        self.assertEqual(status, 204, body[:500])
        self.assertEqual(headers.get("access-control-allow-origin"), APPROVED_ORIGIN)
        self.assertIn("GET", headers.get("access-control-allow-methods", ""))

        status, headers, body = http_request("GET", {
            "Origin": APPROVED_ORIGIN,
            "Accept": "application/json",
        })
        self.assertEqual(status, 200, body[:500])
        self.assertEqual(headers.get("access-control-allow-origin"), APPROVED_ORIGIN)

    def test_unapproved_origin_remains_rejected(self):
        status, headers, body = http_request("OPTIONS", {
            "Origin": "https://unapproved.example",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        })
        self.assertEqual(status, 403, body[:500])
        self.assertNotIn("access-control-allow-origin", headers)


if __name__ == "__main__":
    unittest.main()
