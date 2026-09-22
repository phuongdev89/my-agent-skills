---
name: video-download
description: |
  Download video and audio from YouTube and 1000+ sites using yt-dlp. No API keys needed.
  Use when: (1) Downloading a video from YouTube or other sites, (2) Extracting audio from a video URL,
  (3) Downloading subtitles/captions from a video, (4) Getting video metadata without downloading.
---

# video-download

Download video and audio from URLs using yt-dlp directly. No wrapper scripts needed.

## Quy định Session Directory (Bắt buộc)

Mọi hoạt động tải video, trích xuất âm thanh từ web, tải phụ đề hoặc lưu metadata phải được tổ chức trong session directory:
- **Thư mục gốc**: `./scratch/`
- **Cú pháp định danh**: `./scratch/yyyy-mm-dd_video-download_công-việc-viết-không-dấu`
  - *Ví dụ*: `./scratch/2026-09-22_video-download_download-b-roll-footage`
- **Cấu trúc thư mục con bắt buộc**:
  - `raw/` (hoặc `input/`): Chứa video/audio/phụ đề gốc tải về từ yt-dlp.
  - `output/`: Chứa file media hoàn chỉnh sau khi đổi tên chuẩn hoặc merge format để chuyển giao.
  - `scripts/`: Chứa danh sách URL (vd `urls.txt`), script tải hàng loạt (batch script).
  - `temp/`: Chứa fragments tải tạm, cache download (`--paths temp:...`), metadata json tạm.
- **Quy tắc cấm xả rác**: Tuyệt đối không chạy lệnh tải xả file trực tiếp ra root repo (`cwd` / `./downloads/` ở root). Phải luôn truyền `-o "$SESSION_DIR/output/%(title)s.%(ext)s"` (hoặc `$SESSION_DIR/raw/...`) và chỉ định thư mục tạm `--paths temp:"$SESSION_DIR/temp"`.

Khởi tạo cấu trúc session trước khi tải:
```bash
SESSION_DIR="./scratch/2026-09-22_video-download_download-b-roll-footage"
mkdir -p "$SESSION_DIR/raw" "$SESSION_DIR/output" "$SESSION_DIR/scripts" "$SESSION_DIR/temp"
```

## Commands

### Download best quality

```bash
yt-dlp "URL" -o "$SESSION_DIR/output/%(title)s.%(ext)s" --paths temp:"$SESSION_DIR/temp" --merge-output-format mp4
```

### Download specific resolution

```bash
# 720p
yt-dlp "URL" -f "bestvideo[height<=720]+bestaudio/best[height<=720]" -o "$SESSION_DIR/output/%(title)s.%(ext)s" --paths temp:"$SESSION_DIR/temp" --merge-output-format mp4

# 1080p
yt-dlp "URL" -f "bestvideo[height<=1080]+bestaudio/best[height<=1080]" -o "$SESSION_DIR/output/%(title)s.%(ext)s" --paths temp:"$SESSION_DIR/temp" --merge-output-format mp4
```

### Audio only

```bash
yt-dlp "URL" -x --audio-format mp3 --audio-quality 0 -o "$SESSION_DIR/output/%(title)s.%(ext)s" --paths temp:"$SESSION_DIR/temp"
```

### Download subtitles

```bash
# Download video with English subtitles
yt-dlp "URL" --write-subs --sub-langs en -o "$SESSION_DIR/output/%(title)s.%(ext)s" --paths temp:"$SESSION_DIR/temp" --merge-output-format mp4

# Download video with multiple subtitle languages
yt-dlp "URL" --write-subs --sub-langs "en,es,fr" -o "$SESSION_DIR/output/%(title)s.%(ext)s" --paths temp:"$SESSION_DIR/temp" --merge-output-format mp4

# Download only subtitles (no video)
yt-dlp "URL" --write-subs --sub-langs en -o "$SESSION_DIR/output/%(title)s.%(ext)s" --skip-download
```

### Get metadata (no download)

```bash
yt-dlp "URL" --dump-json --no-download > "$SESSION_DIR/temp/metadata.json"
```

### List available formats

```bash
yt-dlp "URL" -F
```

### Batch download from URL list

```bash
# Lưu danh sách URL vào $SESSION_DIR/scripts/urls.txt
yt-dlp -a "$SESSION_DIR/scripts/urls.txt" -o "$SESSION_DIR/output/%(title)s.%(ext)s" --paths temp:"$SESSION_DIR/temp" --merge-output-format mp4
```

## Quality Presets

| Quality | Format flag |
|---------|-------------|
| Best | `-f "bestvideo+bestaudio/best"` (default) |
| 1080p | `-f "bestvideo[height<=1080]+bestaudio/best[height<=1080]"` |
| 720p | `-f "bestvideo[height<=720]+bestaudio/best[height<=720]"` |
| 480p | `-f "bestvideo[height<=480]+bestaudio/best[height<=480]"` |
| Worst | `-f "worstvideo+worstaudio/worst"` |

## Output Template Variables

Common variables for `-o` templates:

| Variable | Description |
|----------|-------------|
| `%(title)s` | Video title |
| `%(ext)s` | File extension |
| `%(id)s` | Video ID |
| `%(uploader)s` | Channel/uploader name |
| `%(upload_date)s` | Upload date (YYYYMMDD) |
| `%(duration)s` | Duration in seconds |
| `%(resolution)s` | Video resolution |

## Tips

- Always use `--merge-output-format mp4` to avoid ending up with `.webm` or `.mkv` files.
- Use `--no-download` with `--dump-json` for metadata-only queries -- no files written to disk.
- If a download fails with HTTP errors, update yt-dlp first (`yt-dlp -U`).
- Use `-f "bestvideo[height<=720]+bestaudio"` to save bandwidth when full resolution is not needed.
- yt-dlp automatically handles rate limiting and retries.
- The `--dump-json` output includes `title`, `duration`, `uploader`, `view_count`, `description`, `formats`, `subtitles`, and much more.

## Troubleshooting

- **"yt-dlp: command not found"**: Install it (`pip install yt-dlp`) and ensure your PATH includes pip's bin directory.
- **"ffmpeg: command not found"**: Install ffmpeg. Without it, downloads fail when video and audio are separate streams (common on YouTube for HD).
- **Downloads fail or return errors**: Run `yt-dlp -U` to update. Sites change frequently and yt-dlp ships fixes regularly.
