# video-transcribe Skill

Skill phiên âm tiếng nói (speech-to-text / subtitles) từ video hoặc tệp âm thanh thành phụ đề có mốc thời gian chính xác từng mili-giây (`timestamps`), hỗ trợ 3 phương thức phiên âm đa dạng.

Tự động nhận diện URL trực tuyến (YouTube Shorts, TikTok...), tải về trước bằng `yt-dlp`, nén tách âm thanh nhẹ bằng FFmpeg, tương tác hỏi và gợi ý phương thức tốt nhất cho người dùng, in bảng timeline trực quan và lưu 4 định dạng tệp chuẩn (`.srt`, `.vtt`, `.txt`, `.json`).

---

## 1. Cấu trúc Thư mục

```text
video-transcribe/
├── README.md                      # Hướng dẫn chi tiết cho Developer và AI Agent
├── SKILL.md                       # Khai báo kỹ năng chuẩn cho hệ thống Antigravity
└── scripts/
    ├── transcribe_video.py        # CLI điều phối chính + Menu tương tác + In timeline textblock
    ├── engines/
    │   ├── whisper_engine.py      # Engine faster-whisper (CTranslate2) chạy offline 100%
    │   ├── groq_engine.py         # Engine Groq Audio Transcriptions qua OpenAI-compatible API
    │   └── gemini_engine.py       # Engine Google Gemini Direct API (Generative Language)
    └── utils/
        ├── audio_prep.py          # Trích xuất âm thanh mono 64kbps MP3 bằng FFmpeg (<25MB)
        ├── subtitle_exporters.py  # Bộ xuất file .srt, .vtt, .txt, .json
        └── ytdlp_helper.py        # Helper tải media tự động qua yt-dlp
```

---

## 2. 3 Phương thức Phiên âm (Engines)

| Phương thức | Model mặc định | Đặc điểm nổi bật | Khi nào nên dùng? |
|---|---|---|---|
| **`groq`** | `whisper-large-v3-turbo` | ⚡ **Siêu tốc độ (~2-3s)**: Tốc độ xử lý LPU vượt trội, chính xác cao cho cả tiếng Việt và tiếng Anh. | Khuyến nghị khi cần transcript nhanh nhất hoặc video dài. |
| **`whisper`** | `large-v3` / `medium` / `small` | 🔒 **100% Offline & Miễn phí**: Chạy cục bộ bằng `faster-whisper`. Tự động nhận diện GPU NVIDIA CUDA (`float16`) hoặc CPU (`int8`). Không cần API key, không tốn quota. | Khuyến nghị khi cần bảo mật tuyệt đối, không có mạng hoặc không có API key. |
| **`gemini`** | `gemini-2.5-flash` | 🧠 **Phân tích Ngữ cảnh Sâu**: Gọi trực tiếp Google AI Studio API. Hiểu rõ ngữ điệu, video song ngữ phức tạp. | Khuyến nghị khi cần phân tích ngữ cảnh thoại hoặc phong cách KOC. |

---

## 3. Cấu hình Môi trường (.env)

Cấu hình các khóa API tương ứng trong file `.env`:

```env
# ==============================================================================
# VIDEO TRANSCRIPTION (video-transcribe)
# ==============================================================================
# 1. Groq Audio API (OpenAI-compatible)
GROQ_API_KEY=gsk_...
GROQ_ENDPOINT_URL=https://api.groq.com/openai/v1/audio/transcriptions
GROQ_TRANSCRIPTION_MODEL=whisper-large-v3-turbo

# 2. faster-whisper cục bộ (Tùy chọn cấu hình mặc định)
WHISPER_LOCAL_MODEL=large-v3
WHISPER_DEVICE=auto
WHISPER_COMPUTE_TYPE=auto

# 3. Google Gemini Direct API
GEMINI_TRANSCRIPTION_API_KEY=AIzaSy...
GEMINI_TRANSCRIPTION_MODEL=gemini-2.5-flash
```

---

## 4. Hướng dẫn Sử dụng (CLI)

### A. Chế độ Tương tác (Hỏi & Gợi ý Thông minh)
Khi người dùng truyền URL hoặc file mà không chỉ định rõ method, hệ thống sẽ hiển thị menu tư vấn:
```bash
python .agents/skills/video-transcribe/scripts/transcribe_video.py \
  --input "https://www.youtube.com/shorts/3001n8G4-gU" \
  --method interactive
```

Menu tương tác hiển thị:
```text
Select transcription method:
1. groq (Ultra fast, cloud based)
2. whisper (faster-whisper, offline, secure)
3. gemini (Deep analysis, cloud based)
Enter choice (1/2/3):
```

### B. Chạy Trực tiếp với faster-whisper (Offline)
```bash
python .agents/skills/video-transcribe/scripts/transcribe_video.py \
  --input "sessions/demo/voiceover.wav" \
  --method whisper
```

### C. Chạy Trực tiếp với Groq API
```bash
python .agents/skills/video-transcribe/scripts/transcribe_video.py \
  --input "video_review.mp4" \
  --method groq
```

### D. Chạy Trực tiếp với Google Gemini Direct API
```bash
python .agents/skills/video-transcribe/scripts/transcribe_video.py \
  --input "video_review.mp4" \
  --method gemini
```

---

## 5. Kết quả & Định dạng Đầu ra

Khi xử lý xong, màn hình console sẽ hiển thị:
1. Thông số xử lý: **Phương thức**, **Model**, **Thời lượng thực thi**.
2. **Timeline Textblock**:
```text
Phương thức đã dùng: whisper | Model: large-v3 (or fallback) | Thời lượng xử lý: 12.68s

--- Transcription Timeline ---
[00:00:00.000 --> 00:00:02.180]  Xin chào các bạn, hôm nay mình chia sẻ chiếc đầm này...
[00:00:02.200 --> 00:00:05.450]  Chất vải tơ tằm mềm mại cực kỳ tôn dáng.
```

3. Tự động xuất 4 tệp phụ đề tại thư mục thực thi:
- `<output>.srt`: Chuẩn SubRip Subtitle nạp thẳng vào CapCut, Premiere, DaVinci.
- `<output>.vtt`: Chuẩn WebVTT dành cho web video player.
- `<output>.txt`: Văn bản thoại thuần phục vụ phân tích kịch bản.
- `<output>.json`: Cấu trúc JSON chi tiết chứa timestamps `start`, `end`, `text`.
