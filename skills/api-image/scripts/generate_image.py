#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Image gateway CLI: isolated provider configuration, bounded fallback, JSON/SSE.
Standard library only. Reads cwd/.env and environment; never writes configuration.
"""
from __future__ import annotations

import argparse
import base64
import datetime
import json
import mimetypes
import os
import re
import socket
import uuid
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ASPECT_RATIO_MAP = {
    "9:16": "1024x1792",
    "16:9": "1792x1024",
    "1:1": "1024x1024",
    "3:4": "1024x1365",
    "4:3": "1365x1024",
    "2:3": "1024x1536",
    "3:2": "1536x1024",
}

DEFAULT_TIMEOUT = 300


def load_candidate_env() -> Dict[str, str]:
    """Tìm và nạp biến môi trường từ file .env ưu tiên thư mục hiện tại."""
    env_vars: Dict[str, str] = {}
    candidate_files = [
        Path.cwd() / ".env",
    ]
    for p in candidate_files:
        if not p.is_file():
            continue
        try:
            for line in p.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k not in env_vars:
                    env_vars[k] = v
        except Exception:
            pass

    env_keys = (
        "AI_IMAGE_KEY", "AI_IMAGE_API_KEY", "AI_API_KEY",
        "AI_IMAGE_URL", "AI_IMAGE_ENDPOINT_URL", "AI_BASE_URL",
        "AI_IMAGE_MODEL", "AI_MODEL",
        "AI_IMAGE_TYPE", "AI_TIMEOUT",
    )
    for k in env_keys:
        val = os.getenv(k, "")
        if val:
            env_vars[k] = val
    for k, val in os.environ.items():
        if k.startswith("API_IMAGE_"):
            env_vars[k] = val
    return env_vars


class ProviderError(RuntimeError):
    """Only fixed, public messages may cross the transport boundary."""

    def __init__(self, reason: str, fallback: bool = False):
        super().__init__(reason)
        self.fallback = fallback


def classify_error(error: Any, status: Optional[int] = None) -> ProviderError:
    # Inspect upstream privately; never return its text, headers or URLs.
    value = json.dumps(error, ensure_ascii=False).lower()
    if any(word in value for word in (
        "safety", "moderation", "content_policy", "content policy", "refusal",
        "refused", "responsible_ai", "prohibited", "content_filter", "policy_violation",
    )):
        return ProviderError("safety_refusal: dừng, không chuyển provider")
    if any(word in value for word in ("timeout", "timed out", "deadline")) or status in (408, 504):
        return ProviderError("submission_unknown: có thể đã nhận job; không gửi lại")
    if any(word in value for word in ("invalid_parameter", "invalid size", "invalid image", "unsupported image format", "unsupported size", "invalid_request_error")):
        return ProviderError("invalid_input: sửa đầu vào trước khi gửi lại")
    if any(word in value for word in ("unsupported", "not supported", "not_support")):
        return ProviderError("unsupported_task: provider không hỗ trợ tác vụ/đầu vào", True)
    if status in (401, 402, 403, 404, 405, 429, 500, 502, 503) or any(
        word in value for word in ("quota", "rate_limit", "insufficient_credit", "permission_denied", "overloaded")
    ):
        return ProviderError(f"provider_unavailable: HTTP {status}" if status else "provider_unavailable: quota/quyền/dịch vụ", True)
    return ProviderError("invalid_input_or_response: cần kiểm tra đầu vào/phản hồi trước khi gửi lại")


def config_issues(cfg: Dict[str, Any]) -> List[str]:
    issues = [f"missing_{key}" for key in ("base_url", "api_key", "model", "image_type") if not cfg.get(key)]
    if cfg.get("image_type") not in ("sub2api", "edit", "9router", "response", "generation", "generations", "responses", "omni", "omniroute"):
        issues.append("unsupported_protocol")
    try:
        parsed = urllib.parse.urlsplit(cfg.get("base_url", ""))
    except ValueError:
        return issues + ["invalid_base_url"]
    if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        issues.append("invalid_base_url")
    return issues


def resolve_providers(cli_key=None, cli_url=None, cli_model=None, cli_type=None):
    env = load_candidate_env()
    if "API_IMAGE_PROVIDER" not in env and not any(k.startswith("API_IMAGE_") for k in env):
        cfg = resolve_config(cli_key, cli_url, cli_model, cli_type)
        cfg["provider"] = "project-" + cfg["image_type"]
        return [cfg]
    names = [name.strip().lower() for name in env.get("API_IMAGE_PROVIDER", "9router|sub2api").split("|")]
    if not names or len(names) != len(set(names)) or any(name not in ("9router", "sub2api") for name in names):
        raise ValueError("API_IMAGE_PROVIDER: 9router, sub2api hoặc chuỗi phân cách bằng |")
    timeout = int(env.get("API_IMAGE_TIMEOUT", DEFAULT_TIMEOUT))
    if timeout <= 0:
        raise ValueError("API_IMAGE_TIMEOUT phải lớn hơn 0")
    configs = []
    for index, name in enumerate(names):
        prefix = "NINEROUTER" if name == "9router" else "SUB2API"
        cfg = {"provider": name, "timeout": timeout, "image_type": "sub2api" if name == "sub2api" else "9router"}
        for field, suffix in (("base_url", "URL"), ("api_key", "KEY"), ("model", "MODEL")):
            cfg[field] = env.get(f"API_IMAGE_{prefix}_{suffix}", "").strip()
        # Existing CLI flags override the first tier only, never leak to fallback.
        if index == 0:
            for field, override in (("api_key", cli_key), ("base_url", cli_url), ("model", cli_model), ("image_type", cli_type)):
                if override is not None:
                    cfg[field] = override
        if name == "sub2api":
            cfg["image_type"] = "sub2api"
        cfg["base_url"] = cfg["base_url"].rstrip("/")
        configs.append(cfg)
    return configs


def run_providers(configs, **inputs):
    attempts = []
    for cfg in configs:
        attempt = {"provider": cfg["provider"], "model": cfg["model"]}
        attempts.append(attempt)
        issues = config_issues(cfg)
        if issues:
            attempt.update(status="skipped", reason=", ".join(issues))
            continue
        try:
            result = call_project_image_api(**{key: cfg[key] for key in (
                "base_url", "api_key", "model", "image_type", "timeout"
            )}, **inputs)
        except ProviderError as exc:
            attempt.update(status="failed", reason=str(exc))
            if exc.fallback:
                continue
            return None, cfg, attempts
        except Exception:
            attempt.update(status="failed", reason="unexpected_error: dừng để tránh gửi trùng hoặc lộ dữ liệu")
            return None, cfg, attempts
        attempt.update(status="success")
        return result, cfg, attempts
    return None, None, attempts


def public_json(value, **kwargs):
    """Redact configured credentials even if echoed in metadata or prompt."""
    env = load_candidate_env()
    keys = [v for k, v in env.items() if (k.endswith("_KEY") or k == "AI_API_KEY") and v]
    if "--api-key" in sys.argv:
        index = sys.argv.index("--api-key") + 1
        if index < len(sys.argv):
            keys.append(sys.argv[index])
    keys.extend(arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--api-key="))

    def scrub(item):
        if isinstance(item, str):
            for key in sorted(keys, key=len, reverse=True):
                item = item.replace(key, "[REDACTED]")
            return item
        if isinstance(item, dict):
            return {k: scrub(v) for k, v in item.items()}
        if isinstance(item, list):
            return [scrub(v) for v in item]
        return item

    return json.dumps(scrub(value), **kwargs)


def check_response_error(event):
    if isinstance(event, list):
        for item in event:
            check_response_error(item)
    elif isinstance(event, dict):
        if event.get("refusal") or "refusal" in str(event.get("type", "")):
            raise ProviderError("safety_refusal: dừng, không chuyển provider")
        if event.get("error"):
            raise classify_error(event["error"])
        if event.get("status") in ("failed", "cancelled", "incomplete"):
            raise ProviderError("response_unknown: job chưa hoàn tất; kiểm tra trạng thái trước khi gửi lại")
        for key in ("response", "output", "content"):
            if key in event:
                check_response_error(event[key])


def resolve_config(
    cli_key: Optional[str] = None,
    cli_url: Optional[str] = None,
    cli_model: Optional[str] = None,
    cli_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Tự động phát hiện cấu hình và provider từ .env và tham số CLI."""
    env = load_candidate_env()

    # 1. API Key: Ưu tiên AI_IMAGE_KEY (chuẩn project) -> fallback AI_IMAGE_API_KEY, AI_API_KEY
    api_key = (
        cli_key
        or env.get("AI_IMAGE_KEY")
        or env.get("AI_IMAGE_API_KEY")
        or env.get("AI_API_KEY")
        or ""
    ).strip()

    # 2. Base URL / Endpoint: Ưu tiên AI_IMAGE_URL (chuẩn project) -> fallback AI_IMAGE_ENDPOINT_URL, AI_BASE_URL
    raw_url = (
        cli_url
        or env.get("AI_IMAGE_URL")
        or env.get("AI_IMAGE_ENDPOINT_URL")
        or env.get("AI_BASE_URL")
        or ""
    ).strip().rstrip("/")

    # 3. Model: Ưu tiên AI_IMAGE_MODEL -> fallback AI_MODEL
    raw_model = (
        cli_model
        or env.get("AI_IMAGE_MODEL")
        or env.get("AI_MODEL")
        or ""
    ).strip()
    model = raw_model.split(",")[0].strip() if raw_model else "cx/gpt-5.6-sol-image"

    # 4. Phát hiện Image Type (edit | 9router | response)
    image_type = (cli_type or env.get("AI_IMAGE_TYPE", "")).strip().lower()
    if not image_type:
        url_lower = raw_url.lower()
        if "9router" in url_lower:
            image_type = "9router"
        elif "omniroute" in url_lower:
            image_type = "response"
        else:
            image_type = "edit"

    timeout = int(env.get("AI_TIMEOUT", DEFAULT_TIMEOUT))

    return {
        "api_key": api_key,
        "base_url": raw_url,
        "model": model,
        "image_type": image_type or "edit",
        "timeout": timeout,
    }


def encode_image_to_data_uri(image_path: Path) -> str:
    """Mã hóa ảnh địa phương sang Base64 Data URI."""
    if not image_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy ảnh tham chiếu: {image_path}")

    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type:
        mime_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"

    data_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{data_b64}"


def robust_json_loads(s: str) -> Optional[Any]:
    """Parse JSON an toàn, hỗ trợ trích xuất block JSON trong text."""
    if not s or not isinstance(s, str):
        return None
    s_trimmed = s.strip()
    try:
        return json.loads(s_trimmed)
    except Exception:
        pass

    brace_start = s_trimmed.find("{")
    brace_end = s_trimmed.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        candidate = s_trimmed[brace_start:brace_end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
        try:
            fixed = re.sub(r"(?<=\{|\,)\s*\'([a-zA-Z0-9_\-\.]+)\'\s*:", r' "\1":', candidate)
            fixed = re.sub(r",\s*([\}\]])", r"\1", fixed)
            return json.loads(fixed)
        except Exception:
            pass
    return None


def extract_image_from_text(text: str) -> Optional[Tuple[str, str]]:
    """Trích xuất image URL, Base64 data URI, hoặc SVG từ response text."""
    if not text:
        return None
    text = text.strip()

    b64_match = re.search(r'(data:image\/[a-zA-Z0-9\+\-\.]+;base64,[A-Za-z0-9+/=]+)', text)
    if b64_match:
        return b64_match.group(1), "base64"

    md_match = re.search(r'!\[.*?\]\((https?:\/\/[^\s\)\"\']+)\)', text)
    if md_match:
        return md_match.group(1), "url"

    md_b64_match = re.search(r'!\[.*?\]\((data:image\/[^\s\)\"\']+)\)', text)
    if md_b64_match:
        return md_b64_match.group(1), "base64"

    svg_match = re.search(r'(<svg[\s\S]*?<\/svg>)', text, re.IGNORECASE)
    if svg_match:
        svg_content = svg_match.group(1).strip()
        svg_b64 = base64.b64encode(svg_content.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{svg_b64}", "svg"

    url_match = re.search(r'(https?:\/\/[^\s\)\"\'<>]+?\.(?:png|jpg|jpeg|webp|gif))(?:\?[^\s\)\"\'<>]*)?', text, re.IGNORECASE)
    if url_match:
        return url_match.group(0), "url"

    if text.startswith("http://") or text.startswith("https://"):
        first_line = text.splitlines()[0].strip()
        if " " not in first_line:
            return first_line, "url"

    parsed = robust_json_loads(text)
    if isinstance(parsed, dict):
        if "data" in parsed and isinstance(parsed["data"], list) and len(parsed["data"]) > 0:
            item = parsed["data"][0]
            if isinstance(item, dict):
                if item.get("b64_json"):
                    return f"data:image/png;base64,{item['b64_json']}", "base64"
                if item.get("url"):
                    return item["url"], "url"
        for key in ("url", "image_url", "image"):
            val = parsed.get(key)
            if val and isinstance(val, str):
                fmt = "url" if val.startswith("http") else "base64"
                return val, fmt
        if parsed.get("b64_json"):
            return f"data:image/png;base64,{parsed['b64_json']}", "base64"

    return None


def fetch_image_data(src: str, timeout: int = 60) -> Tuple[bytes, str]:
    """Chuyển đổi URL hoặc Data URI thành bytes và mime_type."""
    if src.startswith("data:image/"):
        header, b64_str = src.split(",", 1)
        mime = header.split(";")[0].replace("data:", "")
        return base64.b64decode(b64_str), mime

    ctx = ssl.create_default_context()
    req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        data = resp.read()
        mime = resp.headers.get_content_type() or "image/png"
        return data, mime


def build_project_payload(
    image_type: str,
    base_url: str,
    model: str,
    prompt: str,
    ref_data_uri: Optional[str] = None,
    size: str = "auto",
    quality: str = "auto",
    image_detail: str = "high",
) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
    """Build protocol-specific payload without discarding references."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream, application/json",
    }

    if image_type == "sub2api":
        payload = {"model": model, "prompt": prompt, "n": 1,
                   "size": size or "auto", "quality": quality or "auto"}
        if ref_data_uri:
            payload["image"] = ref_data_uri
        return f"{base_url}/images/{'edits' if ref_data_uri else 'generations'}", payload, headers

    if image_type in ("9router", "generation", "generations"):
        endpoint = f"{base_url}/images/generations"
        prepared_prompt = prompt.replace("[ATTACHED_PHOTO]", "the attached reference image") if "[ATTACHED_PHOTO]" in prompt else prompt
        payload = {
            "model": model,
            "prompt": prepared_prompt,
            "n": 1,
            "size": size or "auto",
            "quality": quality or "auto",
            "background": "auto",
            "image_detail": image_detail or "high",
            "output_format": "png",
            "response_format": "b64_json",
            "stream": True,
        }
        if ref_data_uri:
            payload["image"] = ref_data_uri
        return endpoint, payload, headers

    elif image_type in ("response", "responses", "omni", "omniroute"):
        endpoint = f"{base_url}/responses"
        prepared_prompt = prompt.replace("[ATTACHED_PHOTO]", "the input image") if "[ATTACHED_PHOTO]" in prompt else prompt
        content_list: List[Dict[str, Any]] = []
        if ref_data_uri:
            content_list.append({
                "type": "input_image",
                "image_url": ref_data_uri,
                "detail": image_detail or "high",
            })
        content_list.append({
            "type": "input_text",
            "text": prepared_prompt,
        })
        payload = {
            "model": model,
            "input": [{"role": "user", "content": content_list}],
            "tools": [{
                "type": "image_generation",
                "model": model,
                "action": "edit" if ref_data_uri else "generate",
                "quality": quality or "auto",
                "size": size or "auto",
                "output_format": "png",
            }],
            "tool_choice": {"type": "image_generation"},
        }
        return endpoint, payload, headers

    elif image_type == "edit":
        # Legacy JSON edits protocol (distinct from sub2api multipart edits).
        endpoint = f"{base_url}/images/edits"
        image_id = "input_file_0.png"
        prepared_prompt = prompt.replace("[ATTACHED_PHOTO]", image_id) if "[ATTACHED_PHOTO]" in prompt else prompt
        payload = {
            "model": model,
            "prompt": prepared_prompt,
            "n": 1,
            "size": size or "auto",
            "quality": quality or "auto",
            "background": "auto",
            "image_detail": image_detail or "high",
            "output_format": "png",
            "response_format": "b64_json",
            "stream": True,
            "images": [],
        }
        if ref_data_uri:
            payload["images"].append({
                "id": image_id,
                "image_url": ref_data_uri,
            })
        return endpoint, payload, headers

    raise ProviderError("unsupported_protocol", True)


def call_project_image_api(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    image_type: str = "edit",
    ref_data_uri: Optional[str] = None,
    size: str = "auto",
    quality: str = "auto",
    image_detail: str = "high",
    timeout: int = DEFAULT_TIMEOUT,
) -> Tuple[bytes, str, str, Optional[str]]:
    """Gọi upstream API theo kiến trúc provider của project (hỗ trợ SSE & JSON)."""
    endpoint, payload, headers = build_project_payload(
        image_type=image_type,
        base_url=base_url,
        model=model,
        prompt=prompt,
        ref_data_uri=ref_data_uri,
        size=size,
        quality=quality,
        image_detail=image_detail,
    )
    headers["Authorization"] = f"Bearer {api_key}"

    ctx = ssl.create_default_context()

    if image_type == "sub2api" and ref_data_uri:
        # Standard edits API consumes a binary image in multipart/form-data.
        boundary = "api-image-" + uuid.uuid4().hex
        chunks = []
        for key, value in payload.items():
            if key != "image":
                chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode("utf-8"))
        image_header, encoded = ref_data_uri.split(",", 1)
        mime = image_header.split(";")[0].removeprefix("data:")
        extension = mimetypes.guess_extension(mime) or ".png"
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="reference{extension}"\r\nContent-Type: {mime}\r\n\r\n'.encode("ascii"))
        chunks.extend((base64.b64decode(encoded), f"\r\n--{boundary}--\r\n".encode("ascii")))
        req_data = b"".join(chunks)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    else:
        req_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8", errors="ignore")
        raise classify_error(robust_json_loads(err_body) or err_body, err.code) from None
    except (TimeoutError, socket.timeout):
        raise ProviderError("submission_unknown: timeout; không có API trạng thái được cấu hình, cần kiểm tra job trước khi gửi lại") from None
    except Exception:
        raise ProviderError("submission_unknown: kết nối gián đoạn; kiểm tra job trước khi gửi lại") from None

    # Trích xuất ảnh từ SSE line hoặc JSON body
    candidates = [body] + [
        line[5:].strip() for line in body.splitlines()
        if line.startswith("data:") and line[5:].strip() not in ("", "[DONE]")
    ]

    # Inspect all error/refusal events before accepting an earlier partial image.
    for candidate in candidates:
        event = robust_json_loads(candidate)
        check_response_error(event)

    image_source: Optional[str] = None
    reported_model = None
    for candidate in reversed(candidates):
        data = robust_json_loads(candidate)
        if isinstance(data, dict):
            reported_model = data.get("model") or reported_model
            response = data.get("response", data)
            if isinstance(response, dict):
                reported_model = response.get("model") or reported_model
                for item in response.get("output", []):
                    if isinstance(item, dict) and item.get("type") == "image_generation_call" and item.get("result"):
                        image_source = "data:image/png;base64," + item["result"]
                        reported_model = item.get("model") or reported_model
                        break
                    if isinstance(item, dict) and any(part.get("type") == "refusal" for part in item.get("content", []) if isinstance(part, dict)):
                        raise ProviderError("safety_refusal: dừng, không chuyển provider")
                if image_source:
                    break
            if "error" in data:
                raise classify_error(data["error"]) from None
            if data.get("type") in ("refusal", "response.refusal.done") or data.get("refusal"):
                raise ProviderError("safety_refusal: dừng, không chuyển provider")

            if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                item = data["data"][0]
                if isinstance(item, dict):
                    if item.get("b64_json"):
                        image_source = f"data:image/png;base64,{item['b64_json']}"
                        break
                    if item.get("url"):
                        image_source = item["url"]
                        break

            for k in ("image", "url", "image_url"):
                val = data.get(k)
                if val and isinstance(val, str):
                    image_source = val
                    break
            if image_source:
                break

            if data.get("b64_json"):
                image_source = f"data:image/png;base64,{data['b64_json']}"
                break

        extracted = extract_image_from_text(candidate)
        if extracted:
            image_source = extracted[0]
            break

    if not image_source:
        raise ProviderError("response_unknown: không có ảnh; kiểm tra job, không gửi lại")

    try:
        img_bytes, mime = fetch_image_data(image_source, timeout=timeout)
    except Exception:
        raise ProviderError("download_failed: job đã trả ảnh; không tạo lại job") from None
    return img_bytes, mime, prompt, reported_model


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI tạo ảnh qua API tương thích OpenAI (Edits, Generations, Responses)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--prompt", "-p", type=str, help="Prompt mô tả ảnh")
    parser.add_argument("--prompt-file", type=str, help="Đường dẫn file .txt chứa prompt")
    parser.add_argument(
        "--aspect-ratio",
        type=str,
        choices=list(ASPECT_RATIO_MAP.keys()),
        default=None,
        help="Tỷ lệ khung hình (VD: 9:16)",
    )
    parser.add_argument(
        "--size",
        type=str,
        default=None,
        help="Kích thước pixel (VD: 1024x1792, auto)",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=None,
        help="Model cho tầng đầu (hoặc AI_IMAGE_MODEL trong chế độ legacy)",
    )
    parser.add_argument(
        "--image-type",
        "-t",
        type=str,
        choices=["edit", "9router", "response"],
        default=None,
        help="Giao thức API cho tầng đầu (edit, 9router, response)",
    )
    parser.add_argument(
        "--ref-image",
        "-i",
        type=str,
        default=None,
        help="Đường dẫn ảnh tham chiếu (Image-to-Image / Lock Identity)",
    )
    parser.add_argument(
        "--quality",
        type=str,
        choices=["standard", "hd", "auto"],
        default="auto",
        help="Chất lượng ảnh",
    )
    parser.add_argument(
        "--image-detail",
        type=str,
        choices=["high", "low", "auto"],
        default="high",
        help="Độ chi tiết ảnh tham chiếu",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Đường dẫn file ảnh đầu ra",
    )
    parser.add_argument(
        "--session-dir",
        type=str,
        default=None,
        help="Thư mục session trong .scratch/ (tự động lưu vào output/visual.png)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API Key cho tầng đầu (hoặc AI_IMAGE_KEY trong chế độ legacy)",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Base URL cho tầng đầu (hoặc AI_IMAGE_URL trong chế độ legacy)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Hiển thị thứ tự và trạng thái cấu hình; không gọi mạng",
    )

    args = parser.parse_args()

    # 1. Thu thập văn bản prompt
    prompt_text = ""
    if args.prompt:
        prompt_text = args.prompt.strip()
    elif args.prompt_file:
        pf = Path(args.prompt_file)
        if not pf.is_file():
            print(public_json({"status": "error", "message": f"File prompt không tồn tại: {pf}"}, ensure_ascii=False))
            sys.exit(1)
        prompt_text = pf.read_text(encoding="utf-8").strip()

    if not prompt_text and not args.dry_run:
        print(public_json({"status": "error", "message": "Vui lòng cung cấp prompt qua --prompt hoặc --prompt-file"}, ensure_ascii=False))
        sys.exit(1)

    # 2. Xác định kích thước
    final_size = args.size or (ASPECT_RATIO_MAP.get(args.aspect_ratio) if args.aspect_ratio else "auto")

    # 3. Nạp cấu hình & auto-detect provider
    try:
        configs = resolve_providers(
            cli_key=args.api_key,
            cli_url=args.url,
            cli_model=args.model,
            cli_type=args.image_type,
        )
    except Exception as exc:
        print(public_json({"status": "error", "message": "Cấu hình không hợp lệ; kiểm tra danh sách provider và timeout"}, ensure_ascii=False))
        sys.exit(1)

    ref_path = Path(args.ref_image).resolve() if args.ref_image else None
    ref_data_uri: Optional[str] = None
    if ref_path:
        if not ref_path.is_file():
            print(public_json({"status": "error", "message": f"Ảnh tham chiếu không tồn tại: {ref_path}"}, ensure_ascii=False))
            sys.exit(1)
        ref_data_uri = encode_image_to_data_uri(ref_path)

    # 4. Dry Run
    if args.dry_run:
        summaries = [{"provider": cfg["provider"], "model": cfg["model"],
                      "image_type": cfg["image_type"], "configured": not config_issues(cfg),
                      "issues": config_issues(cfg)} for cfg in configs]
        dry_info = {"status": "dry_run", "providers": summaries,
                    "size": final_size, "quality": args.quality,
                    "has_reference": bool(ref_data_uri)}
        if len(configs) == 1 and configs[0]["provider"].startswith("project-"):
            dry_info.update(provider=configs[0]["provider"], base_url=configs[0]["base_url"] if "invalid_base_url" not in config_issues(configs[0]) else "[invalid URL omitted]",
                            model=configs[0]["model"], image_type=configs[0]["image_type"])
        print(public_json(dry_info, ensure_ascii=False, indent=2))
        sys.exit(0)

    # 6. Xác định file đầu ra trong .scratch/
    if args.output:
        out_file = Path(args.output).resolve()
    else:
        if args.session_dir:
            session_dir = Path(args.session_dir).resolve()
        else:
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            session_dir = Path.cwd() / ".scratch" / f"{today_str}_api-image_default"
        out_file = session_dir / "output" / "visual.png"


    # 7. Thực thi sinh ảnh
    try:
        response, cfg, attempts = run_providers(
            configs,
            prompt=prompt_text,
            ref_data_uri=ref_data_uri,
            size=final_size,
            quality=args.quality,
            image_detail=args.image_detail,
        )
        if response is None:
            print(public_json({"status": "error", "message": "Chuỗi provider thất bại hoặc đã dừng an toàn",
                              "attempts": attempts}, ensure_ascii=False, indent=2))
            sys.exit(1)
        image_bytes, mime, revised_prompt, reported_model = response
        engine_name = cfg["provider"]

        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_bytes(image_bytes)

        result = {
            "status": "success",
            "engine": engine_name,
            "provider": cfg["provider"],
            "attempts": attempts,
            "model": reported_model or cfg["model"],
            "configured_model": cfg["model"],
            "reported_model": reported_model,
            "model_source": "upstream" if reported_model else "configured; upstream did not report model",
            "image_type": cfg["image_type"],
            "aspect_ratio": args.aspect_ratio or "auto",
            "size": final_size,
            "quality": args.quality,
            "output_file": str(out_file),
            "file_size_bytes": out_file.stat().st_size,
            "media_type": mime,
            "revised_prompt": revised_prompt,
        }
        print(public_json(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    except Exception as exc:
        err_res = {
            "status": "error",
            "message": "Không thể lưu hoặc xử lý kết quả; không tự gửi lại job",
            "attempts": attempts if "attempts" in locals() else [],
        }
        print(public_json(err_res, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
