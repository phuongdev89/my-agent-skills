# Image Generate Skill (Project Providers & Google AI Studio Direct)

Kỹ năng tạo và chỉnh sửa hình ảnh chuyên nghiệp phục vụ chu trình sản xuất video ngắn chuẩn phong cách KOC (YouTube Shorts, TikTok, Instagram Reels), tối ưu hóa tỷ lệ dọc 9:16, bảo toàn chân dung KOC và chi tiết phom dáng sản phẩm thương mại.

Module vận hành đồng bộ với kiến trúc tạo ảnh của dự án `ai_prompts_database`:
1. **Project Provider: OpenAI Edits API (`AI_IMAGE_TYPE=edit`)**: Gọi endpoint `/images/edits` (ZPro / OpenAI chuẩn), hỗ trợ mảng `images` với ID `input_file_0.png` và token `[ATTACHED_PHOTO]`.
2. **Project Provider: OpenAI Generations API (`AI_IMAGE_TYPE=9router`)**: Gọi endpoint `/images/generations` (9router), hỗ trợ trường phẳng `image`.
3. **Project Provider: Multimodal Responses API (`AI_IMAGE_TYPE=response`)**: Gọi endpoint `/responses` (OmniRoute), đóng gói `input_image` + `input_text` và `tool_choice: image_generation`.
4. **Google AI Studio Direct (`--use-gemini` hoặc key `AIzaSy...`)**: Gọi trực tiếp API chính hãng của Google Generative Language với model Imagen (`imagen-3.0-generate-002`).

---

## 1. Đặc Tính Kỹ Thuật (Zero Dependencies)

- **100% Pure Python**: Chỉ sử dụng thư viện chuẩn (`urllib`, `base64`, `json`, `pathlib`, `ssl`, `mimetypes`, `argparse`, `re`).
- **Auto-Detection**: Tự động nhận diện cấu hình trong `.env` (`AI_IMAGE_KEY`, `AI_IMAGE_URL`, `AI_IMAGE_MODEL`, `AI_IMAGE_TYPE`), không yêu cầu người dùng cấu hình thủ công lại.
- **Cô lập phiên làm việc**: Toàn bộ dữ liệu sinh ảnh được cô lập trong thư mục `./.scratch/`.

---

## 2. Ma Trận Biến Môi Trường (.env)

Hệ thống ưu tiên đọc các biến môi trường chuẩn của dự án:

| Tên biến môi trường | Kiểu dữ liệu | Mặc định | Mô tả chi tiết |
|---|---|---|---|
| `AI_IMAGE_KEY` | `string` | Bắt buộc | Khóa API Key (ZPro, 9router, OmniRoute hoặc Google AI Studio `AIzaSy...`). Fallback: `AI_IMAGE_API_KEY`. |
| `AI_IMAGE_URL` | `string` (URL) | `https://api.opanai.com/v1` | Base URL của dịch vụ upstream. Fallback: `AI_IMAGE_ENDPOINT_URL`. |
| `AI_IMAGE_MODEL` | `string` | `gpt-image-2` | Tên model tạo ảnh (ví dụ: `gpt-image-2`, `cx/gpt-5.6-sol-image`, `imagen-3.0-generate-002`). |
| `AI_IMAGE_TYPE` | `string` | `edit` | Provider type của project: `edit` (ZPro Edits), `9router` (Generations), `response` (OmniRoute). |
| `AI_IMAGE_USE_GEMINI` | `boolean` | `false` | Đặt `true` để ép buộc gọi trực tiếp Google AI Studio API. |
| `AI_TIMEOUT` | `integer` | `300` | Thời gian chờ tối đa cho mỗi request (giây). |

---

## 3. Cấu Trúc Thư Mục Phiên Làm Việc (.scratch/)

Mọi thao tác tạo ảnh đều được lưu trong `.scratch/`:
```text
./.scratch/yyyy-mm-dd_image-generate_tên-tác-vụ/
├── input/      # Chứa ảnh tham chiếu (chân dung KOC, ảnh sản phẩm)
├── output/     # Chứa ảnh thành phẩm (visual.png, scene_01.png)
├── scripts/    # Chứa script tùy biến nếu có
└── temp/       # Payload JSON tạm, base64 data
```

---

## 4. Hướng Dẫn CLI Script (`generate_image.py`)

Script vị trí tại: [generate_image.py](scripts/generate_image.py)

### Bảng tham số chính:
- `--prompt`, `-p`: Câu lệnh mô tả bức ảnh cần tạo.
- `--prompt-file`: File `.txt` chứa prompt dài.
- `--aspect-ratio`: Tỷ lệ khung hình: `9:16`, `16:9`, `1:1`, `3:4`, `4:3`, `2:3`, `3:2`.
- `--size`: Kích thước pixel cụ thể (hoặc `auto`).
- `--ref-image`, `-i`: Đường dẫn file ảnh tham chiếu (Image-to-Image / Khóa nhận diện).
- `--model`, `-m`: Ghi đè tên model trong `.env`.
- `--image-type`, `-t`: Ghi đè provider (`edit`, `9router`, `response`).
- `--use-gemini`: Kích hoạt gọi Google AI Studio API.
- `--dry-run`: Kiểm tra cấu hình và xem trước payload không gọi API thực tế.
- `--session-dir`: Chỉ định thư mục session trong `.scratch/`.
- `--output`, `-o`: Chỉ định file kết quả đầu ra.

### Ví dụ thực tế:

```bash
# 1. Chạy Text-to-Image tự động detect cấu hình .env
python .claude/skills/image-generate/scripts/generate_image.py \
  --prompt "Chân dung KOC nữ người Việt 22 tuổi nụ cười tươi tắn, mặc áo polo pique cotton màu be" \
  --aspect-ratio "9:16" \
  --session-dir "./.scratch/2026-10-04_demo_koc"

# 2. Sinh ảnh giữ nét khuôn mặt với ảnh tham chiếu
python .claude/skills/image-generate/scripts/generate_image.py \
  --prompt "KOC nữ diện mạo theo [ATTACHED_PHOTO] đang cầm giới thiệu áo polo màu be" \
  --ref-image "./.scratch/2026-10-04_demo_koc/input/koc_face.jpg" \
  --aspect-ratio "9:16" \
  --session-dir "./.scratch/2026-10-04_demo_koc" \
  --output "./.scratch/2026-10-04_demo_koc/output/scene_01.png"

# 3. Chạy trực tiếp Google AI Studio Imagen-3
python .claude/skills/image-generate/scripts/generate_image.py \
  --prompt "Sản phẩm áo polo chụp flat-lay phong cách studio" \
  --aspect-ratio "1:1" \
  --use-gemini \
  --model "imagen-3.0-generate-002" \
  --session-dir "./.scratch/2026-10-04_demo_product"
```
