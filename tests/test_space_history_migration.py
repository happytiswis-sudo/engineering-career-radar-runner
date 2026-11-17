import json
import unittest
from scripts.migrate_space_history_to_r2 import validate_index, validate_snapshot_json, build_manifest, sha256

class MigrationValidationTests(unittest.TestCase):
    def test_accepts_matching_run_archive(self):
        rows = validate_index({"runs":[{"run_id":"12345678","published":True,"archive_file":"history/run-12345678.json"}]},
                              {"history/run-12345678.json":12})
        self.assertEqual(rows[0]["run_id"], "12345678")

    def test_rejects_run_id_filename_mismatch(self):
        with self.assertRaisesRegex(ValueError, "run ID"):
            validate_index({"runs":[{"run_id":"87654321","published":True,"archive_file":"history/run-12345678.json"}]},
                           {"history/run-12345678.json":12})

    def test_rejects_missing_archive(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            validate_index({"runs":[{"run_id":"12345678","published":True,"archive_file":"history/run-12345678.json"}]}, {})

    def test_rejects_unindexed_history_archive(self):
        with self.assertRaisesRegex(ValueError, "Unindexed"):
            validate_index({"runs":[{"run_id":"12345678","published":True,"archive_file":"history/run-12345678.json"}]},
                           {"history/run-12345678.json":12,"history/run-87654321.json":15})

    def test_manifest_records_preserved_files_and_no_deletion(self):
        raw=b'{}'
        manifest=build_manifest("Sidmed/engineering-career-radar",raw,
            [{"run_id":"12345678","path":"history/run-12345678.json","bytes":2,"sha256":sha256(b"{}")}],
            [{"path":"seen-jobs.json","bytes":2,"sha256":sha256(b"{}"),"preserved_in_space":True}],
            "2026-11-17T00:00:00+00:00")
        self.assertFalse(manifest["deletion_performed"])
        self.assertTrue(manifest["preserved_space_files"][0]["preserved_in_space"])
        self.assertEqual(manifest["history_index"]["sha256"],sha256(raw))
        self.assertEqual(manifest["r2_snapshot_files"],[])

    def test_validates_actual_dashboard_snapshot_not_a_jobs_array(self):
        snapshot={"run_id":"42421164429","generated_at":"2026-11-07T22:37:12+00:00","total_shortlisted":11}
        parsed=validate_snapshot_json("jobs.json",json.dumps(snapshot).encode())
        self.assertEqual(parsed["run_id"],"42421164429")
        with self.assertRaisesRegex(ValueError,"run_id"):
            validate_snapshot_json("jobs.json",b'{"total_shortlisted":11}')

    def test_validates_history_index_and_preserves_seen_registry_root(self):
        self.assertEqual(validate_snapshot_json("search-history.json",b'{"runs":[]}'),{"runs":[]})
        self.assertEqual(validate_snapshot_json("seen-jobs.json",b'{"url-a":true}'),{"url-a":True})
        with self.assertRaisesRegex(ValueError,"runs array"):
            validate_snapshot_json("search-history.json",b'{}')

    def test_manifest_records_latest_dashboard_snapshot_and_seen_registry_for_r2(self):
        raw=b'{}'
        snapshots=[
            {"path":"search-history.json","bytes":2,"sha256":sha256(raw),"preserved_in_space":True,"stored_in_r2":True},
            {"path":"jobs.json","bytes":2,"sha256":sha256(raw),"preserved_in_space":True,"stored_in_r2":True},
            {"path":"seen-jobs.json","bytes":2,"sha256":sha256(raw),"preserved_in_space":True,"stored_in_r2":True},
        ]
        manifest=build_manifest("Sidmed/engineering-career-radar",raw,[],[], "2026-11-17T00:00:00+00:00", snapshots)
        self.assertEqual({x["path"] for x in manifest["r2_snapshot_files"]},
                         {"search-history.json","jobs.json","seen-jobs.json"})
        self.assertFalse(manifest["deletion_performed"])


if __name__ == "__main__": unittest.main()
