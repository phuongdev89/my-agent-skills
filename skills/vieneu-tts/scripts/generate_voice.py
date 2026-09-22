#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_voice.py

Script tạo giọng đọc tiếng Việt on-device bằng VieNeu-TTS v3 Turbo (48kHz).
Thuộc skill: .agents/skills/vieneu-tts/

Hỗ trợ:
- Đọc văn bản bằng các giọng dựng sẵn (Minh Quân, Đoan Trang, Ngọc Huyền, Mai Anh...)
- Nhân bản giọng nói tức thì (Instant Voice Cloning) từ audio mẫu 3-8s
- Hỗ trợ tag cảm xúc trực tiếp trong văn bản: [cười], [thở dài], [hắng giọng]
- Tự động kiểm tra cài đặt thư viện 'vieneu', báo lỗi chi tiết nếu thiếu.
- Xuất kết quả chuẩn JSON (đường dẫn, thời lượng audio, sample rate).

Cách dùng:
  # 1. Đọc bằng giọng dựng sẵn:
  python generate_voice.py --text "Chào bạn, đây là giọng Đoan Trang [cười]." --voice "Đoan Trang" --output output.wav

  # 2. Clone giọng KOC từ audio mẫu:
  python generate_voice.py --text "Chất vải này mịn lắm mọi người ơi!" --ref-audio "ref_koc.wav" --output koc_voice.wav

  # 3. Đọc nội dung từ file văn bản:
  python generate_voice.py --text-file "script.txt" --voice "Minh Quân" --output output.wav

  # 4. Liệt kê các giọng dựng sẵn:
  python generate_voice.py --list-voices
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Đảm bảo in UTF-8 không lỗi font trên Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def check_vieneu_installed() -> bool:
    """Kiểm tra package vieneu đã được cài đặt trong môi trường hiện tại chưa."""
    try:
        import vieneu  # noqa: F401
        return True
    except ImportError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sinh giọng đọc tiếng Việt on-device chất lượng cao bằng VieNeu-TTS v3 Turbo (48kHz)."
    )
    parser.add_argument(
        "--text", "-t",
        type=str,
        default="",
        help="Nội dung văn bản cần chuyển thành giọng nói. Hỗ trợ tag [cười], [thở dài]..."
    )
    parser.add_argument(
        "--text-file", "-f",
        type=Path,
        default=None,
        help="Đường dẫn đến file .txt chứa kịch bản cần đọc."
    )
    parser.add_argument(
        "--voice", "-v",
        type=str,
        default="Đoan Trang",
        help="Tên giọng dựng sẵn (mặc định: 'Đoan Trang'). Các giọng phổ biến: Minh Quân, Đoan Trang, Ngọc Huyền, Mai Anh, Thái Sơn..."
    )
    parser.add_argument(
        "--ref-audio", "-r",
        type=Path,
        default=None,
        help="Đường dẫn file audio mẫu (3-8 giây) để nhân bản giọng nói (Instant Voice Cloning)."
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Đường dẫn file audio đầu ra (.wav)."
    )
    parser.add_argument(
        "--session-dir",
        type=Path,
        default=None,
        help="Thư mục phiên làm việc để lưu kết quả."
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.8,
        help="Độ biến thiên ngữ điệu (mặc định 0.8, tối ưu cho tag cảm xúc)."
    )
    parser.add_argument(
        "--no-denoise",
        action="store_true",
        help="Tắt tự động khử nhiễu cho file ref-audio (mặc định luôn tự denoise)."
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="In danh sách toàn bộ các giọng dựng sẵn có trong mô hình và thoát."
    )

    args = parser.parse_args()

    # Kiểm tra cài đặt thư viện vieneu
    if not check_vieneu_installed():
        error_res = {
            "status": "error",
            "error_type": "PackageNotInstalled",
            "message": "Chưa cài đặt thư viện 'vieneu'. Hãy cài đặt bằng lệnh: pip install vieneu (cho CPU/ONNX) hoặc pip install \"vieneu[cuda]\" (cho GPU NVIDIA CUDA).",
            "install_command": "pip install vieneu"
        }
        print(json.dumps(error_res, ensure_ascii=False, indent=2))
        return 1

    try:
        from vieneu import Vieneu
        v = Vieneu()
    except Exception as e:
        error_res = {
            "status": "error",
            "error_type": "InitializationError",
            "message": f"Lỗi khởi tạo mô hình VieNeu-TTS: {e}"
        }
        print(json.dumps(error_res, ensure_ascii=False, indent=2))
        return 1

    # Nếu yêu cầu liệt kê danh sách giọng
    if args.list_voices:
        try:
            voices = v.list_preset_voices()
            voice_list = [{"label": label, "voice_id": vid} for label, vid in voices]
            print(json.dumps({"status": "success", "total": len(voice_list), "voices": voice_list}, ensure_ascii=False, indent=2))
            return 0
        except Exception as e:
            print(json.dumps({"status": "error", "message": f"Không thể lấy danh sách giọng: {e}"}, ensure_ascii=False))
            return 1

    # Đọc nội dung văn bản
    text = args.text
    if args.text_file and args.text_file.exists():
        text = args.text_file.read_text(encoding="utf-8").strip()

    if not text.strip():
        error_res = {
            "status": "error",
            "error_type": "MissingText",
            "message": "Vui lòng cung cấp văn bản cần đọc qua --text hoặc --text-file."
        }
        print(json.dumps(error_res, ensure_ascii=False, indent=2))
        return 1

    # Chuẩn bị file output
    import datetime
    
    if args.output:
        out_path = args.output.resolve()
    else:
        if args.session_dir:
            session_dir = args.session_dir.resolve()
        else:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            session_dir = Path(f"./scratch/{today}_vieneu-tts_default").resolve()
        out_path = session_dir / "output" / "voiceover.wav"
        
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not str(out_path).endswith(".wav"):
        out_path = out_path.with_suffix(".wav")

    # Tiến hành suy luận âm thanh (Inference)
    try:
        if args.ref_audio and args.ref_audio.exists():
            # Chế độ Instant Voice Cloning
            audio = v.infer(
                text=text,
                ref_audio=str(args.ref_audio.resolve()),
                denoise=not args.no_denoise,
                temperature=args.temperature,
            )
            mode = "voice_cloning"
            voice_used = f"clone_from:{args.ref_audio.name}"
        else:
            # Chế độ Preset Voice
            audio = v.infer(
                text=text,
                voice=args.voice,
                temperature=args.temperature,
            )
            mode = "preset_voice"
            voice_used = args.voice

        # Lưu audio đầu ra
        v.save(audio, str(out_path))

        # Tính thời lượng audio chính xác (VieNeu v3 Turbo xuất 48,000 Hz)
        sample_rate = 48000
        duration_seconds = round(len(audio) / sample_rate, 2)

        result = {
            "status": "success",
            "mode": mode,
            "voice": voice_used,
            "output_file": str(out_path),
            "duration_seconds": duration_seconds,
            "sample_rate": sample_rate,
            "file_size_bytes": out_path.stat().st_size if out_path.exists() else 0
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    except Exception as e:
        error_res = {
            "status": "error",
            "error_type": "InferenceError",
            "message": f"Lỗi trong quá trình sinh âm thanh: {e}"
        }
        print(json.dumps(error_res, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
