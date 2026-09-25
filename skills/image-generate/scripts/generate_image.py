#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_image.py

Script tạo ảnh độc lập chuẩn OpenAI Compatibility (/v1/images/generations).
Thuộc skill: .agents/skills/image-generate/

Đặc tính kỹ thuật:
- Thuần Python 100% (Pure Python, Zero dependencies) - không yêu cầu cài đặt package ngoài.
- Tự động nạp cấu hình AI_IMAGE_API_KEY, AI_IMAGE_ENDPOINT_URL, AI_IMAGE_MODEL từ file .env.
- Mặc định tỷ lệ dọc 9:16 (1024x1792) tối ưu cho Shorts, TikTok, Reels.
- Hỗ trợ cả nhận base64 (b64_json) và tải link URL trực tiếp.
- Hỗ trợ truyền ảnh tham chiếu (--ref-image) cho tác vụ Image-to-Image / giữ nét KOC.
- Trả về kết quả chuẩn JSON kèm đường dẫn file và dung lượng thực tế.
"""
from __future__ import annotations

import argparse
import base64
import datetime
import json
import mimetypes
import os
import secrets
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Bản đồ ánh xạ tỷ lệ khung hình sang kích thước pixel chuẩn
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
DEFAULT_TIMEOUT = 180


def load_candidate_env() -> Dict[str, str]:
    """Tìm và nạp biến môi trường từ các file .env ứng viên."""
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

    for k in ("AI_IMAGE_API_KEY", "AI_IMAGE_ENDPOINT_URL", "AI_IMAGE_MODEL", "AI_IMAGE_USE_GEMINI"):
        val = os.getenv(k, "")
        if val:
            env_vars[k] = val
    return env_vars


def resolve_config(
    cli_key: Optional[str] = None,
    cli_endpoint: Optional[str] = None,
    cli_model: Optional[str] = None,
    cli_use_gemini: bool = False,
) -> Dict[str, Any]:
    """Xác định cấu hình API key, endpoint và model sinh ảnh."""
    env = load_candidate_env()

    # 1. API Key: Chỉ nhận AI_IMAGE_API_KEY
    api_key = (
        cli_key
        or env.get("AI_IMAGE_API_KEY", "")
    ).strip()

    # 2. Endpoint URL
    endpoint_url = (
        cli_endpoint
        or env.get("AI_IMAGE_ENDPOINT_URL", "")
    ).strip()

    # Chuẩn hóa endpoint nếu người dùng chỉ truyền base URL
    if endpoint_url and (endpoint_url.endswith("/v1") or endpoint_url.endswith("/v1/")):
        endpoint_url = endpoint_url.rstrip("/") + "/images/generations"

    # 3. Model
    raw_models = env.get("AI_IMAGE_MODEL", "")
    env_model = raw_models.split(",")[0].strip() if raw_models else None
    model = (cli_model or env_model)
    if model:
        model = model.strip()
    else:
        raise RuntimeError("Vui lòng cấu hình AI_IMAGE_MODEL trong .env hoặc truyền tham số --model")
        
    # 4. Use Gemini
    use_gemini_env = str(env.get("AI_IMAGE_USE_GEMINI", "false")).strip().lower() in ("true", "1", "yes")
    use_gemini = cli_use_gemini or use_gemini_env
    
    if not use_gemini and not endpoint_url:
        raise RuntimeError("Vui lòng cấu hình AI_IMAGE_ENDPOINT_URL cho chế độ Gateway")

    return {
        "api_key": api_key,
        "endpoint_url": endpoint_url,
        "model": model,
        "use_gemini": use_gemini,
    }


def encode_image_to_data_uri(image_path: Path) -> str:
    """Mã hóa ảnh địa phương sang chuỗi Base64 Data URI."""
    if not image_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy ảnh tham chiếu: {image_path}")

    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type:
        mime_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"

    data_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{data_b64}"


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
            "outputMimeType": "image/png"
        }
    }
    
    req_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": f"image-generator/{secrets.token_hex(8)}",
        },
        method="POST",
    )

    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            resp_bytes = resp.read()
            data = json.loads(resp_bytes.decode("utf-8"))
    except urllib.error.HTTPError as err:
        err_msg = err.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP Error {err.code}: {err_msg}")
    except Exception as exc:
        raise RuntimeError(f"Không thể kết nối đến Gemini API: {exc}")

    predictions = data.get("predictions", [])
    if not predictions:
        raise RuntimeError(f"API không trả về ảnh nào: {data}")

    b64_img = predictions[0].get("bytesBase64Encoded")
    if not b64_img:
        raise RuntimeError(f"Dữ liệu ảnh trả về không hợp lệ: {predictions[0]}")
        
    image_bytes = base64.b64decode(b64_img)
    return image_bytes, "image/png", prompt


def call_openai_image_api(
    prompt: str,
    api_key: str,
    endpoint_url: str,
    model: str,
    size: str = DEFAULT_SIZE,
    quality: str = "standard",
    ref_image_path: Optional[Path] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Tuple[bytes, str, str]:
    """Gọi API sinh ảnh chuẩn OpenAI Compatibility.
    
    Returns:
        (image_bytes, mime_type, revised_prompt)
    """
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "response_format": "b64_json",
        "n": 1,
    }

    # Nếu có ảnh tham chiếu (Image-to-Image / Style reference)
    if ref_image_path:
        data_uri = encode_image_to_data_uri(ref_image_path)
        payload["image"] = data_uri
        payload["input_references"] = [data_uri]

    req_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        endpoint_url,
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": f"image-generator/{secrets.token_hex(8)}",
        },
        method="POST",
    )

    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            resp_bytes = resp.read()
            data = json.loads(resp_bytes.decode("utf-8"))
    except urllib.error.HTTPError as err:
        err_msg = err.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP Error {err.code}: {err_msg}")
    except Exception as exc:
        raise RuntimeError(f"Không thể kết nối đến Image API: {exc}")

    items = data.get("data", [])
    if not items:
        raise RuntimeError(f"API không trả về ảnh nào: {data}")

    first_item = items[0]
    revised_prompt = first_item.get("revised_prompt", prompt)

    # 1. Trích xuất nếu trả về dạng b64_json
    if "b64_json" in first_item and first_item["b64_json"]:
        image_bytes = base64.b64decode(first_item["b64_json"])
        # Nhận diện magic number ảnh
        if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            mime = "image/png"
        elif image_bytes.startswith(b"\xff\xd8\xff"):
            mime = "image/jpeg"
        elif image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[:16]:
            mime = "image/webp"
        else:
            mime = "image/png"
        return image_bytes, mime, revised_prompt

    # 2. Tải về nếu trả về dạng URL
    if "url" in first_item and first_item["url"]:
        img_url = first_item["url"]
        dl_req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(dl_req, context=ctx, timeout=60) as dl_resp:
            image_bytes = dl_resp.read()
            mime = dl_resp.headers.get("Content-Type", "image/png").split(";")[0].strip()
            return image_bytes, mime, revised_prompt

    raise RuntimeError(f"Dữ liệu ảnh trả về không hợp lệ: {first_item}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OpenAI-Compatible & Gemini Image Generator CLI (Zero Dependencies)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--prompt", "-p", type=str, help="Câu lệnh prompt mô tả ảnh cần tạo")
    parser.add_argument("--prompt-file", type=str, help="Đường dẫn file .txt chứa prompt chi tiết")
    parser.add_argument(
        "--aspect-ratio",
        type=str,
        choices=list(ASPECT_RATIO_MAP.keys()),
        default=None,
        help="Tỷ lệ khung hình (bắt buộc, VD: 9:16)",
    )
    parser.add_argument(
        "--size",
        type=str,
        default=None,
        help="Kích thước pixel cụ thể (VD: 1024x1792, 1024x1024). Bắt buộc nếu không có --aspect-ratio",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=None,
        help="Tên model sinh ảnh (mặc định lấy từ AI_IMAGE_MODEL trong .env)",
    )
    parser.add_argument(
        "--ref-image",
        "-i",
        type=str,
        default=None,
        help="Đường dẫn ảnh tham chiếu (chân dung KOC hoặc chi tiết sản phẩm) cho tác vụ Image-to-Image",
    )
    parser.add_argument(
        "--quality",
        type=str,
        choices=["standard", "hd", "auto"],
        default=None,
        help="Chất lượng ảnh (bắt buộc)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Đường dẫn file ảnh đầu ra (mặc định: output_image.png)",
    )
    parser.add_argument(
        "--session-dir",
        type=str,
        default=None,
        help="Thư mục session lưu kết quả (tự động tạo thư mục output/ bên trong)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API Key thủ công (mặc định đọc AI_IMAGE_API_KEY từ .env)",
    )
    parser.add_argument(
        "--endpoint-url",
        type=str,
        default=None,
        help="Endpoint URL thủ công (mặc định đọc AI_IMAGE_ENDPOINT_URL từ .env)",
    )
    parser.add_argument(
        "--use-gemini",
        action="store_true",
        help="Sử dụng trực tiếp Google AI Studio API",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Kiểm tra cấu hình và in payload mà không gọi API",
    )

    args = parser.parse_args()

    # 0. Validate required args
    if not args.aspect_ratio and not args.size:
        print(json.dumps({"status": "error", "message": "Vui lòng cung cấp tham số --aspect-ratio hoặc --size"}, ensure_ascii=False))
        sys.exit(1)
    if not args.quality:
        print(json.dumps({"status": "error", "message": "Vui lòng cung cấp tham số --quality"}, ensure_ascii=False))
        sys.exit(1)

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
        print(
            json.dumps(
                {"status": "error", "message": "Vui lòng cung cấp prompt qua --prompt hoặc --prompt-file"},
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    # 2. Xác định kích thước ảnh
    final_size = args.size or ASPECT_RATIO_MAP.get(args.aspect_ratio, DEFAULT_SIZE)

    # 3. Nạp cấu hình
    try:
        cfg = resolve_config(cli_key=args.api_key, cli_endpoint=args.endpoint_url, cli_model=args.model, cli_use_gemini=args.use_gemini)
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False))
        sys.exit(1)

    ref_path = Path(args.ref_image).resolve() if args.ref_image else None
    if ref_path and not ref_path.is_file():
        print(json.dumps({"status": "error", "message": f"Ảnh tham chiếu không tồn tại: {ref_path}"}, ensure_ascii=False))
        sys.exit(1)

    # 4. Xử lý Dry Run
    if args.dry_run:
        dry_info = {
            "status": "dry_run",
            "mode": "Google Direct" if cfg["use_gemini"] else "Gateway",
            "endpoint_url": f"https://generativelanguage.googleapis.com/v1beta/models/{cfg['model']}:predict" if cfg["use_gemini"] else cfg["endpoint_url"],
            "model": cfg["model"],
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
            "message": (
                "Không tìm thấy API Key cho Image Generation. "
                "Vui lòng cấu hình AI_IMAGE_API_KEY trong file .env hoặc truyền qua tham số --api-key."
            ),
        }
        print(json.dumps(err_response, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 6. Xác định file đầu ra
    if args.output:
        out_file = Path(args.output).resolve()
    else:
        if args.session_dir:
            session_dir = Path(args.session_dir).resolve()
        else:
            today_str = datetime.datetime.now().strftime("%Y%m%d")
            session_dir = Path.cwd() / "scratch" / f"{today_str}_image-generate_default"
        out_file = session_dir / "output" / "visual.png"

    out_file.parent.mkdir(parents=True, exist_ok=True)

    # 7. Gọi API sinh ảnh
    try:
        if cfg["use_gemini"]:
            image_bytes, mime, revised_prompt = call_gemini_image_api(
                prompt=prompt_text,
                api_key=cfg["api_key"],
                model=cfg["model"],
                aspect_ratio=args.aspect_ratio or DEFAULT_ASPECT_RATIO,
            )
        else:
            image_bytes, mime, revised_prompt = call_openai_image_api(
                prompt=prompt_text,
                api_key=cfg["api_key"],
                endpoint_url=cfg["endpoint_url"],
                model=cfg["model"],
                size=final_size,
                quality=args.quality,
                ref_image_path=ref_path,
            )

        out_file.write_bytes(image_bytes)

        result = {
            "status": "success",
            "engine": "google-ai-studio" if cfg["use_gemini"] else "openai-compatible",
            "model": cfg["model"],
            "aspect_ratio": args.aspect_ratio,
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
            "engine": "google-ai-studio" if cfg["use_gemini"] else "openai-compatible",
            "model": cfg["model"],
            "message": str(exc),
        }
        print(json.dumps(err_res, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
