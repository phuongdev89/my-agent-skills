---
name: muse-image
description: Tạo và chỉnh sửa ảnh qua Muse2API, gồm sinh ảnh, sửa ảnh, tách/thử trang phục, xóa vật thể, thêm phụ kiện và thay nền.
---

# Muse Image

Dùng skill này khi người dùng yêu cầu thao tác ảnh qua Muse2API. Đây là API gateway riêng; không phải Aidancing. Dựa theo API reference Muse2API, skill gọi gateway tại URL người dùng cấu hình và không đổi nhà cung cấp khi lỗi.

## Chọn thao tác

- Tạo ảnh mới: `generate`, gửi prompt và tùy chọn model/kích thước.
- Sửa ảnh hoặc chỉnh nhiều chi tiết: `edit`, cần ảnh nguồn và prompt.
- Tách trang phục khỏi người mẫu: `extract`, cần ảnh người mặc.
- Thử trang phục lên nhân vật: `try-on`, cần ảnh nhân vật và ảnh outfit, đúng thứ tự.
- Xóa vật thể: `remove`, cần ảnh nguồn; có thể thêm mask trắng/đen và prompt. Mask chỉ là hướng dẫn cho Muse, không bảo đảm inpainting chính xác từng pixel.
- Thêm phụ kiện: `accessory`, cần ảnh người và ảnh phụ kiện.
- Thay bối cảnh: `background`, cần ảnh chủ thể và ảnh nền.

Giữ nguyên ảnh gốc, chi tiết người dùng yêu cầu bảo toàn, và tỷ lệ nguồn cho các thao tác sửa. Với endpoint edit chuyên biệt, API hướng dẫn giữ cả chiều rộng và chiều cao ảnh nguồn; đây là chỉ dẫn cho Muse, kết quả thực tế vẫn phụ thuộc upstream.

## Cấu hình

Đọc `.env` tại thư mục làm việc hoặc biến môi trường:

- `MUSE_ENDPOINT_URL`: dùng chung với `muse-chat`; chấp nhận URL gốc (`http://127.0.0.1:18610` hoặc `.../v1`) và URL chat (`.../v1/chat/completions`). Script tự chuẩn hóa về `/v1` cho API ảnh.
- `MUSE_API_KEY`: client API key có quyền `/v1/*`, dùng chung với `muse-chat`.
- `MUSEAI_IMAGE_MODEL`: tùy chọn, mặc định `muse-image`.
- `MUSEAI_IMAGE_TIMEOUT`: tùy chọn, mặc định 600 giây.
- `MUSEAI_IMAGE_POLL_INTERVAL`: tùy chọn, mặc định 2 giây khi poll task async.

Biến môi trường ưu tiên hơn `.env` cùng tên; `.env` tại thư mục làm việc ưu tiên hơn `.env` trong repo skill. Hai tên mới ưu tiên hơn tên cũ `MUSEAI_IMAGE_ENDPOINT_URL` / `MUSEAI_IMAGE_API_KEY` (vẫn hỗ trợ làm dự phòng từng trường). Chỉ hỏi thông tin còn thiếu khi các nguồn này chưa đủ; không in giá trị key khi kiểm tra cấu hình.

Gửi key bằng `Authorization: Bearer ...`. Không in key, ghi key vào log, hoặc đặt key trực tiếp trong lệnh. Không dùng admin key nếu chỉ cần gọi API ảnh.

## Chạy CLI

Script dùng thư viện chuẩn Python, không cần cài package. Đặt output trong session riêng, ví dụ `.scratch/yyyy-mm-dd_muse-image_ten-tac-vu/`; không ghi đè ảnh nguồn.

```powershell
$SkillDir = "<đường-dẫn-thư-mục-skill-muse-image>"
python "$SkillDir/scripts/muse_image.py" generate --prompt "Ảnh sản phẩm áo polo trên nền studio trắng" --size 1024x1024 --output ".scratch/session/output.png"
python "$SkillDir/scripts/muse_image.py" edit --image ".scratch/session/input.png" --prompt "Đổi áo sang màu xanh, giữ nguyên người mẫu" --output ".scratch/session/edited.png"
python "$SkillDir/scripts/muse_image.py" extract --image ".scratch/session/person.jpg" --output ".scratch/session/outfit.png"
python "$SkillDir/scripts/muse_image.py" try-on --character ".scratch/session/person.jpg" --outfit ".scratch/session/outfit.png" --output ".scratch/session/try-on.png"
python "$SkillDir/scripts/muse_image.py" remove --image ".scratch/session/photo.jpg" --prompt "Xóa chiếc chai trên bàn" --output ".scratch/session/removed.png"
python "$SkillDir/scripts/muse_image.py" accessory --image ".scratch/session/person.jpg" --accessory ".scratch/session/glasses.png" --prompt "Đeo kính lên mặt" --output ".scratch/session/accessory.png"
python "$SkillDir/scripts/muse_image.py" background --image ".scratch/session/person.jpg" --background-image ".scratch/session/beach.jpg" --prompt "Giữ người mẫu, khớp ánh sáng" --output ".scratch/session/background.png"
python "$SkillDir/scripts/muse_image.py" edit --image ".scratch/session/input.png" --prompt "Đổi áo sang màu xanh" --async --poll-interval 3 --output ".scratch/session/edited.png"
```

Chạy `python "$SkillDir/scripts/muse_image.py" --help` để xem đầy đủ tùy chọn. `generate` gọi JSON `POST /images/generations`; `edit` gọi multipart `POST /images/edits`; các thao tác còn lại gọi endpoint multipart chuyên biệt theo API reference. `--response-format` nhận `url` hoặc `b64_json` khi endpoint hỗ trợ. Thêm `--async` để nhận task rồi poll `/images/tasks/{id}` (fallback `/images/generations/{id}`) đến khi `succeeded`; timeout poll dùng `MUSEAI_IMAGE_TIMEOUT`.

## Xử lý kết quả và nghiệm thu

- Gateway trả ảnh đồng bộ hoặc task async theo API reference. Với task, script đối chiếu đúng `id`, poll đến trạng thái kết thúc, rồi tải ảnh từ `result.data[].url` hoặc giải mã `result.data[].b64_json` và ghi vào `--output`.
- Nếu nhận URL media tương đối, script ghép với origin của API. Không gửi API key tới host khác nếu URL kết quả trỏ ra ngoài host gateway.
- Khi lỗi HTTP, hiển thị mã trạng thái và thông báo lỗi đã lọc; không in header xác thực.
- Sau khi chạy, xác nhận file tồn tại, mở được và xem ảnh để so với yêu cầu. Không coi HTTP thành công là nghiệm thu hình ảnh.
- Báo phương thức/endpoint, model nếu biết, đường dẫn output và mọi sai khác quan sát được. Không khẳng định tỷ lệ hay chi tiết đã đạt nếu chưa kiểm tra.

Tài liệu endpoint được mô tả trong API reference Muse2API: `/images/generations`, `/images/edits`, `/images/outfits/extract`, `/images/outfits/try-on`, `/images/objects/remove`, `/images/accessories/add`, `/images/background/replace`.
