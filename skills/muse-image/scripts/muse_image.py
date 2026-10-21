#!/usr/bin/env python3
"""Generate and edit images through the Muse2API OpenAI-compatible gateway."""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def load_config() -> tuple[str, str, str, int]:
    values: dict[str, str] = {}
    for env_path in (Path.cwd() / ".env", Path(__file__).resolve().parents[3] / ".env"):
        if not env_path.is_file():
            continue
        try:
            for raw in env_path.read_text(encoding="utf-8-sig").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values.setdefault(key.strip(), value.strip().strip("'\""))
        except OSError:
            continue
    for key in ("MUSEAI_IMAGE_ENDPOINT_URL", "MUSEAI_IMAGE_API_KEY", "MUSEAI_IMAGE_MODEL", "MUSEAI_IMAGE_TIMEOUT"):
        if os.getenv(key):
            values[key] = os.environ[key]

    endpoint = values.get("MUSEAI_IMAGE_ENDPOINT_URL", "").strip().rstrip("/")
    key = values.get("MUSEAI_IMAGE_API_KEY", "").strip()
    model = values.get("MUSEAI_IMAGE_MODEL", "muse-image").strip() or "muse-image"
    try:
        timeout = int(values.get("MUSEAI_IMAGE_TIMEOUT", "600"))
    except ValueError as exc:
        raise ValueError("MUSEAI_IMAGE_TIMEOUT phải là số giây nguyên") from exc
    if not endpoint or not key:
        raise ValueError("Thiếu MUSEAI_IMAGE_ENDPOINT_URL hoặc MUSEAI_IMAGE_API_KEY trong .env/biến môi trường")
    if timeout <= 0:
        raise ValueError("MUSEAI_IMAGE_TIMEOUT phải lớn hơn 0")
    return endpoint, key, model, timeout


def request_json(url: str, api_key: str, timeout: int, payload: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        url, data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    return read_json(req, timeout, api_key)


def request_multipart(url: str, api_key: str, timeout: int, fields: list[tuple[str, str]], files: list[tuple[str, Path]]) -> dict[str, Any]:
    boundary = "----MuseImage" + os.urandom(16).hex()
    body = multipart_body(boundary, fields, files)
    req = urllib.request.Request(
        url, data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": f"multipart/form-data; boundary={boundary}", "Accept": "application/json"},
        method="POST",
    )
    return read_json(req, timeout, api_key)


def multipart_body(boundary: str, fields: list[tuple[str, str]], files: list[tuple[str, Path]]) -> bytes:
    chunks: list[bytes] = []
    for name, value in fields:
        chunks.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())
    for name, path in files:
        if not path.is_file():
            raise FileNotFoundError(f"Không tìm thấy ảnh: {path}")
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{path.name}\"\r\nContent-Type: {mime}\r\n\r\n".encode() + path.read_bytes() + b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks)


def read_json(req: urllib.request.Request, timeout: int, api_key: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
            error = parsed.get("error", parsed)
            message = error.get("message", str(error)) if isinstance(error, dict) else str(error)
        except (ValueError, AttributeError):
            message = body[:500]
        raise RuntimeError(f"HTTP {exc.code}: {message}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Không kết nối được tới Muse2API: {exc.reason}") from None
    if not isinstance(payload, dict):
        raise RuntimeError("Muse2API trả về JSON không đúng cấu trúc")
    return payload


def save_result(data: dict[str, Any], endpoint: str, api_key: str, timeout: int, output: Path) -> None:
    items = data.get("data")
    if not isinstance(items, list) or not items or not isinstance(items[0], dict):
        raise RuntimeError("Response không có ảnh trong data[]")
    item = items[0]
    if item.get("b64_json"):
        image_bytes = base64.b64decode(item["b64_json"], validate=True)
    elif item.get("url"):
        image_url = urllib.parse.urljoin(endpoint + "/", str(item["url"]))
        origin = urllib.parse.urlsplit(endpoint)
        target = urllib.parse.urlsplit(image_url)
        headers = {}
        if (target.scheme, target.netloc) == (origin.scheme, origin.netloc):
            headers["Authorization"] = f"Bearer {api_key}"
        req = urllib.request.Request(image_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                image_bytes = response.read()
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise RuntimeError(f"Không tải được ảnh kết quả: {exc}") from None
    else:
        raise RuntimeError("data[0] không có url hoặc b64_json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image_bytes)
    print(f"Đã lưu ảnh: {output.resolve()} ({len(image_bytes)} bytes)")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Tạo/chỉnh sửa ảnh qua Muse2API")
    subs = root.add_subparsers(dest="operation", required=True)

    def common(name: str, endpoint: str, file_specs: tuple[tuple[str, str], ...], prompt_required: bool = False, size_default: str | None = None) -> argparse.ArgumentParser:
        p = subs.add_parser(name)
        p.set_defaults(endpoint=endpoint, file_specs=file_specs)
        for option, field in file_specs:
            p.add_argument(option, required=True, type=Path, help=f"Ảnh gửi dưới trường {field}")
        if file_specs or prompt_required:
            p.add_argument("--prompt", required=prompt_required, help="Hướng dẫn chỉnh sửa")
        p.add_argument("--model", help="Ghi đè model (mặc định muse-image)")
        p.add_argument("--size", default=size_default, help="Kích thước yêu cầu, ví dụ 1024x1024")
        p.add_argument("--response-format", choices=("url", "b64_json"), default="url")
        p.add_argument("--output", "-o", required=True, type=Path, help="Đường dẫn ảnh kết quả")
        return p

    common("generate", "images/generations", (), prompt_required=True, size_default="1024x1024")
    common("edit", "images/edits", (("--image", "image"),), True)
    common("extract", "images/outfits/extract", (("--image", "image"),))
    common("try-on", "images/outfits/try-on", (("--character", "character"), ("--outfit", "outfit")))
    common("remove", "images/objects/remove", (("--image", "image"),))
    p = common("accessory", "images/accessories/add", (("--image", "image"), ("--accessory", "accessory")))
    p = common("background", "images/background/replace", (("--image", "image"), ("--background-image", "background_image")))
    p = subs.choices["remove"]
    p.add_argument("--mask", type=Path, help="Mask PNG đen/trắng tùy chọn")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        endpoint, api_key, default_model, timeout = load_config()
        url = f"{endpoint}/{args.endpoint}"
        model = args.model or default_model
        if args.operation == "generate":
            payload: dict[str, Any] = {"model": model, "prompt": args.prompt, "size": args.size, "n": 1, "response_format": args.response_format, "background": "auto"}
            data = request_json(url, api_key, timeout, payload)
        else:
            fields: list[tuple[str, str]] = [("model", model), ("response_format", args.response_format)]
            if args.size:
                fields.append(("size", args.size))
            if args.prompt:
                fields.append(("prompt", args.prompt))
            files = [(field, getattr(args, option[2:].replace("-", "_"))) for option, field in args.file_specs]
            if args.operation == "remove" and args.mask:
                files.append(("mask", args.mask))
            data = request_multipart(url, api_key, timeout, fields, files)
        save_result(data, endpoint, api_key, timeout, args.output)
        return 0
    except (ValueError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
