---
name: video-transcribe
description: |
  Phiên âm (transcribe) video và âm thanh thành phụ đề có timeline thời gian thực.
  Hỗ trợ 3 phương thức: Groq API (OpenAI-compatible), faster-whisper cục bộ, Google Gemini Direct API.
  Tự động tải link YouTube/video bằng yt-dlp, hỏi người dùng chọn phương thức kèm gợi ý, và xuất 4 tệp (.srt, .vtt, .txt, .json).
---

# video-transcribe

Skill phiên âm tiếng nói từ video hoặc tệp âm thanh thành phụ đề có mốc thời gian chính xác (timestamped subtitles) phục vụ phân tích kịch bản KOC hoặc làm phụ đề video.

## Quy Chuẩn Bắt Buộc Về Thư Mục Phiên Làm Việc (Session Dir)

> [!IMPORTANT]
> **QUY TẮC CÔ LẬP DỮ LIỆU & BẢO VỆ MÃ NGUỒN**:
> Tuyệt đối **KHÔNG** xả file phụ đề (`.srt`, `.vtt`, `.txt`, `.json`), file âm thanh trích xuất tạm thời hoặc video tải về trực tiếp ra thư mục gốc repo. Mọi tác vụ phiên âm phải được đóng gói gọn trong thư mục session chuẩn hóa.

- **Thư mục gốc:** `./scratch/`
- **Cú pháp đặt tên:** `./scratch/yyyy-mm-dd_video-transcribe_công-việc-viết-không-dấu`
  - Ví dụ: `./scratch/2026-09-22_video-transcribe_boc-bang-short-koc`
- **Cấu trúc phân vùng thư mục con bắt buộc:**
  ```text
  ./scratch/yyyy-mm-dd_video-transcribe_công-việc-viết-không-dấu/
  ├── downloads/  # (hoặc input/) Chứa video gốc tải về từ YouTube/TikTok hoặc tệp media nguồn
  ├── output/     # (hoặc generated/) Chứa 4 định dạng phụ đề xuất xưởng (`transcription.srt`, `.vtt`, `.txt`, `.json`)
  ├── scripts/    # Chứa script xử lý phân đoạn / tinh chỉnh phụ đề riêng cho session (tuyệt đối không sửa src/)
  └── temp/       # Chứa luồng âm thanh trích xuất mono MP3 64kbps và tệp tạm trong quá trình phiên âm
  ```
- **Tự động phân phối tài nguyên bằng tham số `--session-dir`:**
  - Script `transcribe_video.py` hỗ trợ tham số `--session-dir <đường_dẫn_session>`.
  - Khi truyền `--session-dir`, script sẽ **tự động**:
    1. Trích xuất âm thanh trung gian vào `<session_dir>/temp/`.
    2. Xuất toàn bộ 4 file phụ đề hoàn chỉnh vào `<session_dir>/output/`.

## 3 Phương thức Phiên âm (Transcription Engines)

| Phương thức | Model mặc định | Điểm mạnh & Khuyến nghị |
|---|---|---|
| **`groq`** | `whisper-large-v3-turbo` | ⚡ **Siêu tốc độ (~2-3s)**: Khuyến nghị khi cần nhanh nhất, độ chính xác cao nhất cho cả tiếng Việt và tiếng Anh. Gọi qua OpenAI-compatible endpoint. |
| **`whisper`** | `large-v3` / fallback `medium` | 🔒 **100% Offline & Bảo mật**: Chạy trực tiếp trên máy bằng engine `faster-whisper` (CTranslate2). Tự động nhận diện GPU CUDA / CPU int8. Không tốn API key/quota. |
| **`gemini`** | `gemini-2.5-flash` | 🧠 **Phân tích Ngữ cảnh Sâu**: Gọi trực tiếp Google Generative Language API. Thích hợp cho video song ngữ phức tạp hoặc cần bóc tách ngữ điệu/cảm xúc. |

## Luồng Tương tác & Trải nghiệm Người dùng

1. **Tiếp nhận Nguồn**:
   - Nếu người dùng gửi đường link (YouTube Shorts, YouTube Video, TikTok...): Hệ thống tự động dùng `yt-dlp` tải video về trước.
   - Nếu đầu vào là file video (`.mp4`, `.mov`, `.mkv`...): Hệ thống tự động dùng FFmpeg trích xuất luồng âm thanh nhẹ mono 64kbps MP3 (<25MB).
2. **Hỏi & Gợi ý Thông minh**:
   - Dừng lại hỏi người dùng muốn chọn phương thức nào (1, 2, hay 3), nêu rõ ưu điểm của từng phương thức và gợi ý phương án tối ưu nhất.
3. **Thực thi & Báo cáo Minh bạch**:
   - Nêu rõ **Phương thức**, **Model**, và **Thời gian xử lý**.
   - Hiển thị toàn bộ phân đoạn theo timeline trong Textblock dạng `[HH:MM:SS.mmm --> HH:MM:SS.mmm] Lời thoại`.
   - Tự động xuất hoặc cho phép lưu 4 định dạng tệp chuẩn:
     * `<output>.srt`: SubRip Subtitle chuẩn CapCut/Premiere/DaVinci.
     * `<output>.vtt`: WebVTT cho trình duyệt web.
     * `<output>.txt`: Lời thoại văn bản thuần.
     * `<output>.json`: Dữ liệu phân đoạn có timestamps.

## Hướng dẫn Sử dụng (CLI)

```bash
# Thiết lập biến session_dir chuẩn hóa
SESSION_DIR="./scratch/2026-09-22_video-transcribe_boc-bang-short-koc"

# 1. Chế độ Tương tác từ link video (Hỏi người dùng & gợi ý, tự động xuất ra session_dir/output/)
python .agents/skills/video-transcribe/scripts/transcribe_video.py \
  --input "https://www.youtube.com/shorts/..." \
  --method interactive \
  --session-dir "$SESSION_DIR"

# 2. Chạy nhanh bằng faster-whisper cục bộ (Offline)
python .agents/skills/video-transcribe/scripts/transcribe_video.py \
  --input "$SESSION_DIR/downloads/video.mp4" \
  --method whisper \
  --session-dir "$SESSION_DIR"

# 3. Chạy siêu tốc bằng Groq API
python .agents/skills/video-transcribe/scripts/transcribe_video.py \
  --input "$SESSION_DIR/downloads/video.mp4" \
  --method groq \
  --session-dir "$SESSION_DIR"

# 4. Chạy qua Google Gemini Direct API
python .agents/skills/video-transcribe/scripts/transcribe_video.py \
  --input "$SESSION_DIR/downloads/video.mp4" \
  --method gemini \
  --session-dir "$SESSION_DIR"
```

### Cấu hình Biến môi trường (.env)

- **Groq:** `GROQ_API_KEY`, `GROQ_ENDPOINT_URL` (mặc định: `https://api.groq.com/openai/v1/audio/transcriptions`).
- **Gemini Direct:** `GEMINI_TRANSCRIPTION_API_KEY` (hoặc `GEMINI_TTS_API_KEY`, `GEMINI_API_KEY`).
- **faster-whisper:** Không yêu cầu API Key. Tự động tải weights lần đầu vào cache HuggingFace.

## Mẫu Đầu ra Console

```text
Preparing media for transcription...

Using method: whisper

Phương thức đã dùng: whisper | Model: large-v3 (or fallback) | Thời lượng xử lý: 12.68s

--- Transcription Timeline ---
[00:00:00.000 --> 00:00:02.180]  I don't know how to tell you.

Exporting files...
Exported to ./scratch/2026-09-22_video-transcribe_boc-bang-short-koc/output/transcription.[srt|vtt|txt|json]
```
