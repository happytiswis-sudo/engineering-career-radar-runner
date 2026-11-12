import unittest
from unittest.mock import patch
import io
from vacancy_verification import verify_public_job_page


class VacancyVerificationTests(unittest.TestCase):
    def response(self, body, url="https://jobs.example.de/posting/1", status=200):
        class Response:
            def __init__(self):
                self.status = status
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def geturl(self): return url
            def read(self, size=-1): return body.encode("utf-8")[:size]
        return Response()

    def test_active_public_page(self):
        with patch("vacancy_verification.urlopen", return_value=self.response("<html><h1>Engineer</h1></html>")):
            self.assertEqual(verify_public_job_page("https://jobs.example.de/posting/1")["status"], "active")

    def test_closed_phrase_detected(self):
        with patch("vacancy_verification.urlopen", return_value=self.response("<p>This job is no longer available</p>")):
            result = verify_public_job_page("https://jobs.example.de/posting/1")
        self.assertEqual(result["status"], "inactive")
        self.assertEqual(result["reason"], "closed_phrase_on_source_page")

    def test_cross_host_redirect_not_trusted(self):
        with patch("vacancy_verification.urlopen", return_value=self.response("<p>Job</p>", url="https://other.example.net/job")):
            self.assertEqual(verify_public_job_page("https://jobs.example.de/posting/1")["status"], "unknown")

    def test_non_https_url_rejected(self):
        self.assertEqual(verify_public_job_page("http://jobs.example.de/posting/1")["status"], "unknown")

    def test_timeout_or_transport_error_is_unknown_not_closed(self):
        with patch("vacancy_verification.urlopen", side_effect=TimeoutError()):
            self.assertEqual(verify_public_job_page("https://jobs.example.de/posting/1")["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
