import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "r2_free_tier_guard.py"
SPEC = importlib.util.spec_from_file_location("r2_free_tier_guard", SCRIPT)
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


class R2FreeTierGuardianTests(unittest.TestCase):
    def report(self, **updates):
        value = {
            "metrics_complete": True,
            "admitted": True,
            "storage_class": "standard_only",
            "storage_peak_bytes": 1_000_000,
            "class_a_operations_30d": 100,
            "class_b_operations_30d": 100,
            "unknown_operations": [],
        }
        value.update(updates)
        return value

    def test_admits_complete_low_usage(self):
        self.assertTrue(GUARD.evaluate(self.report()))

    def test_fails_closed_on_missing_metrics(self):
        self.assertFalse(GUARD.evaluate(self.report(metrics_complete=False)))
        self.assertFalse(GUARD.evaluate(self.report(storage_peak_bytes=None)))

    def test_fails_closed_on_unknown_operation(self):
        self.assertFalse(GUARD.evaluate(self.report(unknown_operations=["NewOperation"])))

    def test_fails_closed_on_infrequent_access(self):
        self.assertFalse(GUARD.evaluate(self.report(storage_class="mixed")))

    def test_storage_limit_has_safety_margin(self):
        self.assertTrue(GUARD.evaluate(self.report(storage_peak_bytes=6_999_999_999)))
        self.assertFalse(GUARD.evaluate(self.report(storage_peak_bytes=7_000_000_000)))

    def test_operation_limits_have_safety_margin(self):
        self.assertFalse(GUARD.evaluate(self.report(class_a_operations_30d=700_000)))
        self.assertFalse(GUARD.evaluate(self.report(class_b_operations_30d=7_000_000)))

    def test_operation_classification_rejects_unknown_types(self):
        rows = [
            {"dimensions": {"actionType": "PutObject"}, "sum": {"requests": 3}},
            {"dimensions": {"actionType": "GetObject"}, "sum": {"requests": 9}},
            {"dimensions": {"actionType": "DeleteObject"}, "sum": {"requests": 4}},
            {"dimensions": {"actionType": "UncataloguedNewOperation"}, "sum": {"requests": 1}},
        ]
        a, b, unknown = GUARD.classify_operations(rows)
        self.assertEqual((a, b, unknown), (3, 9, ["UncataloguedNewOperation"]))

    def test_storage_upper_bound_sums_each_bucket_peak(self):
        now = GUARD.utc_now()
        timestamp = GUARD.iso(now)
        rows = [
            {"dimensions": {"bucketName": "a", "datetime": timestamp},
             "max": {"payloadSize": 100, "metadataSize": 10}},
            {"dimensions": {"bucketName": "a", "datetime": timestamp},
             "max": {"payloadSize": 120, "metadataSize": 10}},
            {"dimensions": {"bucketName": "b", "datetime": timestamp},
             "max": {"payloadSize": 50, "metadataSize": 5}},
        ]
        peak, latest, buckets = GUARD.storage_peak_bytes(rows)
        self.assertEqual(peak, 185)
        self.assertEqual(buckets, 2)
        self.assertEqual(latest, timestamp)

    def test_account_metrics_requires_all_class_state_fields(self):
        valid = {"success": True, "result": {
            "standard": {
                "published": {"payloadSize": 10, "metadataSize": 1, "objects": 1},
                "uploaded": {"payloadSize": 0, "metadataSize": 0, "objects": 0},
            },
            "infrequentAccess": {
                "published": {"payloadSize": 0, "metadataSize": 0, "objects": 0},
                "uploaded": {"payloadSize": 0, "metadataSize": 0, "objects": 0},
            },
        }}
        with patch.object(GUARD, "cloudflare_request", return_value=valid):
            self.assertEqual(GUARD.current_account_storage("account", "token"), (11, 0))
        incomplete = {"success": True, "result": {
            "standard": {"published": {"payloadSize": 10}, "uploaded": {}},
            "infrequentAccess": {
                "published": {"payloadSize": 0, "metadataSize": 0, "objects": 0},
                "uploaded": {"payloadSize": 0, "metadataSize": 0, "objects": 0},
            },
        }}
        with patch.object(GUARD, "cloudflare_request", return_value=incomplete):
            with self.assertRaisesRegex(RuntimeError, "omitted"):
                GUARD.current_account_storage("account", "token")

    def test_graphql_uses_separate_30_day_operation_and_31_day_storage_windows(self):
        operations_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        storage_start = datetime(2025, 12, 31, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)
        response = {"data": {"viewer": {"accounts": [{
            "r2OperationsAdaptiveGroups": [{"sum": {"requests": 1}, "dimensions": {"actionType": "GetObject"}}],
            "r2StorageAdaptiveGroups": [{"max": {"payloadSize": 1, "metadataSize": 0},
                                         "dimensions": {"bucketName": "bucket", "datetime": "2026-01-31T00:00:00Z"}}],
        }]}}}
        with patch.object(GUARD, "cloudflare_request", return_value=response) as request:
            GUARD.graphql_query("account", "token", operations_start, storage_start, end)
        query = request.call_args.args[3]["query"]
        self.assertIn('datetime_geq: "2026-01-01T00:00:00Z"', query)
        self.assertIn('datetime_geq: "2025-12-31T00:00:00Z"', query)


if __name__ == "__main__":
    unittest.main()
