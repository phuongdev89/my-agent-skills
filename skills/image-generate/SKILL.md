---
name: image-generate
description: Generate or edit raster images, KOC portraits, products and outfits. Detect the requested task, prefer the agent's built-in image tool, then the user's configured API; use Aidancing scripts as an editing fallback for general edits, object removal, background changes, outfit swaps and accessories.
---

# Image Generate

## 1. Nhận diện yêu cầu trước khi chọn công cụ

Đọc yêu cầu và xem ảnh nguồn để xác định kết quả người dùng muốn:
- **Tạo ảnh**: tạo hình ảnh mới từ mô tả; ảnh tham chiếu có thể dùng để giữ nhận diện/phong cách.
- **Sửa ảnh**: thay đổi hoặc bóc tách nội dung từ ảnh có sẵn. Bóc outfit từ ảnh người mẫu là sửa ảnh, không phải đổi trang phục.
- Với sửa ảnh, ghi nhận phần cần thay đổi và phần cần giữ (khuôn mặt, nhân vật, sản phẩm, màu sắc, phom dáng). Không chỉ chọn thao tác theo một từ khóa.
- Dùng thông số người dùng đã cung cấp; chỉ hỏi khi thiếu ảnh đầu vào hoặc mục tiêu còn mơ hồ. Giữ tỷ lệ ảnh nguồn khi sửa; mặc định 9:16 cho ảnh mới phục vụ video ngắn, chất lượng auto. Giữ nhận diện khi được yêu cầu hoặc khi sửa phần khác của ảnh nhân vật.

## 2. Thứ tự ưu tiên bắt buộc

| Nhu cầu | Bước 1 | Bước 2 | Bước 3 |
|---|---|---|---|
| Tạo ảnh | Tool tạo ảnh built-in của agent | Nếu không tồn tại: API từ `.env` của người dùng | Không dùng Aidancing để tạo ảnh mới |
| Sửa ảnh | Tool sửa ảnh built-in của agent | Nếu không tồn tại hoặc bị chặn: API từ `.env` của người dùng | Nếu API vẫn bị chặn: phân loại thao tác và dùng Aidancing |

- Kiểm tra tool thực sự được cung cấp trong phiên và khả năng tạo/sửa ảnh; không giả định tên tool cố định. Ví dụ `image_gen.imagegen` hoặc `generate_image` nếu host cung cấp. Tool tích hợp hỗ trợ cả hai tác vụ vẫn là built-in ưu tiên đầu tiên.
- Nếu built-in khả dụng, gọi trực tiếp theo hợp đồng tool của host. Với sửa ảnh, truyền ảnh nguồn thực tế, không chỉ mô tả lại ảnh bằng chữ. Không đọc `.env` để chuyển qua API trước khi thử built-in.
- Khi chuyển tầng, thông báo ngắn lý do và giữ nguyên mục tiêu, prompt, ảnh nguồn, tỷ lệ, chất lượng đã chọn. Không tự sửa yêu cầu để né giới hạn nội dung. Nếu yêu cầu bị cấm bởi chính sách an toàn áp dụng cho agent, dừng hoặc đề xuất phương án phù hợp; không dùng provider khác để vượt lệnh cấm đó.
- Phân biệt lỗi dịch vụ/quota/quyền truy cập với thiếu file, sai tham số, cấu hình sai hoặc timeout. Sửa lỗi đầu vào/cấu hình tại tầng hiện tại; không coi mọi lỗi là bị chặn. Không retry vô hạn hoặc gửi lại job khi chưa biết job cũ đã được nhận chưa.
- Nếu thiếu cấu hình API, báo thiếu cấu hình và yêu cầu người dùng bổ sung; không tự coi thiếu `.env` là API đã bị chặn.

## 3. API từ `.env` (chỉ đọc khi tới tầng API)

Chạy [scripts/generate_image.py](scripts/generate_image.py) từ thư mục dự án của người dùng để ưu tiên `.env` tại cwd. Không lấy cấu hình từ một dự án khác, không in key hoặc toàn bộ `.env`.

- `AI_IMAGE_KEY` (alias `AI_IMAGE_API_KEY`), `AI_IMAGE_URL` (alias `AI_IMAGE_ENDPOINT_URL`), `AI_IMAGE_MODEL`.
- `AI_IMAGE_TYPE`: `edit` → `/images/edits`, `9router` → `/images/generations`, `response` → `/responses`. Đây là kiểu giao thức API, không phải phân loại ý định tạo/sửa ảnh.
- Google AI Studio được script phát hiện qua `AI_IMAGE_USE_GEMINI=true`, key dạng `AIza...`, model `imagen-...`, hoặc cờ `--use-gemini`. Chỉ dùng cấu hình phù hợp tác vụ; không dùng provider chỉ tạo mới để thay thế sửa ảnh cần giữ nguồn.
- Với sửa ảnh/giữ nhận diện: truyền `--ref-image`; provider edit hỗ trợ placeholder `[ATTACHED_PHOTO]`.
- `--dry-run` kiểm tra cấu hình/payload mà không gọi provider, không chứng minh tạo/sửa ảnh thành công.

Ví dụ PowerShell (đặt `$SkillDir` thành đường dẫn thư mục chứa SKILL.md đang sử dụng, `$SessionDir` thành session của tác vụ):

```powershell
python "$SkillDir/scripts/generate_image.py" --prompt "Chân dung KOC nữ mặc áo polo" --aspect-ratio "9:16" --session-dir "$SessionDir"
python "$SkillDir/scripts/generate_image.py" --prompt "Giữ khuôn mặt theo [ATTACHED_PHOTO], đổi nền thành studio trắng" --ref-image "$SessionDir/input/person.png" --session-dir "$SessionDir" --output "$SessionDir/output/edited.png"
python "$SkillDir/scripts/generate_image.py" --prompt "Kiểm tra cấu hình" --dry-run
```

## 4. Aidancing: phân tích lại thao tác sửa ảnh

Chỉ tới bước này khi sửa ảnh đã đi qua thứ tự fallback trên. Các script gọi `https://image.aidancing.net` bằng `requests`, không đi qua `generate_image.py` và không dùng cấu hình API ảnh trong `.env`. Đọc script liên quan trước khi chạy; nếu runtime thiếu `requests`, cài bằng `python -m pip install requests` trong môi trường đang sử dụng.

| Mục tiêu thực tế | Script trong `scripts/aidancing/` | Đầu vào CLI |
|---|---|---|
| Sửa tổng quát, chỉnh nhiều thành phần, bóc outfit ra ảnh riêng | `aidancing_edit.py` | `image prompt -o output` |
| Xóa vật thể cụ thể, giữ phần còn lại | `aidancing_delete_object.py` | `image prompt -o output` |
| Đổi bối cảnh theo ảnh nền mới | `aidancing_bg_swap.py` | `subject background -p prompt -o output` |
| Mặc trang phục mẫu lên nhân vật | `aidancing_outfit_swap.py` | `person outfit -p prompt -o output` |
| Thêm phụ kiện mẫu lên nhân vật | `aidancing_add_accessory.py` | `person accessory -p prompt -o output` |

Ba script swap/accessory cần **hai ảnh**, theo đúng thứ tự trong bảng. Nếu chỉ có một ảnh và yêu cầu thay đổi bằng mô tả, dùng `aidancing_edit.py`; nếu cần khớp chính xác mẫu chưa có thì yêu cầu ảnh mẫu. Không truyền cùng một ảnh giả làm hai đầu vào. Yêu cầu phối hợp nhiều chỉnh sửa ưu tiên edit với prompt đầy đủ; chỉ tách bước nếu cần và dùng kết quả bước trước làm nguồn cho bước sau.

**Ví dụ bóc outfit từ một ảnh có sẵn:** chọn `aidancing_edit.py`, không chọn `aidancing_outfit_swap.py` hoặc chỉ xóa người bằng delete_object. Prompt:

```text
xoá bối cảnh, xoá nhân vật, bóc tách outfit ra ảnh riêng nền trắng
```

```powershell
python "$SkillDir/scripts/aidancing/aidancing_edit.py" "$SessionDir/input/source.png" "xoá bối cảnh, xoá nhân vật, bóc tách outfit ra ảnh riêng nền trắng" -o "$SessionDir/output/outfit.png"
python "$SkillDir/scripts/aidancing/aidancing_delete_object.py" "$SessionDir/input/source.png" "xoá cái chai nước, giữ nguyên phần còn lại" -o "$SessionDir/output/clean.png"
python "$SkillDir/scripts/aidancing/aidancing_bg_swap.py" "$SessionDir/input/person.png" "$SessionDir/input/background.png" -p "Giữ nguyên nhân vật, khớp ánh sáng nền mới" -o "$SessionDir/output/background.png"
python "$SkillDir/scripts/aidancing/aidancing_outfit_swap.py" "$SessionDir/input/person.png" "$SessionDir/input/outfit.png" -p "Giữ nguyên khuôn mặt và chi tiết trang phục mẫu" -o "$SessionDir/output/dressed.png"
python "$SkillDir/scripts/aidancing/aidancing_add_accessory.py" "$SessionDir/input/person.png" "$SessionDir/input/accessory.png" -p "Thêm phụ kiện đúng vị trí, giữ nguyên nhân vật" -o "$SessionDir/output/accessorized.png"
```

Các script hiện poll `jobs[0]` theo loại job, chưa đối chiếu job ID. Chạy tuần tự trong cùng session dịch vụ; không chạy batch song song và kiểm tra ảnh trả về đúng yêu cầu. Nếu Aidancing thất bại, báo lỗi thực tế và dừng.

## 5. Lưu file và nghiệm thu

- Giữ nguyên ảnh gốc; dùng session `./.scratch/yyyy-mm-dd_image-generate_ten-tac-vu/` với `input/`, `output/`, `scripts/`, `temp/`. Đảm bảo thư mục tạm được gitignore trước khi tạo script tạm.
- Tạo thư mục output trước khi chạy Aidancing và luôn truyền `-o` để không lưu cạnh ảnh gốc. Script Aidancing không có `--session-dir`, `--aspect-ratio` hoặc `--quality`; không truyền cờ không hỗ trợ.
- Với built-in, tuân thủ nơi lưu của host rồi sao chép kết quả vào session nếu có file truy cập được. Trả ảnh trực tiếp theo hợp đồng tool khi tool đã hiển thị ảnh.
- Kiểm tra file tồn tại, mở được và xem ảnh để đối chiếu mục tiêu/nhận diện/chi tiết sản phẩm. Không nghiệm thu chỉ dựa trên thông báo COMPLETED.
- Trả ảnh hoặc link file, phương thức thực tế, model nếu biết, kích thước/tỷ lệ/dung lượng nếu đo được, và prompt thực tế trong khối `text`. Không tự đặt tên model hoặc khẳng định chất lượng chưa kiểm tra.

Đọc thêm khi cần: [prompting_guide.md](references/prompting_guide.md) cho prompt KOC/sản phẩm; [openai_compat_spec.md](references/openai_compat_spec.md) cho giao thức API tương thích.
