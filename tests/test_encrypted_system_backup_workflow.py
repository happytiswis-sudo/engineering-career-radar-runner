from pathlib import Path
import unittest


class EncryptedSystemBackupWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = Path(
            ".github/workflows/backup-system-before-opportunity-expansion.yml"
        ).read_text(encoding="utf-8")

    def test_manual_only_and_serialized_backup(self):
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertNotIn("\n  schedule:", self.workflow)
        self.assertIn("cancel-in-progress: false", self.workflow)
        self.assertIn("timeout-minutes: 30", self.workflow)

    def test_requires_database_url_and_encryption_secret(self):
        self.assertIn("secrets.SUPABASE_DB_URL", self.workflow)
        self.assertIn("secrets.BACKUP_ENCRYPTION_PASSPHRASE", self.workflow)
        self.assertIn("sslmode", self.workflow)
        self.assertIn("postgres:17-alpine", self.workflow)

    def test_gpg_encryption_and_restore_catalog_check(self):
        self.assertIn("--symmetric --cipher-algo AES256", self.workflow)
        self.assertIn("--s2k-digest-algo SHA512", self.workflow)
        self.assertIn("pg_restore --list", self.workflow)
        self.assertIn("gpg --batch --list-packets", self.workflow)

    def test_private_r2_requires_guardian_and_readback(self):
        self.assertIn("python scripts/r2_free_tier_guard.py", self.workflow)
        self.assertIn("r2-guardian.outputs.r2_write_admitted", self.workflow)
        self.assertIn("X-Archive-CI-Token", self.workflow)
        self.assertIn("X-Dashboard-Key", self.workflow)
        self.assertIn("SHA-256 mismatch", self.workflow)
        self.assertIn("backups/pre-opportunity-expansion-20261120", self.workflow)

    def test_no_publication_or_hugging_face_write(self):
        self.assertNotIn("enable_production_publish", self.workflow)
        self.assertNotIn("HF_TOKEN: ${{", self.workflow)
        self.assertNotIn("HF_SPACE_ID: ${{", self.workflow)
        self.assertNotIn("HF_TOKEN", "\n".join(
            line for line in self.workflow.splitlines() if line.strip().startswith("env:")
        ))

    def test_plaintext_is_removed(self):
        self.assertIn("Remove private source checkout and plaintext backup", self.workflow)
        self.assertIn('rm -rf private-source-snapshot "$RUNNER_TEMP/career-radar-backup"', self.workflow)


if __name__ == "__main__":
    unittest.main()
