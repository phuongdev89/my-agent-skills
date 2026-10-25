# API Image

Client Python tạo/sửa ảnh qua 9router và sub2api. Cài cùng `image-generate` để dùng thứ tự built-in → API; có thể gọi `api-image` trực tiếp khi người dùng chọn API.

Cấu hình theo [.env.example](.env.example) trong `.env` của dự án người dùng. `API_IMAGE_PROVIDER=9router|sub2api` là thứ tự fallback; một tên là chỉ dùng gateway đó. Với sub2api, có ảnh tham chiếu gọi edits multipart; không có ảnh gọi generations JSON.

Xem [SKILL.md](SKILL.md) cho CLI, tương thích legacy, an toàn fallback và ý nghĩa kết quả. Chạy `python scripts/generate_image.py --dry-run` từ thư mục skill chỉ kiểm tra cấu hình tại cwd, không gọi mạng.
