import importlib.util
import unittest
from pathlib import Path

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
        rows = [
            {"dimensions": {"bucketName": "a", "datetime": "2026-11-16T00:00:00Z"},
             "max": {"payloadSize": 100, "metadataSize": 10}},
            {"dimensions": {"bucketName": "a", "datetime": "2026-11-17T00:00:00Z"},
             "max": {"payloadSize": 120, "metadataSize": 10}},
            {"dimensions": {"bucketName": "b", "datetime": "2026-11-17T00:00:00Z"},
             "max": {"payloadSize": 50, "metadataSize": 5}},
        ]
        peak, latest, buckets = GUARD.storage_peak_bytes(rows)
        self.assertEqual(peak, 185)
        self.assertEqual(buckets, 2)
        self.assertEqual(latest, "2026-11-17T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
