#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_image.py

Script tạo ảnh đa provider độc lập:
- OpenAI Edits (/v1/images/edits - ZPro / OpenAI chuẩn)
- OpenAI Generations (/v1/images/generations - 9router flat image)
- OpenAI Responses (/v1/responses - OmniRoute multimodal tool_choice)
- Google AI Studio Direct (Imagen-3 predict API)

Đặc tính:
- Thuần Python 100% (Zero dependencies).
- Tự động detect provider từ .env (AI_IMAGE_KEY, AI_IMAGE_URL, AI_IMAGE_MODEL, AI_IMAGE_TYPE).
- Hỗ trợ ảnh tham chiếu (Image-to-Image / Lock Identity / [ATTACHED_PHOTO]).
- Cô lập thư mục phiên làm việc trong .scratch/.
"""
from __future__ import annotations

import argparse
import base64
import datetime
import json
import mimetypes
import os
import re
import secrets
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

DEFAULT_ASPECT_RATIO = "9:16"
DEFAULT_SIZE = ASPECT_RATIO_MAP["9:16"]
DEFAULT_TIMEOUT = 300


def load_candidate_env() -> Dict[str, str]:
    """Tìm và nạp biến môi trường từ file .env ưu tiên thư mục hiện tại."""
    env_vars: Dict[str, str] = {}
    candidate_files = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[4] / ".env",
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
                if k not in env_vars and v:
                    env_vars[k] = v
        except Exception:
            pass

    env_keys = (
        "AI_IMAGE_KEY", "AI_IMAGE_API_KEY", "AI_API_KEY",
        "AI_IMAGE_URL", "AI_IMAGE_ENDPOINT_URL", "AI_BASE_URL",
        "AI_IMAGE_MODEL", "AI_MODEL",
        "AI_IMAGE_TYPE", "AI_IMAGE_USE_GEMINI", "AI_TIMEOUT",
    )
    for k in env_keys:
        val = os.getenv(k, "")
        if val:
            env_vars[k] = val
    return env_vars


def resolve_config(
    cli_key: Optional[str] = None,
    cli_url: Optional[str] = None,
    cli_model: Optional[str] = None,
    cli_type: Optional[str] = None,
    cli_use_gemini: bool = False,
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

    # 4. Phát hiện Google AI Studio
    use_gemini_env = str(env.get("AI_IMAGE_USE_GEMINI", "false")).strip().lower() in ("true", "1", "yes")
    is_gemini_key = api_key.startswith("AIzaSy")
    is_gemini_model = "imagen-" in model.lower()
    use_gemini = cli_use_gemini or use_gemini_env or is_gemini_key or is_gemini_model

    # 5. Phát hiện Image Type (edit | 9router | response)
    image_type = (cli_type or env.get("AI_IMAGE_TYPE", "")).strip().lower()
    if not image_type and not use_gemini:
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
        "use_gemini": use_gemini,
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
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        data = resp.read()
        mime = resp.headers.get_content_type() or "image/png"
        return data, mime


def call_gemini_image_api(
    prompt: str,
    api_key: str,
    model: str,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    timeout: int = DEFAULT_TIMEOUT,
) -> Tuple[bytes, str, str]:
    """Gọi trực tiếp Google AI Studio API cho sinh ảnh."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": aspect_ratio,
            "personGeneration": "ALLOW_ADULT",
            "outputMimeType": "image/png",
        }
    }

    req_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    predictions = data.get("predictions", [])
    if not predictions:
        raise RuntimeError(f"Google AI Studio không trả về ảnh nào: {data}")

    b64_img = predictions[0].get("bytesBase64Encoded")
    if not b64_img:
        raise RuntimeError(f"Dữ liệu ảnh trả về không hợp lệ: {predictions[0]}")

    return base64.b64decode(b64_img), "image/png", prompt


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
    """Tạo endpoint, payload và headers chuẩn theo 3 provider của project."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream, application/json",
    }

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

    else:
        # Default: ZPro / OpenAI Image Edits API (/images/edits)
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
) -> Tuple[bytes, str, str]:
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
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8", errors="ignore")
        parsed = robust_json_loads(err_body)
        msg = err_body[:300]
        if isinstance(parsed, dict) and "error" in parsed:
            err_obj = parsed["error"]
            msg = err_obj.get("message") if isinstance(err_obj, dict) else str(err_obj)
        raise RuntimeError(f"HTTP {err.code} từ {endpoint}: {msg}")
    except Exception as exc:
        raise RuntimeError(f"Lỗi kết nối tới {endpoint}: {exc}")

    # Trích xuất ảnh từ SSE line hoặc JSON body
    candidates = [body] + [
        line[5:].strip() for line in body.splitlines()
        if line.startswith("data:") and line[5:].strip() not in ("", "[DONE]")
    ]

    image_source: Optional[str] = None
    for candidate in reversed(candidates):
        data = robust_json_loads(candidate)
        if isinstance(data, dict):
            if "error" in data:
                err_obj = data["error"]
                msg = err_obj.get("message") if isinstance(err_obj, dict) else str(err_obj)
                raise RuntimeError(f"Lỗi từ mô hình AI: {msg}")

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
        raise RuntimeError("API không trả về ảnh hợp lệ trong payload hoặc stream")

    img_bytes, mime = fetch_image_data(image_source, timeout=timeout)
    return img_bytes, mime, prompt


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI tạo ảnh đa provider (OpenAI Edits, 9router, OmniRoute, Google AI Studio)",
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
        help="Tên model (ghi đè AI_IMAGE_MODEL)",
    )
    parser.add_argument(
        "--image-type",
        "-t",
        type=str,
        choices=["edit", "9router", "response"],
        default=None,
        help="Provider type của project (edit, 9router, response)",
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
        help="API Key thủ công (ghi đè AI_IMAGE_KEY)",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Base URL thủ công (ghi đè AI_IMAGE_URL)",
    )
    parser.add_argument(
        "--use-gemini",
        action="store_true",
        help="Sử dụng trực tiếp Google AI Studio API",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Kiểm tra cấu hình và in payload không gọi API",
    )

    args = parser.parse_args()

    # 1. Thu thập văn bản prompt
    prompt_text = ""
    if args.prompt:
        prompt_text = args.prompt.strip()
    elif args.prompt_file:
        pf = Path(args.prompt_file)
        if not pf.is_file():
            print(json.dumps({"status": "error", "message": f"File prompt không tồn tại: {pf}"}, ensure_ascii=False))
            sys.exit(1)
        prompt_text = pf.read_text(encoding="utf-8").strip()

    if not prompt_text and not args.dry_run:
        print(json.dumps({"status": "error", "message": "Vui lòng cung cấp prompt qua --prompt hoặc --prompt-file"}, ensure_ascii=False))
        sys.exit(1)

    # 2. Xác định kích thước
    final_size = args.size or (ASPECT_RATIO_MAP.get(args.aspect_ratio) if args.aspect_ratio else "auto")

    # 3. Nạp cấu hình & auto-detect provider
    try:
        cfg = resolve_config(
            cli_key=args.api_key,
            cli_url=args.url,
            cli_model=args.model,
            cli_type=args.image_type,
            cli_use_gemini=args.use_gemini,
        )
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False))
        sys.exit(1)

    ref_path = Path(args.ref_image).resolve() if args.ref_image else None
    ref_data_uri: Optional[str] = None
    if ref_path:
        if not ref_path.is_file():
            print(json.dumps({"status": "error", "message": f"Ảnh tham chiếu không tồn tại: {ref_path}"}, ensure_ascii=False))
            sys.exit(1)
        ref_data_uri = encode_image_to_data_uri(ref_path)

    # 4. Dry Run
    if args.dry_run:
        dry_info = {
            "status": "dry_run",
            "provider": "google-ai-studio" if cfg["use_gemini"] else f"project-{cfg['image_type']}",
            "base_url": "https://generativelanguage.googleapis.com" if cfg["use_gemini"] else cfg["base_url"],
            "model": cfg["model"],
            "image_type": "gemini" if cfg["use_gemini"] else cfg["image_type"],
            "size": final_size,
            "aspect_ratio": args.aspect_ratio or "N/A",
            "quality": args.quality,
            "has_api_key": bool(cfg["api_key"]),
            "api_key_length": len(cfg["api_key"]) if cfg["api_key"] else 0,
            "ref_image": str(ref_path) if ref_path else None,
            "prompt": prompt_text,
        }
        print(json.dumps(dry_info, ensure_ascii=False, indent=2))
        sys.exit(0)

    # 5. Kiểm tra API Key
    if not cfg["api_key"]:
        err_response = {
            "status": "error",
            "message": "Không tìm thấy API Key. Cấu hình AI_IMAGE_KEY trong file .env hoặc truyền qua --api-key.",
        }
        print(json.dumps(err_response, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 6. Xác định file đầu ra trong .scratch/
    if args.output:
        out_file = Path(args.output).resolve()
    else:
        if args.session_dir:
            session_dir = Path(args.session_dir).resolve()
        else:
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            session_dir = Path.cwd() / ".scratch" / f"{today_str}_image-generate_default"
        out_file = session_dir / "output" / "visual.png"

    out_file.parent.mkdir(parents=True, exist_ok=True)

    # 7. Thực thi sinh ảnh
    try:
        if cfg["use_gemini"]:
            image_bytes, mime, revised_prompt = call_gemini_image_api(
                prompt=prompt_text,
                api_key=cfg["api_key"],
                model=cfg["model"],
                aspect_ratio=args.aspect_ratio or DEFAULT_ASPECT_RATIO,
                timeout=cfg["timeout"],
            )
            engine_name = "google-ai-studio"
        else:
            if not cfg["base_url"]:
                raise RuntimeError("Thiếu AI_IMAGE_URL trong .env hoặc --url cho chế độ project gateway")
            image_bytes, mime, revised_prompt = call_project_image_api(
                base_url=cfg["base_url"],
                api_key=cfg["api_key"],
                model=cfg["model"],
                prompt=prompt_text,
                image_type=cfg["image_type"],
                ref_data_uri=ref_data_uri,
                size=final_size,
                quality=args.quality,
                image_detail=args.image_detail,
                timeout=cfg["timeout"],
            )
            engine_name = f"project-{cfg['image_type']}"

        out_file.write_bytes(image_bytes)

        result = {
            "status": "success",
            "engine": engine_name,
            "model": cfg["model"],
            "image_type": "gemini" if cfg["use_gemini"] else cfg["image_type"],
            "aspect_ratio": args.aspect_ratio or "auto",
            "size": final_size,
            "quality": args.quality,
            "output_file": str(out_file),
            "file_size_bytes": out_file.stat().st_size,
            "media_type": mime,
            "revised_prompt": revised_prompt,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    except Exception as exc:
        err_res = {
            "status": "error",
            "engine": "google-ai-studio" if cfg["use_gemini"] else f"project-{cfg['image_type']}",
            "model": cfg["model"],
            "message": str(exc),
        }
        print(json.dumps(err_res, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
