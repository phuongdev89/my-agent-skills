#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_vbee_voice.py

Script tạo giọng đọc tiếng Việt qua Cloud API của Vbee AIVoice (vbee.vn).
Thuộc skill: .agents/skills/vbee-tts/

Hỗ trợ:
- Đọc văn bản bằng các giọng Vbee chất lượng cao (Thu Trang, Ngọc Huyền, Mai Phương, Mạnh Dũng...)
- Tự động nạp biến môi trường VBEE_APP_ID và VBEE_ACCESS_TOKEN từ file .env
- Hỗ trợ alias tên giọng ngắn gọn hoặc mã voice code đầy đủ
- Tải file âm thanh về và đo thời lượng thực tế chính xác (duration_seconds)
- Xuất kết quả chuẩn JSON.

Cách dùng:
  # 1. Đọc văn bản bằng giọng Thu Trang (KOC):
  python generate_vbee_voice.py --text "Chào bạn! Đây là giọng đọc Thu Trang của Vbee." --voice "thutrang" --output output.mp3

  # 2. Đọc từ file kịch bản:
  python generate_vbee_voice.py --text-file "script.txt" --voice "ngochuyen" --output output.mp3

  # 3. Liệt kê các giọng phổ biến:
  python generate_vbee_voice.py --list-voices
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path
from typing import Any, Dict

# Đảm bảo in UTF-8 không lỗi font trên Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Bảng ánh xạ alias giọng đọc Vbee
VBEE_VOICE_ALIASES: Dict[str, Dict[str, str]] = {
    "thutrang": {
        "code": "hn_female_thutrang_48k-fhg",
        "label": "Thu Trang — Nữ · Bắc (KOC Review, 48kHz)"
    },
    "ngochuyen": {
        "code": "hn_female_ngochuyen_full_48k-fhg",
        "label": "Ngọc Huyền — Nữ · Bắc (Chuẩn tin tức, thuyết minh)"
    },
    "maiphuong": {
        "code": "hn_female_maiphuong_vdts_48k-fhg",
        "label": "Mai Phương — Nữ · Bắc (Truyền cảm)"
    },
    "manhdung": {
        "code": "hn_male_manhdung_news_48k-fhg",
        "label": "Mạnh Dũng — Nam · Bắc (Đọc báo, chuyên nghiệp)"
    },
    "ducanh": {
        "code": "hn_male_ducanh_48k-fhg",
        "label": "Đức Anh — Nam · Bắc (Tự nhiên, năng động)"
    },
    "thaotrinh": {
        "code": "sg_female_thaotrinh_48k-fhg",
        "label": "Thảo Trinh — Nữ · Nam (Truyền cảm, ấm áp)"
    },
    "minhhoang": {
        "code": "sg_male_minhhoang_48k-fhg",
        "label": "Minh Hoàng — Nam · Nam (Ấm áp, gần gũi)"
    },
    "lanhuong": {
        "code": "sg_female_lanhuong_48k-fhg",
        "label": "Lan Hương — Nữ · Nam (Nhẹ nhàng)"
    },
    "huonggiang": {
        "code": "hue_female_huonggiang_48k-fhg",
        "label": "Hương Giang — Nữ · Huế/Trung (Dịu dàng)"
    },
    "duyphuong": {
        "code": "hue_male_duyphuong_48k-fhg",
        "label": "Duy Phương — Nam · Huế/Trung (Ấm áp)"
    }
}


def load_env_credentials() -> Dict[str, str]:
    """Tìm và nạp VBEE_APP_ID và VBEE_ACCESS_TOKEN từ các file .env ứng viên."""
    creds = {
        "app_id": os.getenv("VBEE_APP_ID", ""),
        "access_token": os.getenv("VBEE_ACCESS_TOKEN", "")
    }
    if creds["app_id"] and creds["access_token"]:
        return creds

    candidate_files = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
        Path(os.getenv("VBEE_ENV_FILE", "")).expanduser() if os.getenv("VBEE_ENV_FILE") else None,
    ]

    for p in candidate_files:
        if p is None or not p.exists():
            continue
        try:
            for line in p.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k == "VBEE_APP_ID" and not creds["app_id"]:
                    creds["app_id"] = v
                elif k == "VBEE_ACCESS_TOKEN" and not creds["access_token"]:
                    creds["access_token"] = v
        except Exception:
            pass

    return creds


def get_audio_duration_seconds(file_path: Path) -> float:
    """Đo thời lượng audio thực tế bằng wave hoặc ffprobe."""
    if file_path.suffix.lower() == ".wav":
        try:
            with wave.open(str(file_path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return round(frames / float(rate), 2)
        except Exception:
            pass

    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            cmd = [
                ffprobe, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(file_path)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return round(float(res.stdout.strip()), 2)
        except Exception:
            pass
    return 0.0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sinh giọng đọc tiếng Việt qua Cloud API Vbee AIVoice."
    )
    parser.add_argument(
        "--text", "-t",
        type=str,
        default="",
        help="Nội dung văn bản cần đọc."
    )
    parser.add_argument(
        "--text-file", "-f",
        type=Path,
        default=None,
        help="Đường dẫn đến file .txt chứa văn bản cần đọc."
    )
    parser.add_argument(
        "--voice", "-v",
        type=str,
        default="thutrang",
        help="Alias giọng đọc (thutrang, ngochuyen, maiphuong...) hoặc mã đầy đủ Vbee. Mặc định: 'thutrang'."
    )
    parser.add_argument(
        "--speed", "-s",
        type=str,
        default="1.0",
        help="Tốc độ đọc từ 0.7 đến 1.5 (mặc định '1.0')."
    )
    parser.add_argument(
        "--format",
        type=str,
        default="mp3",
        choices=["mp3", "wav"],
        help="Định dạng audio xuất ra: 'mp3' hoặc 'wav' (mặc định 'mp3')."
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Đường dẫn file audio đầu ra (mặc định: output.mp3)."
    )
    parser.add_argument(
        "--session-dir",
        type=Path,
        default=None,
        help="Thư mục phiên làm việc để lưu kết quả."
    )
    parser.add_argument(
        "--app-id",
        type=str,
        default="",
        help="Vbee App ID (nếu không cung cấp, tự nạp từ .env)."
    )
    parser.add_argument(
        "--token",
        type=str,
        default="",
        help="Vbee Access Token (nếu không cung cấp, tự nạp từ .env)."
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="In danh sách các giọng đọc Vbee phổ biến và thoát."
    )

    args = parser.parse_args()

    if args.list_voices:
        print(json.dumps({
            "status": "success",
            "aliases": VBEE_VOICE_ALIASES
        }, ensure_ascii=False, indent=2))
        return 0

    # Nạp nội dung văn bản
    text = args.text
    if args.text_file and args.text_file.exists():
        text = args.text_file.read_text(encoding="utf-8").strip()

    if not text.strip():
        print(json.dumps({
            "status": "error",
            "error_type": "MissingText",
            "message": "Vui lòng cung cấp văn bản cần đọc qua --text hoặc --text-file."
        }, ensure_ascii=False, indent=2))
        return 1

    # Nạp thông tin xác thực
    creds = load_env_credentials()
    app_id = args.app_id or creds["app_id"]
    access_token = args.token or creds["access_token"]

    if not app_id or not access_token:
        print(json.dumps({
            "status": "error",
            "error_type": "MissingCredentials",
            "message": "Thiếu thông tin xác thực VBEE_APP_ID hoặc VBEE_ACCESS_TOKEN. Vui lòng cấu hình trong file .env hoặc truyền qua tham số --app-id / --token."
        }, ensure_ascii=False, indent=2))
        return 1

    # Xác định voice_code
    voice_key = args.voice.lower().strip()
    voice_code = VBEE_VOICE_ALIASES.get(voice_key, {}).get("code", args.voice)

    import datetime
    
    if args.output:
        out_path = args.output.resolve()
    else:
        if args.session_dir:
            session_dir = args.session_dir.resolve()
        else:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            session_dir = Path(f"./scratch/{today}_vbee-tts_default").resolve()
        out_path = session_dir / "output" / f"voiceover.{args.format}"
        
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not str(out_path).endswith(f".{args.format}"):
        out_path = out_path.with_suffix(f".{args.format}")

    # Gửi request lên Vbee API
    payload = {
        "app_id": app_id,
        "body": text,
        "voice_code": voice_code,
        "audio_type": args.format,
        "speed": str(args.speed)
    }

    req = urllib.request.Request(
        "https://api.vbee.vn/api/v1/tts",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        method="POST"
    )

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            audio_url = data.get("result", {}).get("audio_link") or data.get("audio_link")
            if not audio_url:
                print(json.dumps({
                    "status": "error",
                    "error_type": "ApiError",
                    "message": f"Vbee API không trả về audio link: {data}"
                }, ensure_ascii=False, indent=2))
                return 1

            # Tải file âm thanh về đĩa
            urllib.request.urlretrieve(audio_url, str(out_path))

            duration = get_audio_duration_seconds(out_path)

            result = {
                "status": "success",
                "engine": "vbee",
                "voice_alias": voice_key if voice_key in VBEE_VOICE_ALIASES else None,
                "voice_code": voice_code,
                "output_file": str(out_path),
                "duration_seconds": duration,
                "format": args.format,
                "file_size_bytes": out_path.stat().st_size if out_path.exists() else 0
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

    except Exception as exc:
        print(json.dumps({
            "status": "error",
            "error_type": "RequestFailed",
            "message": f"Lỗi gọi Vbee API: {exc}"
        }, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
