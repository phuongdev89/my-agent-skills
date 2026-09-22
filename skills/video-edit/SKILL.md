---
name: video-edit
description: |
  Edit videos locally using ffmpeg. Trim, concat, resize, speed, overlay, extract audio, compress, and convert.
  Use when: (1) Trimming or cutting video segments, (2) Concatenating multiple clips, (3) Resizing video for social platforms,
  (4) Extracting or replacing audio, (5) Compressing video, (6) Converting video formats, (7) Getting video info.
---

# Video Edit

Edit videos locally by running ffmpeg/ffprobe directly. No wrapper scripts needed.

## Quy định Session Directory (Bắt buộc)

Mọi hoạt động cắt, ghép, thay đổi tốc độ, nén, trích xuất âm thanh và đóng dấu watermark phải được cô lập trong session directory:
- **Thư mục gốc**: `./scratch/`
- **Cú pháp định danh**: `./scratch/yyyy-mm-dd_video-edit_công-việc-viết-không-dấu`
  - *Ví dụ*: `./scratch/2026-09-22_video-edit_cut-social-clips`
- **Cấu trúc thư mục con bắt buộc**:
  - `input/` (hoặc `raw/`): Chứa video gốc, file audio rời, watermark logo đầu vào.
  - `output/` (hoặc `exports/`): Chứa video thành phẩm đã biên tập (`trimmed.mp4`, `joined.mp4`, `tiktok.mp4`, `watermarked.mp4`).
  - `scripts/`: Chứa các kịch bản script cắt dựng tự động (vd `batch_trim.sh`).
  - `temp/`: Chứa danh sách ghép nối (`list.txt`), audio tạm, file trung gian.
- **Quy tắc cấm xả rác**: Tuyệt đối không xuất file kết quả hay file danh sách trung gian (`list.txt`) trực tiếp ra thư mục gốc (`cwd` / repo root). Mọi câu lệnh phải trỏ rõ vào `$SESSION_DIR`.

Khởi tạo session trước khi thực hiện:
```bash
SESSION_DIR="./scratch/2026-09-22_video-edit_cut-social-clips"
mkdir -p "$SESSION_DIR/input" "$SESSION_DIR/output" "$SESSION_DIR/scripts" "$SESSION_DIR/temp"
```

## Prerequisites

Install ffmpeg (includes ffprobe):

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install -y ffmpeg

# Verify
ffmpeg -version && ffprobe -version
```

## Quick Reference

### Get video info

```bash
ffprobe -v quiet -print_format json -show_format -show_streams "$SESSION_DIR/input/video.mp4"
```

### Trim

```bash
ffmpeg -y -ss 00:00:30 -to 00:01:45 -i "$SESSION_DIR/input/video.mp4" -c copy "$SESSION_DIR/output/trimmed.mp4"
```

### Concatenate clips

```bash
# 1. Create a file list in temp
printf "file '%s'\n" "$SESSION_DIR/input/clip1.mp4" "$SESSION_DIR/input/clip2.mp4" "$SESSION_DIR/input/clip3.mp4" > "$SESSION_DIR/temp/list.txt"

# 2. Concat with stream copy
ffmpeg -y -f concat -safe 0 -i "$SESSION_DIR/temp/list.txt" -c copy "$SESSION_DIR/output/joined.mp4"
```

### Resize for platform

```bash
ffmpeg -y -i "$SESSION_DIR/input/video.mp4" \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" \
  -c:a copy "$SESSION_DIR/output/tiktok.mp4"
```

### Change speed

```bash
# 2x faster
ffmpeg -y -i "$SESSION_DIR/input/video.mp4" -filter:v "setpts=0.5*PTS" -filter:a "atempo=2.0" "$SESSION_DIR/output/fast.mp4"

# 0.5x (slow motion)
ffmpeg -y -i "$SESSION_DIR/input/video.mp4" -filter:v "setpts=2.0*PTS" -filter:a "atempo=0.5" "$SESSION_DIR/output/slow.mp4"
```

### Extract audio

```bash
ffmpeg -y -i "$SESSION_DIR/input/video.mp4" -vn -acodec libmp3lame "$SESSION_DIR/output/audio.mp3"
```

### Replace audio

```bash
ffmpeg -y -i "$SESSION_DIR/input/video.mp4" -i "$SESSION_DIR/input/audio.mp3" -c:v copy -map 0:v:0 -map 1:a:0 -shortest "$SESSION_DIR/output/output.mp4"
```

### Compress

```bash
ffmpeg -y -i "$SESSION_DIR/input/video.mp4" -crf 23 -preset medium -c:a copy "$SESSION_DIR/output/compressed.mp4"
```

### Convert format

```bash
ffmpeg -y -i "$SESSION_DIR/input/video.mov" "$SESSION_DIR/output/output.mp4"
```

### Add image overlay

```bash
# Logo in top-right corner
ffmpeg -y -i "$SESSION_DIR/input/video.mp4" -i "$SESSION_DIR/input/logo.png" \
  -filter_complex "overlay=W-w-10:10" -c:a copy "$SESSION_DIR/output/watermarked.mp4"
```

## Platform Presets

| Platform   | Resolution  | Scale + pad filter                                                                                    |
|------------|-------------|-------------------------------------------------------------------------------------------------------|
| TikTok     | 1080 x 1920 | `scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black`       |
| YouTube    | 1920 x 1080 | `scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black`       |
| Instagram  | 1080 x 1350 | `scale=1080:1350:force_original_aspect_ratio=decrease,pad=1080:1350:(ow-iw)/2:(oh-ih)/2:black`       |
| Square     | 1080 x 1080 | `scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2:black`       |
| Twitter/X  | 1920 x 1080 | `scale=1920:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2:black`       |

Use the filter with: `ffmpeg -y -i "$SESSION_DIR/input/input.mp4" -vf "<filter>" -c:a copy "$SESSION_DIR/output/output.mp4"`

## Tips

- Always use `-y` to overwrite output without prompting.
- Use `-c copy` when you only need to cut/join (no re-encoding, very fast).
- Lower CRF = better quality, larger file. Range 18-28 is typical; 23 is the default.
- For detailed recipes and flag explanations, see `references/operations.md`.
