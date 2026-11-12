import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import radar


class ArbeitnowRecoveryTests(unittest.TestCase):
    def test_429_after_successful_page_preserves_partial_results(self):
        board = {"type": "arbeitnow", "slug": "main", "company": "Arbeitnow"}
        page = {"data": [{
            "company_name": "Example GmbH", "title": "Quality Engineer",
            "location": "Germany", "url": "https://example.de/jobs/1",
            "description": "Quality engineering role"
        }]}
        blocked = urllib.error.HTTPError(
            "https://www.arbeitnow.com/api/job-board-api?page=2",
            429, "rate limited", {"Retry-After": "3600"}, None
        )
        with patch.object(radar, "read_json_url", side_effect=[page, blocked]):
            rows = radar.fetch_board(board)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company"], "Example GmbH")
        self.assertEqual(board["rate_limit_error"]["status"], 429)
        self.assertEqual(board["rate_limit_error"]["retry_after"], "3600")

    def test_cooldown_is_per_feed_and_respects_longer_retry_after(self):
        now = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
        state = {}
        radar.record_arbeitnow_cooldown(
            state, {"type": "arbeitnow", "slug": "main"}, "172800", now
        )
        self.assertEqual(len(state), 1)
        value = state["arbeitnow|main"]
        self.assertEqual(value["reason"], "http_429")
        self.assertEqual(datetime.fromisoformat(value["retry_after"]), now + timedelta(hours=48))
        radar.record_arbeitnow_cooldown(
            state, {"type": "arbeitnow_visa", "slug": "visa"}, "", now
        )
        self.assertIn("arbeitnow_visa|visa", state)

    def test_invalid_retry_after_uses_six_hour_fallback_and_escalates(self):
        now = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
        state = {}
        board = {"type": "arbeitnow", "slug": "main"}
        radar.record_arbeitnow_cooldown(state, board, "not-a-date", now)
        first = datetime.fromisoformat(state["arbeitnow|main"]["retry_after"])
        self.assertEqual(first, now + timedelta(hours=6))

        # Once the previous cooldown has expired, another 429 escalates.
        radar.record_arbeitnow_cooldown(
            state, board, "", first + timedelta(seconds=1)
        )
        second = datetime.fromisoformat(state["arbeitnow|main"]["retry_after"])
        self.assertEqual(second, first + timedelta(seconds=1, hours=6))

    def test_http_date_retry_after_is_honoured_and_capped(self):
        from email.utils import format_datetime
        now = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
        state = {}
        target = now + timedelta(hours=30)
        radar.record_arbeitnow_cooldown(
            state, {"type": "arbeitnow_uk", "slug": "main"},
            format_datetime(target), now
        )
        self.assertEqual(
            datetime.fromisoformat(state["arbeitnow_uk|main"]["retry_after"]),
            target
        )

    def test_non_arbeitnow_sources_do_not_receive_feed_cooldown(self):
        state = {}
        radar.record_arbeitnow_cooldown(
            state, {"type": "greenhouse", "slug": "example"}, "86400"
        )
        self.assertEqual(state, {})


if __name__ == "__main__":
    unittest.main()
