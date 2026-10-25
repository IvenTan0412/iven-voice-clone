"""Verify safety/portability contracts without loading the speech models."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run(root, *args):
    return subprocess.run([sys.executable, str(root / "scripts/voice.py"), *args], capture_output=True, text=True)


class Contracts(unittest.TestCase):
    def test_no_implicit_voice_selection(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "voice.wav"
            result = run(ROOT, "测试文字", "-o", str(out))
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(out.exists())

    def test_existing_sidecar_cannot_be_overwritten(self):
        for suffix in (".wav", ".raw.wav", ".json"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as d:
                out = Path(d) / "voice.wav"
                protected = out.with_suffix(suffix)
                protected.write_bytes(b"user existing work")
                before = hashlib.sha256(protected.read_bytes()).digest()
                result = run(ROOT, "--voice", "female", "测试文字", "-o", str(out))
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(hashlib.sha256(protected.read_bytes()).digest(), before)
                self.assertEqual(len(list(Path(d).iterdir())), 1)

    def test_relocated_profiles_and_corrupt_reference_detection(self):
        with tempfile.TemporaryDirectory(prefix="voice kit with spaces ") as d:
            dest = Path(d)
            for directory in ("scripts", "voices"):
                shutil.copytree(ROOT / directory, dest / directory)
            result = run(dest, "--list-voices")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("male:", result.stdout)
            self.assertIn("female:", result.stdout)
            (dest / "voices/female/reference.wav").write_bytes(b"wrong reference")
            self.assertNotEqual(run(dest, "--list-voices").returncode, 0)


if __name__ == "__main__":
    unittest.main()
