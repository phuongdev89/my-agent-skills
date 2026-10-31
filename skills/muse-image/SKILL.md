---
name: muse-image
description: Tạo và chỉnh sửa ảnh qua gateway Muse2API (muse-image) — sinh ảnh, sinh ảnh có ảnh tham chiếu, sửa ảnh, tách/thử trang phục, xóa vật thể, thêm phụ kiện, thay nền; tự nạp cấu hình theo thứ tự .muse/config.json → biến môi trường → .env, hỗ trợ pin account_id qua X-Account-ID.
---

# Muse Image

Dùng skill này khi người dùng yêu cầu thao tác ảnh qua Muse2API. Đây là API gateway riêng; không phải Aidancing. Dựa theo API reference Muse2API v0.2.0, skill gọi gateway tại URL người dùng cấu hình và không đổi nhà cung cấp khi lỗi.

## Bước 1 — Cấu hình (làm trước tiên, bắt buộc)

Script tự đi tìm cấu hình theo thứ tự ưu tiên **từng trường gộp dần** (thiếu mục nào mới đi tìm mục đó ở nguồn sau):

1. **`<project>/.muse/config.json`** — file dùng chung với `muse-chat`; đã `config set` cho muse-chat một lần là skill này dùng luôn, không cần cấu hình lại.
2. **Biến môi trường** — `MUSE_ENDPOINT_URL`, `MUSE_API_KEY`, `MUSE_ACCOUNT_ID` (tên riêng của skill: `MUSEAI_IMAGE_*` làm dự phòng).
3. **`.env`** tại thư mục làm việc hoặc repo skill (đựng các key cùng tên, ưu tiên thấp nhất).

`account_id` (dạng `acc_…`, tùy chọn) cũng nạp theo đúng thứ tự trên, cộng thêm cờ `--account-id` trên từng lệnh (cao nhất, ghi đè mọi nguồn). Ý nghĩa theo API reference: pin request vào đúng một account trong pool và **tắt failover** — dùng khi muốn cố định quota/hồ sơ account. Không set thì gateway tự chọn account.

Kiểm tra nhanh đã đủ cấu hình chưa: chạy một lệnh generate thật nhỏ (xem Bước 3) — thiếu endpoint/key script thoát lỗi ngay với thông báo rõ. Script không có lệnh config riêng; muốn lưu cấu hình vào `.muse/config.json` thì dùng `muse_chat.py config set` (chia sẻ chung) hoặc tự đặt biến môi trường.

Endpoint chấp nhận URL gốc (`http://host:18610`, `.../v1`) lẫn URL chat (`.../v1/chat/completions`) — script tự chuẩn hóa về `/v1` cho API ảnh. Gửi key bằng `Authorization: Bearer ...`; không in key, không ghi key vào log, không đặt key trực tiếp trong lệnh. Không dùng admin key nếu chỉ cần gọi API ảnh.

## Chọn thao tác

- Tạo ảnh mới: `generate`, gửi prompt và tùy chọn model/kích thước; có thể kèm tới 4 ảnh tham chiếu (`--image`, lặp cờ) và `--background transparent` để nhận PNG nền trong suốt (cắt chủ thể cục bộ).
- Sửa ảnh hoặc chỉnh nhiều chi tiết: `edit`, cần ảnh nguồn và prompt.
- Tách trang phục khỏi người mẫu: `extract`, cần ảnh người mặc.
- Thử trang phục lên nhân vật: `try-on`, cần ảnh nhân vật và ảnh outfit, đúng thứ tự.
- Xóa vật thể: `remove`, cần ảnh nguồn; có thể thêm mask trắng/đen và prompt. Mask chỉ là hướng dẫn cho Muse, không bảo đảm inpainting chính xác từng pixel.
- Thêm phụ kiện: `accessory`, cần ảnh người và ảnh phụ kiện.
- Thay bối cảnh: `background`, cần ảnh chủ thể và ảnh nền.

Giữ nguyên ảnh gốc, chi tiết người dùng yêu cầu bảo toàn, và tỷ lệ nguồn cho các thao tác sửa. Theo API reference, `size` chỉ là gợi ý sinh ảnh: với edit dựa trên ảnh nguồn, Muse được hướng dẫn giữ nguyên kích thước/tỷ lệ nguồn; kết quả thực tế vẫn phụ thuộc upstream, không phải resize cứng.

## Chạy CLI

Script dùng thư viện chuẩn Python, không cần cài package. Đặt output trong session riêng, ví dụ `.scratch/yyyy-mm-dd_muse-image_ten-tac-vu/`; không ghi đè ảnh nguồn.

```bash
$SkillDir="<đường-dẫn-thư-mục-skill-muse-image>"
python "$SkillDir/scripts/muse_image.py" generate --prompt "Ảnh sản phẩm áo polo trên nền studio trắng" --size 1024x1024 --output .scratch/session/output.png
python "$SkillDir/scripts/muse_image.py" generate --prompt "Đặt chiếc túi lên tay người mẫu" --image .scratch/session/bag.jpg --image .scratch/session/model.jpg --output .scratch/session/ref.png
python "$SkillDir/scripts/muse_image.py" generate --prompt "Cắt chủ thể ra nền trong suốt" --background transparent --output .scratch/session/cutout.png
python "$SkillDir/scripts/muse_image.py" edit --image .scratch/session/input.png --prompt "Đổi áo sang màu xanh, giữ nguyên người mẫu" --output .scratch/session/edited.png
python "$SkillDir/scripts/muse_image.py" extract --image .scratch/session/person.jpg --output .scratch/session/outfit.png
python "$SkillDir/scripts/muse_image.py" try-on --character .scratch/session/person.jpg --outfit .scratch/session/outfit.png --output .scratch/session/try-on.png
python "$SkillDir/scripts/muse_image.py" remove --image .scratch/session/photo.jpg --prompt "Xóa chiếc chai trên bàn" --output .scratch/session/removed.png
python "$SkillDir/scripts/muse_image.py" accessory --image .scratch/session/person.jpg --accessory .scratch/session/glasses.png --prompt "Đeo kính lên mặt" --output .scratch/session/accessory.png
python "$SkillDir/scripts/muse_image.py" background --image .scratch/session/person.jpg --background-image .scratch/session/beach.jpg --prompt "Giữ người mẫu, khớp ánh sáng" --output .scratch/session/background.png
python "$SkillDir/scripts/muse_image.py" edit --image .scratch/session/input.png --prompt "Đổi áo sang màu xanh" --account-id acc_xxx --async --poll-interval 3 --output .scratch/session/edited.png
```

Chạy `python "$SkillDir/scripts/muse_image.py" --help` để xem đầy đủ tùy chọn. `generate` gọi JSON `POST /images/generations` (ảnh tham chiếu gửi dạng data URL trong body); `edit` gọi multipart `POST /images/edits`; các thao tác còn lại gọi endpoint multipart chuyên biệt. `--response-format` nhận `url` hoặc `b64_json` khi endpoint hỗ trợ. Thêm `--async` để nhận task rồi poll `/images/tasks/{id}` (fallback `/images/generations/{id}`) đến khi `succeeded`; timeout poll dùng `MUSEAI_IMAGE_TIMEOUT`. Mọi lệnh đều nhận `--account-id`.

## Xử lý kết quả và nghiệm thu

- Gateway trả ảnh đồng bộ hoặc task async theo API reference. Với task, script đối chiếu đúng `id`, poll đến trạng thái kết thúc, rồi tải ảnh từ `result.data[].url` hoặc giải mã `result.data[].b64_json` và ghi vào `--output`.
- Nếu nhận URL media tương đối, script ghép với origin của API (`/v1/media/{name}` phục vụ file không cần auth). Không gửi API key tới host khác nếu URL kết quả trỏ ra ngoài host gateway.
- Khi lỗi HTTP, hiển thị mã trạng thái và thông báo lỗi đã lọc; không in header xác thực.
- Sau khi chạy, xác nhận file tồn tại, mở được và xem ảnh để so với yêu cầu. Không coi HTTP thành công là nghiệm thu hình ảnh.
- Báo phương thức/endpoint, model nếu biết, đường dẫn output và mọi sai khác quan sát được. Không khẳng định tỷ lệ hay chi tiết đã đạt nếu chưa kiểm tra.

Tài liệu endpoint được mô tả trong API reference Muse2API: `/images/generations`, `/images/edits`, `/images/outfits/extract`, `/images/outfits/try-on`, `/images/objects/remove`, `/images/accessories/add`, `/images/background/replace`.
