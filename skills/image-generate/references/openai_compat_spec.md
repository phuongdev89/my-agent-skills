# Đặc Tả Kỹ Thuật OpenAI Image Compatibility

Tài liệu chuẩn giao tiếp HTTP API với các cổng hình ảnh tương thích chuẩn OpenAI (`/v1/images/generations` và `/v1/images/edits`).

---

## 1. Endpoint Chuẩn

* **Tạo ảnh từ văn bản (Text-to-Image)**:
  `POST {ENDPOINT_URL}` (Thường là `https://.../v1/images/generations`)
* **Chỉnh sửa / Biến thể từ ảnh mẫu (Image-to-Image / Edit)**:
  `POST {ENDPOINT_BASE}/v1/images/edits`

---

## 2. Cấu Trúc Request Header

```http
POST /v1/images/generations HTTP/1.1
Host: your-gateway.com
Authorization: Bearer <AI_IMAGE_API_KEY>
Content-Type: application/json
```

---

## 3. Payload Request JSON (`/v1/images/generations`)

```json
{
  "model": "cx/gpt-5.6-sol-image",
  "prompt": "Chân dung KOC nữ người Việt mặc áo polo xanh navy, chụp dọc 9:16, ánh sáng studio, 4k photorealistic...",
  "size": "1024x1792",
  "quality": "standard",
  "response_format": "b64_json",
  "n": 1
}
```

### Các trường tham số chính:
* `model` (bắt buộc): Model chỉ định sinh ảnh (lấy từ biến `AI_IMAGE_MODEL` trong `.env`, ví dụ: `cx/gpt-5.6-sol-image`, `cx/gpt-image-2`, `dall-e-3`...).
* `prompt` (bắt buộc): Câu lệnh mô tả ảnh bằng tiếng Anh hoặc tiếng Việt.
* `size` (tùy chọn): Kích thước ảnh.
  - Khuyên dùng cho video ngắn dọc: `"1024x1792"` hoặc `"1024x1536"` (tỷ lệ 9:16).
  - Vuông: `"1024x1024"`.
  - Ngang: `"1792x1024"`.
* `response_format`: Ưu tiên `"b64_json"` để nhận trực tiếp dữ liệu nhị phân base64, tránh bị lỗi hết hạn URL hoặc lỗi tường lửa tải ảnh.
* `n`: Số lượng ảnh sinh ra (mặc định 1).

---

## 4. Cấu Trúc Response JSON

### Dạng 1: Dữ liệu Base64 (`response_format: "b64_json"`)
```json
{
  "created": 1726000000,
  "data": [
    {
      "b64_json": "/9j/4AAQSkZJRgABAQEASABIAAD...",
      "revised_prompt": "An authentic Vietnamese female KOC standing in a modern cafe..."
    }
  ]
}
```

### Dạng 2: Đường dẫn tải ảnh URL (`response_format: "url"`)
```json
{
  "created": 1726000000,
  "data": [
    {
      "url": "https://storage.googleapis.com/.../image.png",
      "revised_prompt": "..."
    }
  ]
}
```

Script sẽ tự động giải mã `b64_json` hoặc tải ảnh từ `url` về lưu thẳng vào đường dẫn file đích được chỉ định.
