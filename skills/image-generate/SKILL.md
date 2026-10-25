---
name: image-generate
description: Tạo và sửa ảnh raster, chân dung KOC và sản phẩm; ưu tiên công cụ imagegen tích hợp của agent, chuyển sang skill api-image khi công cụ không có hoặc không khả dụng.
---

# Image Generate

## Chọn công cụ

- Xác định tạo ảnh hay sửa ảnh; xem ảnh nguồn trước khi sửa. Bóc outfit từ ảnh người mẫu là sửa ảnh. Ghi nhận phần cần đổi và phần cần giữ.
- Dùng prompt, ảnh tham chiếu, kích thước, tỷ lệ và chất lượng người dùng yêu cầu. Giữ tỷ lệ ảnh nguồn khi sửa; mặc định 9:16 cho ảnh mới phục vụ video ngắn, chất lượng auto.
- Ưu tiên công cụ imagegen built-in thực sự có trong phiên (ví dụ `image_gen.imagegen`); tuân thủ hợp đồng của host, truyền ảnh nguồn thực tế khi sửa. Cấu hình API trong `.env` không thay đổi ưu tiên này.
- Khi built-in không có, không hỗ trợ tác vụ hoặc không khả dụng do dịch vụ/quota/quyền truy cập, dùng skill `api-image`. Tìm skill đã cài theo tên; trong repository này đọc [api-image](../api-image/SKILL.md). Nếu chưa cài, báo thiếu skill; không tự viết một client thay thế.
- Khi chuyển sang API, nêu lý do; chuyển nguyên prompt, ảnh nguồn, kích thước, tỷ lệ, chất lượng và lịch sử thử đã có. Không bỏ ảnh tham chiếu để biến sửa ảnh thành tạo ảnh.
- Lỗi đầu vào cần sửa hoặc dừng. Từ chối an toàn phải dừng, không chuyển provider để vượt từ chối. Timeout chưa rõ job đã nhận hay chưa: kiểm tra trạng thái nếu host hỗ trợ; không tự gửi lại hoặc chuyển API tạo trùng job.
- Skill này chỉ điều phối built-in → `api-image`, không chứa client hoặc cấu hình gateway. Không tự điều phối MuseAI.

## Kết quả

Giữ ảnh gốc. Nếu cần lưu file, dùng session `.scratch/yyyy-mm-dd_image-generate_ten-tac-vu/`; script tạm phải ở thư mục đã gitignore. Với built-in, tuân thủ nơi lưu/hiển thị của host.

Kiểm tra ảnh mở được và xem ảnh để đối chiếu nội dung/nhận diện/sản phẩm. Trả ảnh hoặc link file, công cụ/provider, model thực tế nếu biết (không đoán), các lần thử/lý do fallback, thông số đo được và prompt thực tế. Phân biệt kết quả API với kết quả đã kiểm tra trực quan.

Đọc [prompting_guide.md](references/prompting_guide.md) khi cần prompt KOC/sản phẩm.
