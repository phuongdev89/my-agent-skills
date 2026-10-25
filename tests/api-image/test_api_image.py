"""Real routing/serialization/parsing logic with mocked HTTP transport; no paid calls."""
import base64
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/api-image/scripts/generate_image.py"
spec = importlib.util.spec_from_file_location("api_image", SCRIPT)
image = importlib.util.module_from_spec(spec)
spec.loader.exec_module(image)
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j7ioAAAAASUVORK5CYII=")
REFERENCE = "data:image/png;base64," + base64.b64encode(PNG).decode()
ENV = {
    "API_IMAGE_PROVIDER": "9router|sub2api", "API_IMAGE_TIMEOUT": "37",
    "API_IMAGE_NINEROUTER_URL": "https://nine.example/v1",
    "API_IMAGE_NINEROUTER_KEY": "nine-secret", "API_IMAGE_NINEROUTER_MODEL": "gpt-image-2.5",
    "API_IMAGE_SUB2API_URL": "https://sub.example/v1",
    "API_IMAGE_SUB2API_KEY": "sub-secret", "API_IMAGE_SUB2API_MODEL": "gpt-image-2",
}
INPUTS = dict(prompt="Giữ khuôn mặt và áo", ref_data_uri=REFERENCE,
              size="1024x1536", quality="hd", image_detail="high")


def reply(value=None, raw=None):
    return io.BytesIO(raw if raw is not None else json.dumps(value or {
        "model": "actual-image-model", "data": [{"b64_json": base64.b64encode(PNG).decode()}]
    }).encode())


def http_error(status, error):
    return HTTPError("https://secret.example/?key=nine-secret", status,
                     "secret reason", {"Authorization": "Bearer nine-secret"},
                     io.BytesIO(json.dumps({"error": error}).encode()))


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.object(image, "load_candidate_env", return_value=ENV.copy())
        self.env.start()
        self.addCleanup(self.env.stop)

    def run_chain(self, effects, inputs=None, configs=None):
        with patch.object(image.urllib.request, "urlopen", side_effect=effects) as network:
            result = image.run_providers(configs or image.resolve_providers(), **(inputs or INPUTS))
        return result, network

    def test_default_order_and_first_success(self):
        (result, cfg, attempts), network = self.run_chain([reply()])
        self.assertEqual(cfg["provider"], "9router")
        self.assertEqual(result[0], PNG)
        self.assertEqual(result[3], "actual-image-model")
        self.assertEqual(len(attempts), 1)
        self.assertEqual(network.call_count, 1)
        self.assertEqual(image.resolve_providers()[0]["timeout"], 37)

    def test_fallback_isolates_credentials_models_and_preserves_inputs(self):
        (result, cfg, attempts), network = self.run_chain([
            http_error(429, {"message": "quota nine-secret"}), reply()
        ])
        self.assertEqual(result[0], PNG)
        self.assertEqual(cfg["provider"], "sub2api")
        self.assertEqual([a["status"] for a in attempts], ["failed", "success"])
        first, second = [call.args[0] for call in network.call_args_list]
        self.assertEqual(first.full_url, ENV["API_IMAGE_NINEROUTER_URL"] + "/images/generations")
        self.assertEqual(second.full_url, ENV["API_IMAGE_SUB2API_URL"] + "/images/edits")
        self.assertEqual(first.get_header("Authorization"), "Bearer nine-secret")
        self.assertEqual(second.get_header("Authorization"), "Bearer sub-secret")
        first_payload = json.loads(first.data)
        self.assertEqual(first_payload["model"], "gpt-image-2.5")
        for key in ("prompt", "size", "quality"):
            self.assertEqual(first_payload[key], INPUTS[key])
            self.assertIn(str(INPUTS[key]).encode(), second.data)
        self.assertEqual(first_payload["image"], REFERENCE)
        self.assertIn(PNG, second.data)
        self.assertIn(b'name="model"\r\n\r\ngpt-image-2\r\n', second.data)
        self.assertNotIn(b"gpt-image-2.5", second.data)
        self.assertIn("multipart/form-data", second.get_header("Content-type"))

    def test_sub2api_detects_reference_even_with_protocol_override(self):
        env = dict(ENV, API_IMAGE_PROVIDER="sub2api")
        with patch.object(image, "load_candidate_env", return_value=env):
            configs = image.resolve_providers(cli_type="9router")
        self.assertEqual(configs[0]["image_type"], "sub2api")
        for reference, endpoint in ((REFERENCE, "edits"), (None, "generations")):
            with self.subTest(reference=bool(reference)):
                (_, cfg, _), network = self.run_chain([reply()], dict(INPUTS, ref_data_uri=reference), configs)
                request = network.call_args.args[0]
                self.assertTrue(request.full_url.endswith("/images/" + endpoint))
                if reference is None:
                    payload = json.loads(request.data)
                    self.assertNotIn("image", payload)
                    self.assertEqual(payload["quality"], "hd")

    def test_selector_order_single_and_defaults(self):
        for selector, expected in (("sub2api|9router", ["sub2api", "9router"]), ("sub2api", ["sub2api"])):
            with patch.object(image, "load_candidate_env", return_value=dict(ENV, API_IMAGE_PROVIDER=selector)):
                self.assertEqual([c["provider"] for c in image.resolve_providers()], expected)
        env = ENV.copy()
        del env["API_IMAGE_PROVIDER"]
        with patch.object(image, "load_candidate_env", return_value=env):
            self.assertEqual([c["provider"] for c in image.resolve_providers()], ["9router", "sub2api"])

    def test_missing_config_skips_without_borrowing_legacy(self):
        env = dict(ENV, API_IMAGE_NINEROUTER_KEY="", AI_IMAGE_KEY="wrong-secret")
        with patch.object(image, "load_candidate_env", return_value=env):
            configs = image.resolve_providers()
        (_, cfg, attempts), network = self.run_chain([reply()], configs=configs)
        self.assertEqual(cfg["provider"], "sub2api")
        self.assertIn("missing_api_key", attempts[0]["reason"])
        self.assertEqual(network.call_count, 1)

    def test_cli_override_only_first_tier(self):
        configs = image.resolve_providers("override-secret", "https://override.example/v1", "override-model", "response")
        self.assertEqual(configs[0]["image_type"], "response")
        self.assertEqual(configs[1]["api_key"], "sub-secret")
        self.assertEqual(configs[1]["model"], "gpt-image-2")
        self.assertEqual(configs[1]["base_url"], ENV["API_IMAGE_SUB2API_URL"])

    def test_failure_classification_stops_or_falls_back(self):
        for status, error, fallback in (
            (503, "service unavailable", True), (401, "no access", True),
            (402, "no credit", True), (403, "permission denied", True),
            (400, "reference image not supported", True),
            (400, "invalid size", False), (422, "invalid image", False),
            (400, "unsupported image format", False), (400, "unsupported size", False),
            (429, "content_policy_violation", False), (503, "safety refusal", False),
            (408, "unknown", False), (504, "unknown", False), (500, "job timed out", False),
        ):
            with self.subTest(status=status, error=error):
                (result, _, attempts), network = self.run_chain([http_error(status, error), reply()])
                self.assertEqual(network.call_count, 2 if fallback else 1)
                self.assertEqual(result is not None, fallback)

    def test_network_timeout_disconnect_and_download_do_not_resubmit(self):
        for error in (TimeoutError("nine-secret"), URLError("sub-secret")):
            (result, _, attempts), network = self.run_chain([error])
            self.assertIsNone(result)
            self.assertEqual(network.call_count, 1)
            self.assertIn("submission_unknown", attempts[0]["reason"])
        with patch.object(image, "fetch_image_data", side_effect=RuntimeError("nine-secret")):
            (result, _, attempts), network = self.run_chain([reply()])
        self.assertIsNone(result)
        self.assertEqual(network.call_count, 1)
        self.assertIn("download_failed", attempts[0]["reason"])

    def test_exhaustion_bounded(self):
        (result, cfg, attempts), network = self.run_chain([http_error(503, "offline"), http_error(429, "quota")])
        self.assertIsNone(result)
        self.assertIsNone(cfg)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(network.call_count, 2)

    def test_json_sse_nested_response_and_refusal(self):
        encoded = base64.b64encode(PNG).decode()
        body = b'data: {"type":"response.completed","response":' + json.dumps({
            "model": "reported", "output": [{"type": "image_generation_call", "result": encoded}]
        }).encode() + b'}\n\ndata: [DONE]\n'
        (result, _, _), _ = self.run_chain([reply(raw=body)])
        self.assertEqual(result[0], PNG)
        self.assertEqual(result[3], "reported")
        refusal = {"output": [{"type": "message", "content": [{"type": "refusal", "refusal": "blocked"}]}]}
        (result, _, attempts), network = self.run_chain([reply(refusal)])
        self.assertIsNone(result)
        self.assertEqual(network.call_count, 1)
        self.assertIn("safety_refusal", attempts[0]["reason"])

    def test_errors_and_metadata_redact_credentials(self):
        (result, _, attempts), _ = self.run_chain([http_error(400, "Authorization: Bearer nine-secret prompt/private")])
        public = image.public_json({"attempts": attempts, "model": "sub-secret", "prompt": "nine-secret"})
        for sensitive in ("nine-secret", "sub-secret", "Authorization", "prompt/private"):
            self.assertNotIn(sensitive, public)

    def test_model_not_reported_is_not_invented(self):
        (result, _, _), _ = self.run_chain([reply({"data": [{"b64_json": base64.b64encode(PNG).decode()}]})])
        self.assertIsNone(result[3])

    def test_missing_reference_stops_before_network(self):
        with tempfile.TemporaryDirectory() as temp:
            args = [str(SCRIPT), "--prompt", "edit", "--ref-image", str(Path(temp) / "missing.png")]
            stream = io.StringIO()
            with patch.object(sys, "argv", args), patch.object(image.urllib.request, "urlopen") as network:
                with contextlib.redirect_stdout(stream), self.assertRaises(SystemExit) as stopped:
                    image.main()
            self.assertEqual(stopped.exception.code, 1)
            network.assert_not_called()
            self.assertEqual(json.loads(stream.getvalue())["status"], "error")

    def test_legacy_aliases_and_protocols(self):
        env = {"AI_IMAGE_API_KEY": "legacy", "AI_IMAGE_ENDPOINT_URL": "https://legacy.example/v1",
               "AI_IMAGE_MODEL": "legacy-model,ignored", "AI_IMAGE_TYPE": "response", "AI_TIMEOUT": "123"}
        with patch.object(image, "load_candidate_env", return_value=env):
            cfg = image.resolve_providers()[0]
        self.assertEqual((cfg["api_key"], cfg["model"], cfg["image_type"], cfg["timeout"]),
                         ("legacy", "legacy-model", "response", 123))
        for protocol, suffix in (("edit", "images/edits"), ("response", "responses"), ("9router", "images/generations")):
            endpoint, payload, _ = image.build_project_payload(protocol, cfg["base_url"], cfg["model"],
                                                              "Keep [ATTACHED_PHOTO]", REFERENCE)
            self.assertTrue(endpoint.endswith(suffix))
            self.assertIn(REFERENCE, json.dumps(payload))

    def test_dry_run_never_calls_network_and_cli_success_writes_image(self):
        with tempfile.TemporaryDirectory() as temp:
            ref = Path(temp) / "reference.png"
            ref.write_bytes(PNG)
            output = Path(temp) / "output.png"
            for dry in (True, False):
                args = [str(SCRIPT), "--prompt", INPUTS["prompt"], "--ref-image", str(ref), "--output", str(output)]
                if dry:
                    args.append("--dry-run")
                stream = io.StringIO()
                with patch.object(sys, "argv", args), patch.object(image.urllib.request, "urlopen", return_value=reply()) as network:
                    with contextlib.redirect_stdout(stream), self.assertRaises(SystemExit) as stopped:
                        image.main()
                self.assertEqual(stopped.exception.code, 0)
                data = json.loads(stream.getvalue())
                if dry:
                    network.assert_not_called()
                    self.assertEqual([p["provider"] for p in data["providers"]], ["9router", "sub2api"])
                    self.assertFalse(output.exists())
                else:
                    self.assertEqual(output.read_bytes(), PNG)
                    self.assertEqual(data["model"], "actual-image-model")
                    self.assertEqual(data["configured_model"], "gpt-image-2.5")

    def test_bad_selector_timeout_stops_before_network(self):
        for changes in ({"API_IMAGE_PROVIDER": ""}, {"API_IMAGE_PROVIDER": "9router|9router"},
                        {"API_IMAGE_PROVIDER": "zpro"}, {"API_IMAGE_TIMEOUT": "0"},
                        {"API_IMAGE_TIMEOUT": "nine-secret"}):
            with patch.object(image, "load_candidate_env", return_value=dict(ENV, **changes)):
                with self.assertRaises(ValueError):
                    image.resolve_providers()


class EnvFileTests(unittest.TestCase):
    def test_cwd_env_read_only_environment_precedence_and_empty_key(self):
        with tempfile.TemporaryDirectory() as temp:
            env_file = Path(temp) / ".env"
            content = "API_IMAGE_PROVIDER=9router|sub2api\nAPI_IMAGE_NINEROUTER_KEY=\nAPI_IMAGE_TIMEOUT=99\n"
            env_file.write_text(content, encoding="utf-8")
            with patch.object(image.Path, "cwd", return_value=Path(temp)), patch.dict(os.environ, {"API_IMAGE_TIMEOUT": "12"}, clear=True):
                env = image.load_candidate_env()
                self.assertEqual(env["API_IMAGE_NINEROUTER_KEY"], "")
                self.assertEqual(env["API_IMAGE_TIMEOUT"], "12")
                configs = image.resolve_providers()
                with patch.object(image.urllib.request, "urlopen") as network:
                    result, _, attempts = image.run_providers(configs, **INPUTS)
                network.assert_not_called()
            self.assertEqual(env_file.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
