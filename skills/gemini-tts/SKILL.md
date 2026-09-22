---
name: gemini-tts
description: Generate expressive, style-controlled Vietnamese voiceovers using Google Gemini's native audio modality (Gemini 2.0/2.5 Flash) or OpenAI-compatible gateways. Use when creating AI voiceovers with customizable emotion, style prompts (energetic KOC, warm storytelling), or when user requests Gemini TTS.
---

# Gemini-TTS (Google GenAI & OpenAI-Compatible Audio Generation)

**Gemini-TTS** hỗ trợ 2 hình thức tạo giọng đọc AI tiếng Việt thế hệ mới với khả năng biểu cảm và tùy biến sắc thái cao:
1. **Google AI Studio chính hãng (Native Audio Modality)**: Xuất âm thanh bản địa từ dòng `gemini-2.0-flash` / `gemini-2.5-flash`, điều khiển ngữ điệu tự nhiên bằng câu lệnh (`--style`), hỗ trợ các giọng prebuilt như Kore, Puck, Aoede, Charon...
2. **OpenAI Compatibility Gateway**: Kết nối linh hoạt qua các trạm trung chuyển (như Omniroute, OneAPI, OpenAI proxy) hỗ trợ endpoint `/v1/audio/speech` hoặc `/v1/chat/completions` (modalities audio).

## Quy Chuẩn Bắt Buộc Về Thư Mục Phiên Làm Việc (Session Dir)

> [!IMPORTANT]
> **QUY TẮC CÔ LẬP DỮ LIỆU & BẢO VỆ MÃ NGUỒN**:
> Tuyệt đối **KHÔNG** xả file âm thanh hay script tạo voice trực tiếp ra thư mục gốc repo hoặc `04_canh/` bừa bãi. Mọi tác vụ sinh giọng đọc phải được tổ chức trong thư mục session chuẩn hóa.

- **Thư mục gốc:** `./scratch/`
- **Cú pháp đặt tên:** `./scratch/yyyy-mm-dd_gemini-tts_công-việc-viết-không-dấu`
  - Ví dụ: `./scratch/2026-09-22_gemini-tts_sinh-voice-koc-ao-polo`
- **Cấu trúc phân vùng thư mục con bắt buộc:**
  ```text
  ./scratch/yyyy-mm-dd_gemini-tts_công-việc-viết-không-dấu/
  ├── input/      # Chứa file văn bản kịch bản phân cảnh (`voice_segment.txt`, `script.txt`)
  ├── output/     # Chứa tệp âm thanh hoàn chỉnh (`voiceover.wav`, `voiceover.mp3`, `S01_audio.wav`)
  ├── scripts/    # Chứa script tiện ích / tinh chỉnh bổ trợ phiên làm việc (tuyệt đối không sửa src/)
  └── temp/       # Chứa audio chunks tạm, cache giải mã âm thanh
  ```
- **Tự động phân phối tài nguyên bằng tham số `--session-dir`:**
  - Script `generate_gemini_voice.py` hỗ trợ tham số `--session-dir <đường_dẫn_session>`.
  - Khi có `--session-dir` và không truyền `--output`, script tự động xuất file âm thanh vào `<session_dir>/output/voiceover.<format>`.
  - Hoặc có thể chỉ định chính xác `--output <session_dir>/output/<tên_file>`.

---

## 1. Quy tắc Khóa Độc Lập (Strict Key Isolation)

> [!IMPORTANT]
> **TUYỆT ĐỐI KHÔNG DÙNG CHUNG KEY VỚI CÁC AGENT KHÁC.**
> `gemini-tts` sở hữu bộ biến môi trường độc lập hoàn toàn, không phụ thuộc hay can thiệp vào `AI_AGENT_1_API_KEY`, `AI_AGENT_2_API_KEY`... nhằm đảm bảo hạn ngạch (rate limit), tính ổn định và tách bạch trách nhiệm hệ thống.

Cấu hình trong file `.env` tại thư mục dự án hoặc `d:\Affiliate\05_Tai_Khoan_Va_ID\.env`:

```env
# ==============================================================================
# GEMINI-TTS (Giọng đọc AI độc lập)
# ==============================================================================
GEMINI_TTS_ENABLE=true
GEMINI_TTS_API_KEY=your_dedicated_key_here
GEMINI_TTS_ENDPOINT_URL=
GEMINI_TTS_MODEL=gemini-2.0-flash
GEMINI_TTS_VOICE=Kore
```

### Các kịch bản cấu hình thực tế:

#### Kịch bản A: Dùng Google AI Studio chính hãng
```env
GEMINI_TTS_ENDPOINT_URL=
GEMINI_TTS_API_KEY=AIzaSy...
GEMINI_TTS_MODEL=gemini-2.0-flash
GEMINI_TTS_VOICE=Kore
```

#### Kịch bản B: Dùng Gateway chuẩn OpenAI Compatibility
```env
GEMINI_TTS_ENDPOINT_URL=https://omniroute.phuonganh.io.vn/v1/audio/speech
GEMINI_TTS_API_KEY=sk-...
GEMINI_TTS_MODEL=gemini-2.0-flash
GEMINI_TTS_VOICE=nova
```

---

## 2. Tiện ích Thực thi CLI (`scripts/generate_gemini_voice.py`)

Skill cung cấp sẵn script CLI thực thi hoàn chỉnh tại:
[`scripts/generate_gemini_voice.py`](scripts/generate_gemini_voice.py)

Tự động nhận diện provider (`aistudio` hoặc `openai`) dựa trên endpoint và API key.

```bash
# Thiết lập biến session_dir chuẩn hóa
SESSION_DIR="./scratch/2026-09-22_gemini-tts_sinh-voice-koc-ao-polo"
```

### A. Sinh voice qua Google AI Studio (Tự động xuất vào session_dir/output/)
```bash
python .agents/skills/gemini-tts/scripts/generate_gemini_voice.py \
  --text "Chào bạn! Chiếc áo polo này mặc lên form cực kỳ tôn dáng luôn nhé." \
  --voice "kore" \
  --style "Hào hứng, tươi vui, phong cách KOC thân thiện chia sẻ trải nghiệm bạn bè" \
  --session-dir "$SESSION_DIR"
```

### B. Sinh voice qua OpenAI Compatibility Gateway (Chỉ định rõ file trong output/)
```bash
python .agents/skills/gemini-tts/scripts/generate_gemini_voice.py \
  --text "Chào bạn! Đây là giọng đọc qua OpenAI compatible gateway nhé." \
  --provider "openai" \
  --voice "nova" \
  --speed 1.05 \
  --format "mp3" \
  --session-dir "$SESSION_DIR" \
  --output "$SESSION_DIR/output/S01_audio.mp3"
```

### C. Đọc từ file kịch bản trong input/ của session
```bash
python .agents/skills/gemini-tts/scripts/generate_gemini_voice.py \
  --text-file "$SESSION_DIR/input/voice_segment.txt" \
  --voice "puck" \
  --session-dir "$SESSION_DIR" \
  --output "$SESSION_DIR/output/S01_audio.wav"
```

### D. Liệt kê toàn bộ danh mục giọng đọc có sẵn
```bash
python .agents/skills/gemini-tts/scripts/generate_gemini_voice.py --list-voices
```

### Định dạng đầu ra (JSON Output)
Script trả về kết quả chuẩn JSON giúp Agent và hệ thống đối soát độ dài file âm thanh:
```json
{
  "status": "success",
  "engine": "gemini-tts",
  "provider": "aistudio",
  "model": "gemini-2.0-flash",
  "voice": "Kore",
  "output_file": "D:\\Affiliate\\04_Tools\\idea_to_video_v2 - gemini\\scratch\\2026-09-22_gemini-tts_sinh-voice-koc-ao-polo\\output\\voiceover.wav",
  "duration_seconds": 4.15,
  "sample_rate": 24000,
  "file_size_bytes": 199244,
  "audio_format": "wav"
}
```

---

## 3. Danh mục Giọng đọc Hỗ trợ

### 3.1. Google AI Studio (Prebuilt Voices)
| Voice | Giới tính | Sắc thái & Ứng dụng gợi ý |
| :--- | :--- | :--- |
| **`Kore`** *(Mặc định)* | Nữ | Ấm áp, êm dịu, thư thái, tự nhiên (rất hợp KOC nữ review thời trang, mỹ phẩm, đời sống) |
| **`Aoede`** | Nữ | Trong trẻo, tươi vui, biểu cảm sinh động (rất hợp clip đồ gia dụng, ẩm thực, unboxing) |
| **`Puck`** | Nam | Năng động, nhiệt huyết, sôi nổi, trẻ trung (rất hợp KOC nam, công nghệ, thể thao) |
| **`Charon`** | Nam | Trầm ấm, chững chạc, uy quyền, điềm tĩnh (rất hợp podcast, bất động sản, tài chính) |
| **`Fenrir`** | Nam | Mạnh mẽ, dứt khoát, lôi cuốn, giọng dày (hợp review đồ nam, gaming, xe máy) |
| **`Autonoe`** | Nữ | Rõ ràng, dứt khoát, chuẩn mực, rành mạch (hợp thuyết minh tính năng sản phẩm) |

### 3.2. OpenAI Compatibility (Standard Voices)
| Voice | Giới tính | Đặc điểm |
| :--- | :--- | :--- |
| **`nova`** *(Mặc định)* | Nữ | Năng động, trẻ trung, tự nhiên (rất hợp KOC review) |
| **`shimmer`** | Nữ | Trong trẻo, nhẹ nhàng, êm tai |
| **`alloy`** | Trung tính | Cân bằng, phổ thông, rõ ràng |
| **`echo`** | Nam | Trầm ấm, truyền cảm |
| **`fable`** | Nam | Biểu cảm, phong cách kể chuyện |
| **`onyx`** | Nam | Trầm sâu, uy lực, nghiêm túc |

---

## 4. Quy tắc KOC & Dynamic Duration (Bắt buộc)

1. **KOC Identity**: Lời thoại đọc voice tuyệt đối KHÔNG nhắc KOC là AI, avatar ảo hay đang làm affiliate/quảng cáo. CẤM các từ khóa bán hàng thô thiển: *giỏ hàng, link bio, link affiliate, mua ngay, nhanh tay, voucher, shop...*
2. **Thời lượng linh hoạt (Dynamic Duration)**: Tuyệt đối KHÔNG cố định thời lượng video là 28s. Độ dài video được tính động từ chính trường `duration_seconds` do script trả về sau khi sinh file audio thực tế.
