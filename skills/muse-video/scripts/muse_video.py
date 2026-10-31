#!/usr/bin/env python3
"""Create text-to-video / image-to-video tasks through the Muse2API gateway.

Config (mỗi trường gộp riêng): --account-id > .muse/config.json (dùng chung
muse-chat/muse-image) > biến môi trường (MUSE_ENDPOINT_URL, MUSE_API_KEY,
MUSE_ACCOUNT_ID, MUSEAI_VIDEO_*) > .env. account_id nếu có gửi kèm header
X-Account-ID trên POST /v1/videos. Video luôn chạy bất đồng bộ: POST /v1/videos
trả task, poll GET /v1/videos/{task_id} đến khi succeeded rồi tải result.url.

Lệnh:
  muse_video.py create --prompt "..." [--image PATH|URL] [--size 16:9]
                       [--duration 5] [--model muse-video] [--account-id ID]
                       [--poll-interval S] --output out.mp4
  muse_video.py status TASK_ID [--output out.mp4]   # xem task; succeeded + --output thì tải

Mã thoát: 0 OK; 1 lỗi cấu hình/chạy.
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

TERMINAL_OK = {"succeeded", "completed", "done"}
TERMINAL_FAIL = {"failed", "error", "cancelled", "canceled", "interrupted"}


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
    """Đọc .muse/config.json ở project root — file dùng chung với muse-chat/muse-image."""
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
    for key in ("MUSE_ENDPOINT_URL", "MUSE_API_KEY", "MUSE_ACCOUNT_ID", "MUSEAI_VIDEO_ENDPOINT_URL", "MUSEAI_VIDEO_API_KEY", "MUSEAI_VIDEO_ACCOUNT_ID", "MUSEAI_VIDEO_MODEL", "MUSEAI_VIDEO_TIMEOUT", "MUSEAI_VIDEO_POLL_INTERVAL"):
        if os.getenv(key):
            values[key] = os.environ[key]

    shared = load_dotmuse()
    # Mỗi trường gộp riêng: .muse/config.json (dùng chung muse-chat/muse-image) > biến môi trường > .env
    endpoint = (shared.get("endpoint") or values.get("MUSE_ENDPOINT_URL") or values.get("MUSEAI_VIDEO_ENDPOINT_URL") or "").strip().rstrip("/")
    key = (shared.get("api_key") or values.get("MUSE_API_KEY") or values.get("MUSEAI_VIDEO_API_KEY") or "").strip()
    account_id = (account_id_flag or shared.get("account_id") or values.get("MUSE_ACCOUNT_ID") or values.get("MUSEAI_VIDEO_ACCOUNT_ID") or "").strip() or None
    if endpoint:
        if endpoint.endswith("/chat/completions"):
            endpoint = endpoint[:-len("/chat/completions")]
        if not endpoint.endswith("/v1"):
            endpoint += "/v1"
    model = values.get("MUSEAI_VIDEO_MODEL", "muse-video").strip() or "muse-video"
    try:
        timeout = int(values.get("MUSEAI_VIDEO_TIMEOUT", "900"))
    except ValueError as exc:
        raise ValueError("MUSEAI_VIDEO_TIMEOUT phải là số giây nguyên") from exc
    if not endpoint or not key:
        raise ValueError("Thiếu endpoint/API key trong .muse/config.json, .env hoặc biến môi trường (MUSE_ENDPOINT_URL, MUSE_API_KEY)")
    if timeout <= 0:
        raise ValueError("MUSEAI_VIDEO_TIMEOUT phải lớn hơn 0")
    try:
        poll_interval = float(values.get("MUSEAI_VIDEO_POLL_INTERVAL", "5"))
    except ValueError as exc:
        raise ValueError("MUSEAI_VIDEO_POLL_INTERVAL phải là số giây") from exc
    if poll_interval <= 0:
        raise ValueError("MUSEAI_VIDEO_POLL_INTERVAL phải lớn hơn 0")
    return endpoint, key, account_id, model, timeout, poll_interval


def auth_headers(api_key: str, account_id: str | None, extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    if account_id:
        # Pin request vào một account trong pool, tắt failover (header X-Account-ID theo API reference)
        headers["X-Account-ID"] = account_id
    if extra:
        headers.update(extra)
    return headers


def request_json(url: str, api_key: str, timeout: int, payload: dict[str, Any], account_id: str | None = None, method: str = "POST") -> dict[str, Any]:
    req = urllib.request.Request(
        url, data=json.dumps(payload, ensure_ascii=False).encode(),
        headers=auth_headers(api_key, account_id, {"Content-Type": "application/json"}),
        method=method,
    )
    return read_json(req, timeout, api_key)


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


def first_frame(value: str) -> str:
    """--image nhận http(s) URL (gửi nguyên) hoặc đường dẫn file (đổi thành data URL)."""
    if urllib.parse.urlsplit(value).scheme in {"http", "https"}:
        return value
    path = Path(value)
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy ảnh first-frame: {path}")
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def request_task(endpoint: str, task_id: str, api_key: str, timeout: int) -> dict[str, Any]:
    url = f"{endpoint}/videos/{urllib.parse.quote(task_id, safe='')}"
    req = urllib.request.Request(url, headers=auth_headers(api_key, None))
    return read_json(req, timeout, api_key)


def poll_task(data: dict[str, Any], endpoint: str, api_key: str, timeout: int, interval: float) -> dict[str, Any]:
    task_id = data.get("id")
    if not task_id:
        raise RuntimeError("Muse2API video response thiếu task id")
    deadline = time.monotonic() + timeout
    last_status = None
    while True:
        status = str(data.get("status", "")).lower()
        if status != last_status:
            print(f"Trạng thái task {task_id}: {status or 'unknown'}", file=sys.stderr)
            last_status = status
        if status in TERMINAL_OK:
            result = data.get("result")
            if not isinstance(result, dict):
                raise RuntimeError("Task hoàn tất nhưng thiếu result")
            return result
        if status in TERMINAL_FAIL:
            raise RuntimeError(f"Task {task_id} thất bại: {data.get('error') or status}")
        if time.monotonic() >= deadline:
            raise RuntimeError(f"Timeout khi poll task {task_id} sau {timeout} giây — kiểm tra lại bằng lệnh status")
        time.sleep(min(interval, max(0.1, deadline - time.monotonic())))
        data = request_task(endpoint, str(task_id), api_key, timeout)


def download_result(result: dict[str, Any], endpoint: str, api_key: str, timeout: int, output: Path) -> None:
    video_url = result.get("url")
    if video_url:
        image_url = urllib.parse.urljoin(endpoint + "/", str(video_url))
        origin = urllib.parse.urlsplit(endpoint)
        target = urllib.parse.urlsplit(image_url)
        headers = {}
        if (target.scheme, target.netloc) == (origin.scheme, origin.netloc):
            headers["Authorization"] = f"Bearer {api_key}"
        req = urllib.request.Request(image_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                video_bytes = response.read()
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise RuntimeError(f"Không tải được video kết quả: {exc}") from None
    else:
        items = result.get("data")
        if isinstance(items, list) and items and isinstance(items[0], dict) and items[0].get("b64_json"):
            video_bytes = base64.b64decode(items[0]["b64_json"], validate=True)
        else:
            raise RuntimeError("result không có url để tải video")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(video_bytes)
    print(f"Đã lưu video: {output.resolve()} ({len(video_bytes)} bytes)")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Tạo video qua Muse2API (luôn chạy async, poll đến khi xong)")
    subs = root.add_subparsers(dest="operation", required=True)

    p_create = subs.add_parser("create", help="Gửi task tạo video rồi poll đến khi hoàn tất")
    p_create.add_argument("--prompt", required=True, help="Mô tả video cần tạo")
    p_create.add_argument("--image", help="Ảnh first-frame: http(s) URL hoặc đường dẫn file local")
    p_create.add_argument("--size", help="Tỷ lệ khung hình, ví dụ 16:9 hoặc 9:16 (chỉ là gợi ý)")
    p_create.add_argument("--duration", type=int, help="Độ dài video tính giây (1-60)")
    p_create.add_argument("--model", help="Ghi đè model (mặc định muse-video)")
    p_create.add_argument("--account-id", help="Pin request vào một account trong pool (header X-Account-ID, tắt failover)")
    p_create.add_argument("--poll-interval", type=float, help="Khoảng cách giữa các lần poll (giây)")
    p_create.add_argument("--output", "-o", required=True, type=Path, help="Đường dẫn file video kết quả (mp4)")

    p_status = subs.add_parser("status", help="Xem trạng thái task video")
    p_status.add_argument("task_id", help="Task id trả về từ create")
    p_status.add_argument("--output", "-o", type=Path, help="Nếu task succeeded: tải video vào đường dẫn này")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        endpoint, api_key, account_id, default_model, timeout, poll_interval = load_config(getattr(args, "account_id", None))
        if args.operation == "create":
            if args.duration is not None and not 1 <= args.duration <= 60:
                raise ValueError("--duration phải trong khoảng 1-60 giây")
            payload: dict[str, Any] = {"model": args.model or default_model, "prompt": args.prompt}
            if args.size:
                payload["size"] = args.size
            if args.duration is not None:
                payload["duration"] = args.duration
            if args.image:
                payload["image"] = first_frame(args.image)
            url = f"{endpoint}/videos"
            data = request_json(url, api_key, timeout, payload, account_id)
            result = poll_task(data, endpoint, api_key, timeout, args.poll_interval or poll_interval)
            download_result(result, endpoint, api_key, timeout, args.output)
        else:
            data = request_task(endpoint, args.task_id, api_key, timeout)
            status = str(data.get("status", "unknown"))
            print(f"Task {args.task_id}: {status}")
            result = data.get("result")
            if isinstance(result, dict) and result.get("url"):
                print(f"Kết quả: {urllib.parse.urljoin(endpoint + '/', str(result['url']))}")
            if status.lower() in TERMINAL_OK and args.output:
                if not isinstance(result, dict):
                    raise RuntimeError("Task hoàn tất nhưng thiếu result")
                download_result(result, endpoint, api_key, timeout, args.output)
            elif status.lower() in TERMINAL_FAIL:
                raise RuntimeError(f"Task thất bại: {data.get('error') or status}")
        return 0
    except (ValueError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
