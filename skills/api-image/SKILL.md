---
name: api-image
description: Tạo và sửa ảnh qua API gateway 9router hoặc sub2api với cấu hình API_IMAGE_* riêng trong .env, hỗ trợ fallback có giới hạn. Dùng khi người dùng chọn API hoặc image-generate chuyển sang API.
---

# API Image

Chạy [scripts/generate_image.py](scripts/generate_image.py) bằng Python từ thư mục dự án người dùng. Script chỉ dùng thư viện chuẩn, đọc `.env` tại cwd và biến môi trường (biến môi trường ưu tiên); không đọc cấu hình dự án khác và không sửa `.env` khi fallback.

## Cấu hình và định tuyến

Xem [.env.example](.env.example). `API_IMAGE_PROVIDER=9router|sub2api` là chuỗi ưu tiên trái sang phải, mỗi provider tối đa một lần; dùng `9router` hoặc `sub2api` để chỉ chọn một gateway. Khi có biến `API_IMAGE_*` nhưng thiếu selector, mặc định `9router|sub2api`. URL/key/model của mỗi gateway lấy riêng, không mượn từ gateway khác hay biến legacy. Tên gateway độc lập với người bán, có thể thay URL sub2api sang người bán khác.

- `API_IMAGE_NINEROUTER_URL/KEY/MODEL`: cấu hình 9router, gọi `/images/generations`; ảnh tham chiếu được gửi trong trường `image` theo giao thức gateway hiện có.
- `API_IMAGE_SUB2API_URL/KEY/MODEL`: cấu hình sub2api. Có `--ref-image` → `/images/edits` với file ảnh multipart; không có → `/images/generations` JSON. Không dùng endpoint generations cho ảnh tham chiếu sub2api.
- `API_IMAGE_TIMEOUT`: timeout giây, mặc định 300.
- Giữ các cờ CLI hiện có: `--prompt`, `--prompt-file`, `--aspect-ratio`, `--size`, `--model`, `--image-type`, `--ref-image`, `--quality`, `--image-detail`, `--output`, `--session-dir`, `--api-key`, `--url`, `--dry-run` và alias ngắn. Override URL/key/model/protocol chỉ áp dụng tầng đầu, không lan sang fallback. Riêng sub2api luôn tự chọn edit/generation theo ảnh, kể cả khi có `--image-type`.
- `--image-type` là giao thức (`edit`, `9router`, `response`), không phải tên người bán. Các payload edit JSON/Responses cũ vẫn được hỗ trợ qua CLI/legacy; xem [đặc tả](references/openai_compat_spec.md).
- Khi hoàn toàn chưa có biến `API_IMAGE_*`, giữ cấu hình legacy `AI_IMAGE_URL/KEY/MODEL/TYPE`, alias cũ và `AI_TIMEOUT`. Không dùng schema thử nghiệm `IMAGE_PROVIDERS` / `NINEROUTER_IMAGE_*` / `ZPRO_IMAGE_*`.

## Chạy

Đặt `$SkillDir` là thư mục `api-image` đã cài:

```powershell
python "$SkillDir/scripts/generate_image.py" --prompt "Ảnh sản phẩm trên nền studio" --aspect-ratio 9:16 --session-dir .scratch/demo
python "$SkillDir/scripts/generate_image.py" --prompt "Giữ khuôn mặt, đổi nền trắng" --ref-image .scratch/demo/input/person.png --output .scratch/demo/output/edited.png
python "$SkillDir/scripts/generate_image.py" --dry-run
```

`--dry-run` hiển thị thứ tự, model, giao thức và lỗi cấu hình; không gọi mạng, không in key/header/prompt/ảnh. Không chứng minh gateway hỗ trợ hoặc đã tạo ảnh thành công.

## Fallback và giới hạn

- Giữ nguyên đầu vào ở mọi tầng: prompt, ảnh tham chiếu, size, quality, image detail. Chỉ chuyển đổi cách đóng gói theo giao thức (placeholder legacy được thay bằng định danh ảnh).
- Thiếu/sai cấu hình gateway: ghi lý do và thử tầng tiếp theo. Dịch vụ/quota/quyền truy cập hoặc tác vụ không được hỗ trợ: ghi lý do, có thể chuyển tầng; không tự bỏ ảnh hay giảm yêu cầu.
- Lỗi đầu vào: sửa hoặc dừng. Từ chối an toàn: dừng toàn chuỗi, không dùng fallback vượt từ chối.
- Timeout, mất kết nối sau khi gửi, phản hồi không rõ hoặc lỗi tải ảnh sau khi job thành công: dừng, không tự gửi trùng. Các adapter hiện tại chưa có hợp đồng API tra trạng thái job; cần kiểm tra trên gateway trước khi gửi lại. Nếu gateway bổ sung API trạng thái, tra job cũ trước khi cân nhắc tạo job mới.
- Hết provider thì báo thất bại với `attempts`; không retry vô hạn, không tự chuyển built-in/MuseAI và không sửa cấu hình.

## Kết quả và bảo mật

JSON trả `provider`, `model`, `configured_model`, `reported_model`, `model_source`, `attempts` cùng đường dẫn ảnh. Nếu upstream không báo model thực thi, `model` là model đã yêu cầu và `reported_model=null`; không khẳng định đã xác minh model backend. Lỗi được chuẩn hóa, không xuất body lỗi, key, header xác thực hay URL có thông tin nhạy cảm. Không in toàn bộ `.env`.

Giữ nguyên ảnh gốc; mở và xem ảnh đầu ra để nghiệm thu nội dung. Báo rõ dry-run/mock/API thật và phần chưa xác minh trực quan. Không gọi API tính phí chỉ để kiểm thử khi chưa được yêu cầu.
