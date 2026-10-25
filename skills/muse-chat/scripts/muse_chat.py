#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chat với Muse qua gateway Muse2API cục bộ. Chỉ dùng thư viện chuẩn Python.

Thứ tự tự tìm cấu hình (giá trị tìm thấy trước thắng, các trường gộp dần):
  1. <project>/.muse/config.json (xem config.example.json)
  2. Biến môi trường máy: MUSE_ENDPOINT_URL, MUSE_API_KEY
  3. Vẫn thiếu mới hỏi người dùng (agent làm bước này, rồi lưu bằng config set)
Endpoint chấp nhận URL gốc (.../v1) hoặc URL đầy đủ (.../v1/chat/completions).
account_id do người dùng tự cung cấp (lưu qua config set); model cố định muse-chat.

Lệnh:
  muse_chat.py config set --endpoint URL --api-key KEY [--account-id ID] [--model NAME]
  muse_chat.py config show
  muse_chat.py ask (--text "..." | --file F) [--topic chat] [--new-thread] [--out F] [--timeout S]

Mã thoát: 0 OK; 2 chưa cấu hình; 3 lỗi HTTP; 4 lỗi kết nối; 5 reply rỗng.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

DEFAULT_MODEL = "muse-chat"
DEFAULT_TIMEOUT = 600
THREAD_RE = re.compile(r"muse\.ai/thread/([0-9a-fA-F]{8}-[0-9a-fA-F-]{27})")


def project_root():
    d = os.path.abspath(os.getcwd())
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.path.abspath(os.getcwd())
        d = parent


def config_path():
    return os.path.join(project_root(), ".muse", "config.json")


def load_config():
    path = config_path()
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                cfg = json.load(f)
            if isinstance(cfg, dict):
                return cfg
        except (OSError, json.JSONDecodeError):
            pass
    return {}


ENV_VARS = {
    "endpoint": "MUSE_ENDPOINT_URL",
    "api_key": "MUSE_API_KEY",
}


def normalize_endpoint(url):
    """Chuẩn hoá endpoint: chấp nhận cả URL gốc lẫn URL đầy đủ."""
    url = url.strip().rstrip("/")
    if not url:
        return url
    if url.endswith("/chat/completions"):
        return url
    if url.endswith("/v1"):
        return url + "/chat/completions"
    return url + "/v1/chat/completions"


def resolve_config():
    """Gộp .muse/config.json với biến môi trường; file thắng env từng trường.

    Trả về (cfg, sources) với sources[field] = "file" | "env:TÊN_BIẾN" | "missing".
    """
    cfg = load_config()
    sources = {}
    for field, var in ENV_VARS.items():
        if cfg.get(field):
            sources[field] = "file"
        else:
            env_val = os.environ.get(var, "").strip()
            if env_val:
                cfg[field] = env_val
                sources[field] = "env:" + var
            else:
                sources[field] = "missing"
    if cfg.get("endpoint"):
        cfg["endpoint"] = normalize_endpoint(cfg["endpoint"])
    return cfg, sources


def save_config(cfg):
    path = config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")


def mask(secret):
    if not secret:
        return "(chưa đặt)"
    return secret[:6] + "…" + secret[-4:] if len(secret) > 12 else "***"


def next_number(topic_dir):
    n = 0
    if os.path.isdir(topic_dir):
        for name in os.listdir(topic_dir):
            m = re.match(r"msg_(\d+)\.json$", name)
            if m:
                n = max(n, int(m.group(1)))
    return n + 1


def dedupe_replays(text):
    """Stream của gateway này hay replay nguyên bản tin nhắn nhiều lần liền.
    Lấy từ lần xuất HIỆN LẠI (last occurrence) của cụm mở đầu đến hết text."""
    if len(text) < 300:
        return text
    opening = text[:60]
    idx = text.rfind(opening)
    if 0 < idx and (len(text) - idx) >= max(200, int(len(text) * 0.15)):
        return text[idx:]
    return text


def build_message(args):
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            return f.read().strip()
    return args.text.strip()


def send(cfg, payload, timeout):
    """Gửi request stream:true, trả về (text_gộp_từ_delta, raw_response)."""
    headers = {
        "Authorization": "Bearer " + cfg["api_key"],
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "text/event-stream",
    }
    if cfg.get("account_id"):
        headers["X-Account-ID"] = cfg["account_id"]
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(cfg["endpoint"], data=body, headers=headers, method="POST")
    raw_parts, deltas = [], []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw_line in resp:
                raw_parts.append(raw_line)
                line = raw_line.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    continue
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = obj.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                piece = delta.get("content") or (choices[0].get("message") or {}).get("content") or ""
                if piece:
                    deltas.append(piece)
    except urllib.error.HTTPError as e:
        excerpt = ""
        try:
            excerpt = e.read().decode("utf-8", "replace")[:800]
        except Exception:
            pass
        print(f"[lỗi] HTTP {e.code} từ gateway. {excerpt}", file=sys.stderr)
        sys.exit(3)
    except urllib.error.URLError as e:
        print(f"[lỗi] Không kết nối được gateway ({e.reason}). Endpoint đúng chưa, gateway có đang chạy không?", file=sys.stderr)
        sys.exit(4)

    raw = b"".join(raw_parts).decode("utf-8", "replace")
    text = "".join(deltas)
    if not text:
        # phòng khi gateway trả JSON thường thay vì SSE
        try:
            obj = json.loads(raw)
            text = (obj.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        except json.JSONDecodeError:
            pass
    return text, raw


def _src_label(sources, field):
    s = sources.get(field)
    if s and s.startswith("env:"):
        return f"  [biến môi trường {s[4:]}]"
    if s == "file":
        return "  [file config]"
    return ""


def cmd_config_set(args):
    cfg = load_config()
    if args.endpoint:
        cfg["endpoint"] = normalize_endpoint(args.endpoint)
    if args.api_key:
        cfg["api_key"] = args.api_key.strip()
    if args.account_id:
        cfg["account_id"] = args.account_id.strip()
    missing = [k for k in ("endpoint", "api_key") if not cfg.get(k)]
    if missing:
        print(f"[lỗi] Vẫn thiếu: {', '.join(missing)}. Chạy lại config set với các giá trị còn thiếu.", file=sys.stderr)
        sys.exit(2)
    save_config(cfg)
    print(f"[ok] Đã lưu {config_path()}")
    print(f"  endpoint   : {cfg['endpoint']}")
    print(f"  api_key    : {mask(cfg.get('api_key'))}")
    print(f"  account_id : {cfg.get('account_id', '(không có)')}")
    print(f"  thread     : {cfg.get('thread', '(chưa có — lượt ask đầu sẽ tự tạo)')}")
    print("  (thread hiện có được giữ nguyên khi đổi cấu hình)")


def cmd_config_show(_args):
    cfg, sources = resolve_config()
    path = config_path()
    has_file = os.path.exists(path)
    if not has_file and not any(k in cfg for k in ENV_VARS):
        print(f"[chưa cấu hình] Không có {path} và không tìm thấy biến môi trường "
              f"{ENV_VARS['endpoint']} / {ENV_VARS['api_key']}. "
              "Hỏi người dùng API endpoint + API key rồi chạy lệnh config set.", file=sys.stderr)
        sys.exit(2)
    print(f"file    : {path} ({'có' if has_file else 'chưa có'})")
    print(f"endpoint: {cfg.get('endpoint', '(thiếu)')}{_src_label(sources, 'endpoint')}")
    print(f"api_key : {mask(cfg.get('api_key'))}{_src_label(sources, 'api_key')}")
    print(f"account : {cfg.get('account_id', '(không có)')}")
    print(f"thread  : {cfg.get('thread', '(chưa có)')}")
    missing = [k for k in ("endpoint", "api_key") if not cfg.get(k)]
    if missing:
        print(f"[thiếu] {', '.join(missing)} — hỏi người dùng rồi chạy config set.", file=sys.stderr)
        sys.exit(2)


def cmd_ask(args):
    cfg, _sources = resolve_config()
    missing = [k for k in ("endpoint", "api_key") if not cfg.get(k)]
    if missing:
        print(f"[chưa cấu hình] Không tìm thấy {', '.join(missing)} trong .muse/config.json "
              f"lẫn biến môi trường ({ENV_VARS['endpoint']}, {ENV_VARS['api_key']}). "
              "Hỏi người dùng API endpoint + API key rồi chạy lệnh config set.", file=sys.stderr)
        sys.exit(2)

    text = build_message(args)
    if not text:
        print("[lỗi] Tin nhắn rỗng.", file=sys.stderr)
        sys.exit(2)

    topic_dir = os.path.join(project_root(), ".scratch", "muse", args.topic)
    os.makedirs(topic_dir, exist_ok=True)
    n = next_number(topic_dir)
    thread = None if args.new_thread else cfg.get("thread")
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": text}],
        "stream": True,
        "thread": thread,
    }
    msg_path = os.path.join(topic_dir, f"msg_{n:02d}.json")
    with open(msg_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    reply, raw = send(cfg, payload, args.timeout)

    raw_path = os.path.join(topic_dir, f"reply_{n:02d}.raw")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(raw)
    reply = dedupe_replays(reply)
    reply_path = os.path.join(topic_dir, f"reply_{n:02d}.txt")
    with open(reply_path, "w", encoding="utf-8") as f:
        f.write(reply)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(reply)

    m = THREAD_RE.findall(raw)
    if m and cfg.get("thread") != (url := f"https://muse.ai/thread/{m[-1]}"):
        cfg["thread"] = url
        save_config(cfg)

    print(f"[thread] {cfg.get('thread', '(không thấy thread mới trong response)')}")
    print(f"[saved]  {msg_path}")
    print(f"[saved]  {reply_path}" + (f" và {args.out}" if args.out else ""))
    if not reply:
        print("[lỗi] Reply rỗng — xem reply .raw để chẩn đoán.", file=sys.stderr)
        sys.exit(5)
    if len(reply) < 120:
        print("[cảnh báo] Reply ngắn bất thường — có thể là stub 1 dòng của Muse; gửi một tin nhắc ngắn để lấy bản đầy đủ.")
    print("[reply]")
    print(reply)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_cfg = sub.add_parser("config", help="quản lý .muse/config.json")
    cfg_sub = p_cfg.add_subparsers(dest="cfg_cmd", required=True)

    p_set = cfg_sub.add_parser("set", help="lưu endpoint/API key vào .muse/config.json")
    p_set.add_argument("--endpoint")
    p_set.add_argument("--api-key")
    p_set.add_argument("--account-id")
    p_set.set_defaults(func=cmd_config_set)

    p_show = cfg_sub.add_parser("show", help="xem cấu hình (key bị che)")
    p_show.set_defaults(func=cmd_config_show)

    p_ask = sub.add_parser("ask", help="gửi một tin user cho Muse và in trả lời")
    p_ask.add_argument("--text")
    p_ask.add_argument("--file", help="file UTF-8 chứa tin nhắn (ưu tiên cho tin dài/tiếng Việt)")
    p_ask.add_argument("--topic", default="chat", help="thư mục transcript con dưới .scratch/muse/ (mặc định: chat)")
    p_ask.add_argument("--new-thread", action="store_true", help="mở thread mới thay vì dùng thread trong config")
    p_ask.add_argument("--out", help="file bổ sung để ghi reply sạch")
    p_ask.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    p_ask.set_defaults(func=cmd_ask)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
