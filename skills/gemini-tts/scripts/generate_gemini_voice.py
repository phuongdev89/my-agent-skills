#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_gemini_voice.py

Script tạo giọng đọc qua Gemini-TTS hỗ trợ cả 2 chế độ:
1. Google AI Studio chính hãng (Native Audio Modality qua REST API).
2. Gateway chuẩn OpenAI Compatibility (/v1/audio/speech hoặc /v1/chat/completions với audio modality).

Thuộc skill: .agents/skills/gemini-tts/

Quy tắc độc lập tuyệt đối (Strict Key Isolation):
- KHÔNG dùng chung key với bất kỳ agent nào khác (AI_AGENT_1, AI_AGENT_2...).
- Đọc biến môi trường riêng: GEMINI_TTS_API_KEY, GEMINI_TTS_ENDPOINT_URL, GEMINI_TTS_MODEL, GEMINI_TTS_VOICE.
- Tự động đóng gói và đo lường thời lượng audio thực tế chính xác (duration_seconds).
- Trả về JSON chuẩn để đối soát trong quy trình Dynamic Duration.
"""
from __future__ import annotations

import argparse
import base64
import datetime
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Danh mục giọng đọc Google AI Studio (Prebuilt Voices)
AISTUDIO_VOICE_CATALOG: Dict[str, Dict[str, str]] = {
    "kore": {
        "name": "Kore",
        "gender": "Nữ",
        "tone": "Ấm áp, êm dịu, thư thái, tự nhiên (rất hợp KOC nữ review đời sống, làm đẹp, thời trang)",
    },
    "aoede": {
        "name": "Aoede",
        "gender": "Nữ",
        "tone": "Trong trẻo, tươi vui, biểu cảm sinh động (rất hợp clip review đồ gia dụng, ẩm thực)",
    },
    "puck": {
        "name": "Puck",
        "gender": "Nam",
        "tone": "Năng động, nhiệt huyết, sôi nổi, trẻ trung (rất hợp KOC nam, unboxing, công nghệ)",
    },
    "charon": {
        "name": "Charon",
        "gender": "Nam",
        "tone": "Trầm ấm, chững chạc, uy quyền, điềm tĩnh (rất hợp phong cách podcast, tài chính, tin tức)",
    },
    "fenrir": {
        "name": "Fenrir",
        "gender": "Nam",
        "tone": "Mạnh mẽ, dứt khoát, lôi cuốn, giọng dày (hợp review thể thao, gaming, xe)",
    },
    "autonoe": {
        "name": "Autonoe",
        "gender": "Nữ",
        "tone": "Rõ ràng, dứt khoát, chuẩn mực, rành mạch (hợp giới thiệu tính năng, hướng dẫn)",
    },
}

# Danh mục giọng đọc OpenAI Compatibility
OPENAI_VOICE_CATALOG: Dict[str, Dict[str, str]] = {
    "alloy": {"name": "alloy", "gender": "Trung tính", "tone": "Cân bằng, phổ thông, rõ ràng"},
    "echo": {"name": "echo", "gender": "Nam", "tone": "Trầm, ấm, truyền cảm"},
    "fable": {"name": "fable", "gender": "Nam", "tone": "Biểu cảm, kể chuyện, hơi thở tự nhiên"},
    "onyx": {"name": "onyx", "gender": "Nam", "tone": "Trầm sâu, uy lực, nghiêm túc"},
    "nova": {"name": "nova", "gender": "Nữ", "tone": "Năng động, trẻ trung, tự nhiên (rất hợp KOC)"},
    "shimmer": {"name": "shimmer", "gender": "Nữ", "tone": "Trong trẻo, nhẹ nhàng, êm tai"},
}

DEFAULT_AISTUDIO_MODEL = "gemini-2.0-flash"
DEFAULT_OPENAI_MODEL = "gemini-2.0-flash"


def load_candidate_env() -> Dict[str, str]:
    """Tìm và nạp biến môi trường từ các file .env ứng viên."""
    env_vars: Dict[str, str] = {}
    candidate_files = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
        Path(r"d:\Affiliate\05_Tai_Khoan_Va_ID\.env"),
        Path(r"d:\Affiliate\04_Tools\idea_to_video_v2 - gemini\.env"),
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

    # Ưu tiên các biến chuyên dụng cho GEMINI_TTS trong os.environ
    for k in (
        "GEMINI_TTS_API_KEY",
        "GEMINI_TTS_ENDPOINT_URL",
        "GEMINI_TTS_MODEL",
        "GEMINI_TTS_VOICE",
        "GEMINI_TTS_PROVIDER",
        "GEMINI_API_KEY",
    ):
        val = os.getenv(k, "")
        if val:
            env_vars[k] = val
    return env_vars


def resolve_config(
    cli_key: Optional[str] = None,
    cli_endpoint: Optional[str] = None,
    cli_model: Optional[str] = None,
    cli_voice: Optional[str] = None,
    cli_provider: Optional[str] = None,
) -> Dict[str, str]:
    """Xác định toàn bộ cấu hình riêng cho Gemini TTS (tuyệt đối không dùng chung key agent khác)."""
    env = load_candidate_env()

    # 1. API Key: BẮT BUỘC dùng GEMINI_TTS_API_KEY hoặc GEMINI_API_KEY (không dùng AI_AGENT_*)
    api_key = (
        cli_key
        or env.get("GEMINI_TTS_API_KEY", "")
        or env.get("GEMINI_API_KEY", "")
    ).strip()

    # 2. Endpoint URL
    endpoint_url = (cli_endpoint or env.get("GEMINI_TTS_ENDPOINT_URL", "")).strip()

    # 3. Provider: Tự động phân tích (auto) hoặc gán thủ công
    provider = (cli_provider or env.get("GEMINI_TTS_PROVIDER", "auto")).strip().lower()
    if provider not in ("aistudio", "openai"):
        # Auto-detect dựa trên endpoint
        if endpoint_url and any(domain in endpoint_url.lower() for domain in ("openai.com", "phuonganh.io.vn", "/v1")):
            provider = "openai"
        elif endpoint_url and "googleapis.com" in endpoint_url.lower():
            provider = "aistudio"
        elif api_key.startswith("AIzaSy"):
            provider = "aistudio"
        elif api_key.startswith("sk-"):
            provider = "openai"
        else:
            provider = "aistudio"  # Mặc định Google AI Studio

    # 4. Model
    model = (
        cli_model
        or env.get("GEMINI_TTS_MODEL", "")
        or (DEFAULT_AISTUDIO_MODEL if provider == "aistudio" else DEFAULT_OPENAI_MODEL)
    ).strip()

    # 5. Voice
    default_voice = "kore" if provider == "aistudio" else "nova"
    voice = (cli_voice or env.get("GEMINI_TTS_VOICE", "") or default_voice).strip()

    return {
        "api_key": api_key,
        "endpoint_url": endpoint_url,
        "provider": provider,
        "model": model,
        "voice": voice,
    }


def resolve_voice_name(voice_input: str, provider: str) -> str:
    """Chuẩn hóa alias giọng đọc theo từng provider."""
    v_clean = voice_input.strip().lower()
    if provider == "aistudio":
        if v_clean in AISTUDIO_VOICE_CATALOG:
            return AISTUDIO_VOICE_CATALOG[v_clean]["name"]
        for k, info in AISTUDIO_VOICE_CATALOG.items():
            if v_clean == info["name"].lower():
                return info["name"]
    elif provider == "openai":
        if v_clean in OPENAI_VOICE_CATALOG:
            return OPENAI_VOICE_CATALOG[v_clean]["name"]
        for k, info in OPENAI_VOICE_CATALOG.items():
            if v_clean == info["name"].lower():
                return info["name"]

    return voice_input.strip()


def build_system_instruction(style: Optional[str] = None) -> str:
    """Tạo chỉ dẫn ngữ điệu phát âm tiếng Việt cho mô hình."""
    base = (
        "Bạn là người đọc thuyết minh và KOC chuyên nghiệp tiếng Việt. "
        "Nhiệm vụ duy nhất của bạn là đọc to, rõ ràng và truyền cảm văn bản được cung cấp. "
        "Yêu cầu bắt buộc:\n"
        "1. TUYỆT ĐỐI KHÔNG thêm lời chào mào, giải thích, hay bất kỳ từ nào ngoài văn bản gốc.\n"
        "2. Phát âm chuẩn tiếng Việt tự nhiên, ngắt nghỉ đúng dấu câu, không bị nuốt chữ hay giật cục.\n"
    )
    if style:
        base += f"3. Sắc thái biểu cảm: {style.strip()}.\n"
    else:
        base += "3. Sắc thái biểu cảm: Thân thiện, gần gũi như bạn bè chia sẻ trải nghiệm thực tế, giọng nói có sức sống.\n"
    return base


# ==============================================================================
# 1. HÌNH THỨC 1: GOOGLE AI STUDIO CHÍNH HÃNG (Native Audio Modality)
# ==============================================================================
def call_aistudio_audio_api(
    text: str,
    api_key: str,
    endpoint_url: str = "",
    model: str = DEFAULT_AISTUDIO_MODEL,
    voice_name: str = "Kore",
    style: Optional[str] = None,
    timeout: int = 120,
) -> Tuple[bytes, str, int]:
    """Gọi Google Generative Language REST API chính hãng.
    
    Returns:
        (raw_audio_bytes, mime_type, sample_rate)
    """
    if endpoint_url and "generateContent" in endpoint_url:
        endpoint = endpoint_url
        if "key=" not in endpoint:
            endpoint += f"{'&' if '?' in endpoint else '?'}key={api_key}"
    elif endpoint_url:
        base = endpoint_url.rstrip("/")
        endpoint = f"{base}/v1beta/models/{model}:generateContent?key={api_key}"
    else:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    sys_instruction = build_system_instruction(style)
    full_prompt = (
        f"{sys_instruction}\n"
        f"--- BẮT ĐẦU VĂN BẢN CẦN ĐỌC ---\n"
        f"{text.strip()}\n"
        f"--- KẾT THÚC VĂN BẢN ---"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": full_prompt}
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice_name
                    }
                }
            }
        }
    }

    req_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as response:
            resp_bytes = response.read()
            data = json.loads(resp_bytes.decode("utf-8"))
    except urllib.error.HTTPError as err:
        error_msg = err.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Google AI Studio HTTP Error {err.code}: {error_msg}")
    except Exception as exc:
        raise RuntimeError(f"Không thể kết nối đến Google AI Studio API: {exc}")

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini API không trả về candidates nào: {data}")

    parts = candidates[0].get("content", {}).get("parts", [])
    audio_part = None
    for p in parts:
        if "inlineData" in p or "inline_data" in p:
            audio_part = p.get("inlineData") or p.get("inline_data")
            break

    if not audio_part:
        text_parts = [p.get("text", "") for p in parts if "text" in p]
        raise RuntimeError(
            "Gemini không trả về dữ liệu audio. Nội dung text trả về: "
            f"{' '.join(text_parts) if text_parts else str(parts)}"
        )

    mime_type = audio_part.get("mimeType") or audio_part.get("mime_type") or "audio/pcm;rate=24000"
    b64_data = audio_part.get("data", "")
    if not b64_data:
        raise RuntimeError("Dữ liệu audio trong inlineData bị rỗng.")

    audio_bytes = base64.b64decode(b64_data)
    rate_match = re.search(r"rate=(\d+)", mime_type)
    sample_rate = int(rate_match.group(1)) if rate_match else 24000

    return audio_bytes, mime_type, sample_rate


# ==============================================================================
# 2. HÌNH THỨC 2: OPENAI COMPATIBILITY GATEWAY (/v1/audio/speech hoặc /v1/chat/completions)
# ==============================================================================
def call_openai_compat_speech_api(
    text: str,
    api_key: str,
    endpoint_url: str,
    model: str = DEFAULT_OPENAI_MODEL,
    voice_name: str = "nova",
    speed: float = 1.0,
    desired_format: str = "wav",
    style: Optional[str] = None,
    timeout: int = 120,
) -> Tuple[bytes, str, int]:
    """Gọi endpoint OpenAI Compatibility để sinh audio.
    
    Tự động hỗ trợ:
    - Chuẩn Speech: /v1/audio/speech (nhận trực tiếp stream binary audio)
    - Chuẩn Chat Audio: /v1/chat/completions (nhận base64 data trong choices[0].message.audio)
    """
    ctx = ssl.create_default_context()
    ep = endpoint_url.strip() if endpoint_url else "https://api.openai.com/v1/audio/speech"

    # Chuẩn bị URL chính xác
    if "/chat/completions" in ep:
        # Trường hợp 2A: Gateway chỉ hỗ trợ chat completions với audio modality
        sys_instruction = build_system_instruction(style)
        payload = {
            "model": model,
            "modalities": ["text", "audio"],
            "audio": {
                "voice": voice_name,
                "format": "wav" if desired_format == "wav" else "mp3",
            },
            "messages": [
                {"role": "system", "content": sys_instruction},
                {"role": "user", "content": text.strip()}
            ]
        }
        req_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            ep,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=timeout) as response:
                resp_json = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            err_text = err.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"OpenAI Compat (Chat) HTTP Error {err.code}: {err_text}")
        except Exception as exc:
            raise RuntimeError(f"Lỗi gọi OpenAI Compat Chat Audio: {exc}")

        msg = resp_json.get("choices", [{}])[0].get("message", {})
        audio_info = msg.get("audio", {})
        b64_data = audio_info.get("data", "")
        if not b64_data:
            raise RuntimeError(f"Không nhận được audio data từ gateway chat completions: {resp_json}")
        audio_bytes = base64.b64decode(b64_data)
        mime_type = f"audio/{audio_info.get('format', desired_format)}"
        return audio_bytes, mime_type, 24000

    else:
        # Trường hợp 2B: Chuẩn Audio Speech endpoint (/v1/audio/speech)
        speech_url = ep
        if not speech_url.endswith("/speech") and not speech_url.endswith("/audio/speech"):
            if speech_url.endswith("/v1"):
                speech_url += "/audio/speech"
            elif speech_url.endswith("/v1/"):
                speech_url += "audio/speech"
            else:
                speech_url = speech_url.rstrip("/") + "/v1/audio/speech"

        # Định dạng audio yêu cầu
        req_format = "wav" if desired_format.lower() == "wav" else "mp3"
        payload = {
            "model": model,
            "input": text.strip(),
            "voice": voice_name,
            "response_format": req_format,
            "speed": max(0.25, min(4.0, float(speed))),
        }

        req_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            speech_url,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=timeout) as response:
                audio_bytes = response.read()
                content_type = response.headers.get("Content-Type", f"audio/{req_format}")
                return audio_bytes, content_type, 24000
        except urllib.error.HTTPError as err:
            err_text = err.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"OpenAI Compat (Speech) HTTP Error {err.code}: {err_text}")
        except Exception as exc:
            raise RuntimeError(f"Lỗi gọi OpenAI Compat Speech endpoint ({speech_url}): {exc}")


def save_audio_file(
    audio_bytes: bytes,
    mime_type: str,
    sample_rate: int,
    output_path: Path,
    desired_format: str = "wav",
) -> Path:
    """Lưu dữ liệu audio và đóng gói thành file wav hoặc mp3 hoàn chỉnh."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    is_pcm = "pcm" in mime_type.lower() or mime_type.startswith("audio/l16")
    target_wav = output_path if desired_format.lower() == "wav" else output_path.with_suffix(".temp.wav")

    if is_pcm:
        # Raw 16-bit little-endian mono PCM (từ Gemini Native)
        with wave.open(str(target_wav), "wb") as wf:
            wf.setnchannels(1)       # Mono
            wf.setsampwidth(2)       # 16-bit = 2 bytes
            wf.setframerate(sample_rate)
            wf.writeframes(audio_bytes)
    else:
        # File đã có container hoàn chỉnh (WAV, MP3...)
        target_wav.write_bytes(audio_bytes)

    # Chuyển đổi sang MP3 nếu yêu cầu và file hiện tại là WAV
    if desired_format.lower() == "mp3":
        target_mp3 = output_path.with_suffix(".mp3")
        # Nếu audio_bytes bản thân đã là MP3 thì đổi tên hoặc giữ nguyên
        if "mpeg" in mime_type.lower() or "mp3" in mime_type.lower() or audio_bytes[:3] == b"ID3" or audio_bytes[:2] == b"\xff\xfb":
            target_mp3.write_bytes(audio_bytes)
            if target_wav.exists() and target_wav != target_mp3:
                target_wav.unlink(missing_ok=True)
            return target_mp3

        ffmpeg_bin = shutil.which("ffmpeg")
        if ffmpeg_bin:
            try:
                cmd = [
                    ffmpeg_bin, "-y",
                    "-i", str(target_wav),
                    "-codec:a", "libmp3lame",
                    "-qscale:a", "2",
                    str(target_mp3),
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                if target_wav.exists() and target_wav != target_mp3:
                    target_wav.unlink(missing_ok=True)
                return target_mp3
            except Exception:
                pass
        
        # Nếu không có ffmpeg thì lưu đuôi .wav
        if target_wav != output_path:
            target_wav.rename(output_path.with_suffix(".wav"))
            return output_path.with_suffix(".wav")
        return target_wav

    return target_wav


def measure_audio_duration(file_path: Path) -> float:
    """Đo thời lượng audio chính xác tính theo giây."""
    if not file_path.is_file() or file_path.stat().st_size <= 0:
        return 0.0

    if file_path.suffix.lower() == ".wav":
        try:
            with wave.open(str(file_path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return round(frames / float(rate), 3)
        except Exception:
            pass

    ffprobe_bin = shutil.which("ffprobe")
    if ffprobe_bin:
        try:
            cmd = [
                ffprobe_bin,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return round(float(proc.stdout.strip()), 3)
        except Exception:
            pass

    return 0.0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gemini-TTS Voice Generator CLI (Google AI Studio & OpenAI Compatibility)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--text", type=str, help="Văn bản tiếng Việt cần đọc")
    parser.add_argument("--text-file", type=str, help="Đường dẫn file .txt chứa kịch bản")
    parser.add_argument(
        "--voice",
        type=str,
        default=None,
        help="Giọng đọc hoặc alias (AI Studio: kore, puck, aoede, charon... / OpenAI: nova, alloy, shimmer...)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["auto", "aistudio", "openai"],
        default=None,
        help="Chế độ cung cấp: aistudio (Google chính hãng) hoặc openai (OpenAI compatible gateway)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Tên model xuất audio (mặc định theo provider)",
    )
    parser.add_argument(
        "--style",
        type=str,
        default=None,
        help="Sắc thái biểu cảm giọng điệu (VD: 'hào hứng, năng động', 'trầm ấm, tin cậy')",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Tốc độ đọc (dành cho chế độ OpenAI compat, mặc định: 1.0)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["wav", "mp3"],
        default="wav",
        help="Định dạng container đầu ra (wav hoặc mp3, mặc định: wav)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Đường dẫn file output âm thanh",
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
        help="API key riêng cho Gemini TTS (nếu không truyền sẽ đọc GEMINI_TTS_API_KEY từ .env)",
    )
    parser.add_argument(
        "--endpoint-url",
        type=str,
        default=None,
        help="Endpoint URL tùy chỉnh (GEMINI_TTS_ENDPOINT_URL từ .env)",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="Liệt kê danh sách các giọng có sẵn và thoát",
    )

    args = parser.parse_args()

    # 1. Liệt kê danh mục giọng đọc
    if args.list_voices:
        out = {
            "status": "success",
            "aistudio_voices": AISTUDIO_VOICE_CATALOG,
            "openai_compat_voices": OPENAI_VOICE_CATALOG,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(0)

    # 2. Đọc cấu hình biệt lập (Key isolation)
    cfg = resolve_config(
        cli_key=args.api_key,
        cli_endpoint=args.endpoint_url,
        cli_model=args.model,
        cli_voice=args.voice,
        cli_provider=args.provider,
    )

    if not cfg["api_key"]:
        err_response = {
            "status": "error",
            "message": (
                "Không tìm thấy API Key riêng biệt cho Gemini-TTS. "
                "Vui lòng cấu hình GEMINI_TTS_API_KEY trong file .env hoặc truyền qua tham số --api-key. "
                "(Lưu ý: Theo quy tắc, Gemini-TTS không dùng chung API key với các agent khác để bảo đảm tính độc lập)."
            ),
        }
        print(json.dumps(err_response, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 3. Thu thập văn bản
    text = ""
    if args.text:
        text = args.text.strip()
    elif args.text_file:
        tf = Path(args.text_file)
        if not tf.is_file():
            print(json.dumps({"status": "error", "message": f"File không tồn tại: {tf}"}, ensure_ascii=False))
            sys.exit(1)
        text = tf.read_text(encoding="utf-8").strip()

    if not text:
        print(
            json.dumps(
                {"status": "error", "message": "Vui lòng cung cấp văn bản qua --text hoặc --text-file"},
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    provider = cfg["provider"]
    voice_name = resolve_voice_name(cfg["voice"], provider)
    model = cfg["model"]

    # 4. Xác định đường dẫn file đầu ra
    if args.output:
        out_path = Path(args.output).resolve()
    else:
        if args.session_dir:
            session_dir = Path(args.session_dir).resolve()
        else:
            today_str = datetime.datetime.now().strftime("%Y%m%d")
            session_dir = Path.cwd() / "scratch" / f"{today_str}_gemini-tts_default"
        out_path = session_dir / "output" / f"voiceover.{args.format}"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 5. Gọi API tương ứng với từng Provider
    try:
        if provider == "aistudio":
            audio_bytes, mime_type, sample_rate = call_aistudio_audio_api(
                text=text,
                api_key=cfg["api_key"],
                endpoint_url=cfg["endpoint_url"],
                model=model,
                voice_name=voice_name,
                style=args.style,
            )
        else:
            audio_bytes, mime_type, sample_rate = call_openai_compat_speech_api(
                text=text,
                api_key=cfg["api_key"],
                endpoint_url=cfg["endpoint_url"],
                model=model,
                voice_name=voice_name,
                speed=args.speed,
                desired_format=args.format,
                style=args.style,
            )

        final_file = save_audio_file(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            sample_rate=sample_rate,
            output_path=out_path,
            desired_format=args.format,
        )

        duration = measure_audio_duration(final_file)
        result = {
            "status": "success",
            "engine": "gemini-tts",
            "provider": provider,
            "model": model,
            "voice": voice_name,
            "output_file": str(final_file),
            "duration_seconds": duration,
            "sample_rate": sample_rate,
            "file_size_bytes": final_file.stat().st_size if final_file.exists() else 0,
            "audio_format": final_file.suffix.lstrip(".").lower(),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    except Exception as exc:
        err_result = {
            "status": "error",
            "engine": "gemini-tts",
            "provider": provider,
            "model": model,
            "voice": voice_name,
            "message": str(exc),
        }
        print(json.dumps(err_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
