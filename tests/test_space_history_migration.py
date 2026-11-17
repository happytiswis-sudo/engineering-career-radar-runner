import unittest
from scripts.migrate_space_history_to_r2 import validate_index, build_manifest, sha256

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

if __name__ == "__main__": unittest.main()
