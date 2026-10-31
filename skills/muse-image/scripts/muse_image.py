#!/usr/bin/env python3
"""Generate and edit images through the Muse2API OpenAI-compatible gateway.

Config (mỗi trường gộp riêng): --account-id > .muse/config.json (dùng chung muse-chat)
> biến môi trường (MUSE_ENDPOINT_URL, MUSE_API_KEY, MUSE_ACCOUNT_ID, MUSEAI_IMAGE_*)
> .env. account_id nếu có gửi kèm header X-Account-ID trên các POST /v1/images/*.
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def project_root() -> Path:
    d = Path.cwd().resolve()
    while True:
        if (d / ".git").exists():
            return d
        parent = d.parent
        if parent == d:
            return Path.cwd().resolve()
        d = parent


def load_dotmuse() -> dict[str, Any]:
    """Đọc .muse/config.json ở project root — file dùng chung với muse-chat."""
    path = project_root() / ".muse" / "config.json"
    try:
        cfg = json.loads(path.read_text(encoding="utf-8-sig"))
        return cfg if isinstance(cfg, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def load_config(account_id_flag: str | None = None) -> tuple[str, str, str | None, str, int, float]:
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
    for key in ("MUSE_ENDPOINT_URL", "MUSE_API_KEY", "MUSE_ACCOUNT_ID", "MUSEAI_IMAGE_ENDPOINT_URL", "MUSEAI_IMAGE_API_KEY", "MUSEAI_IMAGE_ACCOUNT_ID", "MUSEAI_IMAGE_MODEL", "MUSEAI_IMAGE_TIMEOUT", "MUSEAI_IMAGE_POLL_INTERVAL"):
        if os.getenv(key):
            values[key] = os.environ[key]

    shared = load_dotmuse()
    # Mỗi trường gộp riêng: .muse/config.json (dùng chung muse-chat) > biến môi trường > .env
    endpoint = (shared.get("endpoint") or values.get("MUSE_ENDPOINT_URL") or values.get("MUSEAI_IMAGE_ENDPOINT_URL") or "").strip().rstrip("/")
    key = (shared.get("api_key") or values.get("MUSE_API_KEY") or values.get("MUSEAI_IMAGE_API_KEY") or "").strip()
    account_id = (account_id_flag or shared.get("account_id") or values.get("MUSE_ACCOUNT_ID") or values.get("MUSEAI_IMAGE_ACCOUNT_ID") or "").strip() or None
    if endpoint:
        if endpoint.endswith("/chat/completions"):
            endpoint = endpoint[:-len("/chat/completions")]
        if not endpoint.endswith("/v1"):
            endpoint += "/v1"
    model = values.get("MUSEAI_IMAGE_MODEL", "muse-image").strip() or "muse-image"
    try:
        timeout = int(values.get("MUSEAI_IMAGE_TIMEOUT", "600"))
    except ValueError as exc:
        raise ValueError("MUSEAI_IMAGE_TIMEOUT phải là số giây nguyên") from exc
    if not endpoint or not key:
        raise ValueError("Thiếu endpoint/API key trong .muse/config.json, .env hoặc biến môi trường (MUSE_ENDPOINT_URL, MUSE_API_KEY)")
    if timeout <= 0:
        raise ValueError("MUSEAI_IMAGE_TIMEOUT phải lớn hơn 0")
    try:
        poll_interval = float(values.get("MUSEAI_IMAGE_POLL_INTERVAL", "2"))
    except ValueError as exc:
        raise ValueError("MUSEAI_IMAGE_POLL_INTERVAL phải là số giây") from exc
    if poll_interval <= 0:
        raise ValueError("MUSEAI_IMAGE_POLL_INTERVAL phải lớn hơn 0")
    return endpoint, key, account_id, model, timeout, poll_interval


def auth_headers(api_key: str, account_id: str | None, extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    if account_id:
        # Pin request vào một account trong pool, tắt failover (header X-Account-ID theo API reference)
        headers["X-Account-ID"] = account_id
    if extra:
        headers.update(extra)
    return headers


def request_json(url: str, api_key: str, timeout: int, payload: dict[str, Any], account_id: str | None = None) -> dict[str, Any]:
    req = urllib.request.Request(
        url, data=json.dumps(payload, ensure_ascii=False).encode(),
        headers=auth_headers(api_key, account_id, {"Content-Type": "application/json"}),
        method="POST",
    )
    return read_json(req, timeout, api_key)


def request_multipart(url: str, api_key: str, timeout: int, fields: list[tuple[str, str]], files: list[tuple[str, Path]], account_id: str | None = None) -> dict[str, Any]:
    boundary = "----MuseImage" + os.urandom(16).hex()
    body = multipart_body(boundary, fields, files)
    req = urllib.request.Request(
        url, data=body,
        headers=auth_headers(api_key, account_id, {"Content-Type": f"multipart/form-data; boundary={boundary}"}),
        method="POST",
    )
    return read_json(req, timeout, api_key)


def data_url(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy ảnh: {path}")
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


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


def request_task(url: str, api_key: str, timeout: int) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"})
    return read_json(req, timeout, api_key)


def poll_task(data: dict[str, Any], endpoint: str, api_key: str, timeout: int, interval: float) -> dict[str, Any]:
    task_id = data.get("id")
    if not task_id:
        raise RuntimeError("Muse2API async response thiếu task id")
    deadline = time.monotonic() + timeout
    last_status = None
    while True:
        status = str(data.get("status", "")).lower()
        if status != last_status:
            print(f"Trạng thái task {task_id}: {status or 'unknown'}", file=sys.stderr)
            last_status = status
        if status in {"succeeded", "completed", "done"}:
            result = data.get("result")
            if not isinstance(result, dict):
                raise RuntimeError("Task hoàn tất nhưng thiếu result")
            return result
        if status in {"failed", "error", "cancelled", "canceled", "interrupted"}:
            raise RuntimeError(f"Task {task_id} thất bại: {data.get('error') or status}")
        if time.monotonic() >= deadline:
            raise RuntimeError(f"Timeout khi poll task {task_id} sau {timeout} giây")
        time.sleep(min(interval, max(0.1, deadline - time.monotonic())))
        task_path = f"{endpoint}/images/tasks/{urllib.parse.quote(str(task_id), safe='')}"
        try:
            data = request_task(task_path, api_key, timeout)
        except RuntimeError as first_error:
            if "HTTP 404" not in str(first_error):
                raise
            data = request_task(f"{endpoint}/images/generations/{urllib.parse.quote(str(task_id), safe='')}", api_key, timeout)


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
        p.add_argument("--async", dest="async_mode", action="store_true", help="Gửi background task rồi poll đến khi hoàn tất")
        p.add_argument("--poll-interval", type=float, help="Khoảng cách giữa các lần poll (giây)")
        p.add_argument("--account-id", help="Pin request vào một account trong pool (header X-Account-ID, tắt failover)")
        p.add_argument("--output", "-o", required=True, type=Path, help="Đường dẫn ảnh kết quả")
        return p

    common("generate", "images/generations", (), prompt_required=True, size_default="1024x1024")
    gen = subs.choices["generate"]
    gen.add_argument("--image", action="append", type=Path, help="Ảnh tham chiếu (data URL/base64 qua JSON, lặp tối đa 4 lần)")
    gen.add_argument("--background", choices=("auto", "opaque", "transparent"), default="auto", help="transparent: cắt chủ thể ra nền trong suốt RGBA")
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
        endpoint, api_key, account_id, default_model, timeout, poll_interval = load_config(args.account_id)
        url = f"{endpoint}/{args.endpoint}"
        model = args.model or default_model
        if args.operation == "generate":
            payload: dict[str, Any] = {"model": model, "prompt": args.prompt, "size": args.size, "n": 1, "response_format": args.response_format, "background": args.background, "async": args.async_mode}
            if args.image:
                if len(args.image) > 4:
                    raise ValueError("Tối đa 4 ảnh tham chiếu cho generate")
                payload["image"] = [data_url(p) for p in args.image]
            data = request_json(url, api_key, timeout, payload, account_id)
        else:
            fields: list[tuple[str, str]] = [("model", model), ("response_format", args.response_format)]
            if args.size:
                fields.append(("size", args.size))
            if args.prompt:
                fields.append(("prompt", args.prompt))
            fields.append(("async", "true" if args.async_mode else "false"))
            files = [(field, getattr(args, option[2:].replace("-", "_"))) for option, field in args.file_specs]
            if args.operation == "remove" and args.mask:
                files.append(("mask", args.mask))
            data = request_multipart(url, api_key, timeout, fields, files, account_id)
        if args.async_mode:
            data = poll_task(data, endpoint, api_key, timeout, args.poll_interval or poll_interval)
        save_result(data, endpoint, api_key, timeout, args.output)
        return 0
    except (ValueError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
