---
name: openai-image
description: Tạo và sửa ảnh raster, chân dung KOC và sản phẩm bằng tool built-in của agent hoặc API tương thích OpenAI cấu hình trong dự án.
---

# OpenAI Image

## 1. Nhận diện yêu cầu trước khi chọn công cụ

Đọc yêu cầu và xem ảnh nguồn để xác định kết quả người dùng muốn:
- **Tạo ảnh**: tạo hình ảnh mới từ mô tả; ảnh tham chiếu có thể dùng để giữ nhận diện/phong cách.
- **Sửa ảnh**: thay đổi hoặc bóc tách nội dung từ ảnh có sẵn. Bóc outfit từ ảnh người mẫu là sửa ảnh, không phải đổi trang phục.
- Với sửa ảnh, ghi nhận phần cần thay đổi và phần cần giữ (khuôn mặt, nhân vật, sản phẩm, màu sắc, phom dáng). Không chỉ chọn thao tác theo một từ khóa.
- Dùng thông số người dùng đã cung cấp; chỉ hỏi khi thiếu ảnh đầu vào hoặc mục tiêu còn mơ hồ. Giữ tỷ lệ ảnh nguồn khi sửa; mặc định 9:16 cho ảnh mới phục vụ video ngắn, chất lượng auto. Giữ nhận diện khi được yêu cầu hoặc khi sửa phần khác của ảnh nhân vật.

## 2. Thứ tự ưu tiên bắt buộc

| Nhu cầu | Bước 1 | Bước 2 |
|---|---|---|
| Tạo ảnh | Tool tạo ảnh built-in của agent | Nếu không tồn tại: API từ `.env` của người dùng |
| Sửa ảnh | Tool sửa ảnh built-in của agent | Nếu không tồn tại hoặc bị chặn: API từ `.env` của người dùng |

- Kiểm tra tool thực sự được cung cấp trong phiên và khả năng tạo/sửa ảnh; không giả định tên tool cố định. Ví dụ `image_gen.imagegen` hoặc `generate_image` nếu host cung cấp. Tool tích hợp hỗ trợ cả hai tác vụ vẫn là built-in ưu tiên đầu tiên.
- Nếu built-in khả dụng, gọi trực tiếp theo hợp đồng tool của host. Với sửa ảnh, truyền ảnh nguồn thực tế, không chỉ mô tả lại ảnh bằng chữ. Không đọc `.env` để chuyển qua API trước khi thử built-in.
- Khi chuyển tầng, thông báo ngắn lý do và giữ nguyên mục tiêu, prompt, ảnh nguồn, tỷ lệ, chất lượng đã chọn. Không tự sửa yêu cầu để né giới hạn nội dung. Nếu yêu cầu bị cấm bởi chính sách an toàn áp dụng cho agent, dừng hoặc đề xuất phương án phù hợp; không dùng provider khác để vượt lệnh cấm đó.
- Phân biệt lỗi dịch vụ/quota/quyền truy cập với thiếu file, sai tham số, cấu hình sai hoặc timeout. Sửa lỗi đầu vào/cấu hình tại tầng hiện tại; không coi mọi lỗi là bị chặn. Không retry vô hạn hoặc gửi lại job khi chưa biết job cũ đã được nhận chưa.
- Nếu thiếu cấu hình API, báo thiếu cấu hình và yêu cầu người dùng bổ sung; không tự coi thiếu `.env` là API đã bị chặn.

## 3. API từ `.env` (chỉ đọc khi tới tầng API)

Chạy [scripts/generate_image.py](scripts/generate_image.py) từ thư mục dự án của người dùng để ưu tiên `.env` tại cwd. Không lấy cấu hình từ một dự án khác, không in key hoặc toàn bộ `.env`.

- `AI_IMAGE_KEY` (alias `AI_IMAGE_API_KEY`), `AI_IMAGE_URL` (alias `AI_IMAGE_ENDPOINT_URL`), `AI_IMAGE_MODEL`.
- `AI_IMAGE_TYPE`: `edit` → `/images/edits`, `9router` → `/images/generations`, `response` → `/responses`. Đây là kiểu giao thức API, không phải phân loại ý định tạo/sửa ảnh.
- Với sửa ảnh/giữ nhận diện: truyền `--ref-image`; provider edit hỗ trợ placeholder `[ATTACHED_PHOTO]`.
- `--dry-run` kiểm tra cấu hình/payload mà không gọi provider, không chứng minh tạo/sửa ảnh thành công.

Ví dụ PowerShell (đặt `$SkillDir` thành đường dẫn thư mục chứa SKILL.md đang sử dụng, `$SessionDir` thành session của tác vụ):

```powershell
python "$SkillDir/scripts/generate_image.py" --prompt "Chân dung KOC nữ mặc áo polo" --aspect-ratio "9:16" --session-dir "$SessionDir"
python "$SkillDir/scripts/generate_image.py" --prompt "Giữ khuôn mặt theo [ATTACHED_PHOTO], đổi nền thành studio trắng" --ref-image "$SessionDir/input/person.png" --session-dir "$SessionDir" --output "$SessionDir/output/edited.png"
python "$SkillDir/scripts/generate_image.py" --prompt "Kiểm tra cấu hình" --dry-run
```

## 4. Lưu file và nghiệm thu

- Giữ nguyên ảnh gốc; dùng session `./.scratch/yyyy-mm-dd_openai-image_ten-tac-vu/` với `input/`, `output/`, `scripts/`, `temp/`. Đảm bảo thư mục tạm được gitignore trước khi tạo script tạm.
- Với built-in, tuân thủ nơi lưu của host rồi sao chép kết quả vào session nếu có file truy cập được. Trả ảnh trực tiếp theo hợp đồng tool khi tool đã hiển thị ảnh.
- Kiểm tra file tồn tại, mở được và xem ảnh để đối chiếu mục tiêu/nhận diện/chi tiết sản phẩm. Không nghiệm thu chỉ dựa trên thông báo COMPLETED.
- Trả ảnh hoặc link file, phương thức thực tế, model nếu biết, kích thước/tỷ lệ/dung lượng nếu đo được, và prompt thực tế trong khối `text`. Không tự đặt tên model hoặc khẳng định chất lượng chưa kiểm tra.

Đọc thêm khi cần: [prompting_guide.md](references/prompting_guide.md) cho prompt KOC/sản phẩm; [openai_compat_spec.md](references/openai_compat_spec.md) cho giao thức API tương thích.
