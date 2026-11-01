import json
import tempfile
import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from file_integrity_checker import create_baseline, verify_files, load_baseline


class FileIntegrityCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "data"
        self.root.mkdir()
        self.baseline = self.root / ".file_integrity_baseline.json"
        (self.root / "one.txt").write_text("hello", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_clean_verification(self):
        create_baseline(self.root, self.baseline)
        result = verify_files(self.root, self.baseline)
        self.assertTrue(result["is_clean"])
        self.assertEqual(result["unchanged"], ["one.txt"])

    def test_detect_modified_file(self):
        create_baseline(self.root, self.baseline)
        (self.root / "one.txt").write_text("changed", encoding="utf-8")
        result = verify_files(self.root, self.baseline)
        self.assertEqual(result["modified"], ["one.txt"])
        self.assertFalse(result["is_clean"])

    def test_detect_added_file(self):
        create_baseline(self.root, self.baseline)
        (self.root / "two.txt").write_text("new", encoding="utf-8")
        result = verify_files(self.root, self.baseline)
        self.assertEqual(result["added"], ["two.txt"])

    def test_detect_missing_file(self):
        create_baseline(self.root, self.baseline)
        (self.root / "one.txt").unlink()
        result = verify_files(self.root, self.baseline)
        self.assertEqual(result["missing"], ["one.txt"])

    def test_reject_invalid_baseline(self):
        self.baseline.write_text(json.dumps({"algorithm": "MD5", "version": 1, "files": {}}))
        with self.assertRaises(ValueError):
            load_baseline(self.baseline)


if __name__ == "__main__":
    unittest.main()
