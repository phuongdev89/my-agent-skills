"""Offline regression checks for the image skill split; no provider calls."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/openai-image/scripts/generate_image.py"
spec = importlib.util.spec_from_file_location("openai_image", SCRIPT)
image = importlib.util.module_from_spec(spec)
spec.loader.exec_module(image)


class ImageSkillSplitTests(unittest.TestCase):
    def test_gateway_payloads_preserve_reference(self):
        reference = "data:image/png;base64,aGVsbG8="
        for mode, suffix in (("edit", "images/edits"), ("9router", "images/generations"), ("response", "responses")):
            with self.subTest(mode=mode):
                url, payload, _ = image.build_project_payload(
                    mode, "https://gateway.example/v1", "image-model",
                    "Keep [ATTACHED_PHOTO]", ref_data_uri=reference,
                )
                self.assertEqual(url, "https://gateway.example/v1/" + suffix)
                self.assertIn(reference, json.dumps(payload))
                self.assertNotIn("[ATTACHED_PHOTO]", json.dumps(payload))

    def test_cli_dry_run_modes(self):
        for mode in ("edit", "9router", "response"):
            with self.subTest(mode=mode):
                result = subprocess.run([
                    sys.executable, str(SCRIPT), "--dry-run", "--image-type", mode,
                    "--url", "https://gateway.example/v1", "--model", "image-model",
                ], capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(result.returncode, 0, result.stderr)
                data = json.loads(result.stdout)
                self.assertEqual(data["provider"], "project-" + mode)
                self.assertEqual(data["base_url"], "https://gateway.example/v1")

    def test_removed_cli_flag_rejected(self):
        result = subprocess.run([
            sys.executable, str(SCRIPT), "--use-gemini", "--dry-run",
        ], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_aidancing_scripts_preserved(self):
        for name in ("edit", "delete_object", "bg_swap", "outfit_swap", "add_accessory"):
            relative = f"scripts/aidancing/aidancing_{name}.py"
            previous = subprocess.run([
                "git", "show", "HEAD:skills/image-generate/" + relative,
            ], cwd=ROOT, capture_output=True, check=True).stdout
            current = (ROOT / "skills/aidancing-image/scripts" / f"aidancing_{name}.py").read_bytes()
            self.assertEqual(current.replace(b"\r\n", b"\n"), previous.replace(b"\r\n", b"\n"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
