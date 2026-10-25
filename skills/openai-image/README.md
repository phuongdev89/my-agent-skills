# OpenAI Image

Tạo và sửa ảnh với tool built-in của agent, sau đó API tương thích OpenAI khi cần theo [SKILL.md](SKILL.md).

Script [generate_image.py](scripts/generate_image.py) dùng thư viện chuẩn Python. Cấu hình qua biến môi trường hoặc `.env` trong thư mục làm việc:

| Biến | Ý nghĩa |
|---|---|
| `AI_IMAGE_KEY` | API key; alias `AI_IMAGE_API_KEY`, `AI_API_KEY` |
| `AI_IMAGE_URL` | Base URL gateway gồm `/v1`; alias `AI_IMAGE_ENDPOINT_URL`, `AI_BASE_URL`; bắt buộc khi gọi API |
| `AI_IMAGE_MODEL` | Model; alias `AI_MODEL`; mặc định `cx/gpt-5.6-sol-image` |
| `AI_IMAGE_TYPE` | `edit`, `9router` (generations), `response`; tự nhận diện từ URL nếu thiếu |
| `AI_TIMEOUT` | Timeout request, mặc định 300 giây |

```powershell
python skills/openai-image/scripts/generate_image.py --prompt "Ảnh sản phẩm trên nền studio" --aspect-ratio 9:16 --session-dir .scratch/demo
python skills/openai-image/scripts/generate_image.py --prompt "Giữ khuôn mặt theo [ATTACHED_PHOTO], đổi nền trắng" --ref-image .scratch/demo/input/person.png --output .scratch/demo/output/edited.png
python skills/openai-image/scripts/generate_image.py --dry-run
```

`--dry-run` chỉ kiểm tra cấu hình, không gọi API. Dùng `--help` để xem tham số. Xem [đặc tả gateway](references/openai_compat_spec.md) để chọn giao thức phù hợp; payload có các phần mở rộng tùy gateway.
