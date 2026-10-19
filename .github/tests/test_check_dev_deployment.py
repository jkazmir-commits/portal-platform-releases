"""Offline acceptance checks; no external HTTP access."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "scripts" / "check_dev_deployment.py"
spec = importlib.util.spec_from_file_location("dev_checker", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ReleaseAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.good = {
            "version": "0.8.0-dev108",
            "package": mod.RELEASE_ROOT + "0.8.0-dev108/portal-platform-0.8.0-dev108.zip",
            "sha256": "f" * 64,
        }

    def test_manifest(self):
        self.assertEqual(mod.manifest(self.good), self.good)

    def test_package_rejected(self):
        with self.assertRaises(ValueError):
            mod.manifest(dict(self.good, package="https://evil.example/1.zip"))

    def test_hash_rejected(self):
        with self.assertRaises(ValueError):
            mod.manifest(dict(self.good, sha256="bad"))

    def test_wrong_version_rejected(self):
        with self.assertRaises(ValueError):
            mod.manifest(dict(self.good, version="1.2.3"))

    def test_minimal_live_response(self):
        self.assertEqual(mod.installed({"version": "0.8.0-dev108", "environment": "dev"}), "0.8.0-dev108")

    def test_wrong_environment(self):
        with self.assertRaises(ValueError):
            mod.installed({"version": "0.8.0-dev108", "environment": "prod"})

    def test_extra_fields(self):
        with self.assertRaises(ValueError):
            mod.installed({"version": "0.8.0-dev108", "environment": "dev", "secret": "x"})

    def test_current(self):
        self.assertEqual(mod.verdict("0.8.0-dev108", "0.8.0-dev108", 123), ("current", 0))

    def test_cron_delay(self):
        self.assertEqual(mod.verdict("0.8.0-dev109", "0.8.0-dev108", 7200), ("pending_wordpress_auto_update", 0))

    def test_stale_wp(self):
        self.assertEqual(mod.verdict("0.8.0-dev109", "0.8.0-dev108", mod.GRACE_SECONDS + 1), ("overdue_wordpress_auto_update", 1))

    def test_wp_ahead(self):
        self.assertEqual(mod.verdict("0.8.0-dev108", "0.8.0-dev109", 5), ("ahead_of_release", 1))


if __name__ == "__main__":
    unittest.main()
