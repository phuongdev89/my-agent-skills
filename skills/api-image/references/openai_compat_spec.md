# Gateway protocols

Provider và giao thức độc lập. Schema mới dùng `API_IMAGE_PROVIDER=9router|sub2api`, URL/key/model riêng theo [.env.example](../.env.example).

## sub2api tự định tuyến

Không có ảnh tham chiếu: `POST {API_IMAGE_SUB2API_URL}/images/generations`, JSON gồm `model`, `prompt`, `n=1`, `size`, `quality`.

Có ảnh tham chiếu: `POST {API_IMAGE_SUB2API_URL}/images/edits`, multipart/form-data gồm các trường trên và file nhị phân `image` (MIME từ ảnh nguồn). Ảnh không được bỏ khi fallback; không gửi trường JSON `images` của adapter edit legacy sang sub2api. `image_detail` là tùy chọn adapter 9router/response/legacy; sub2api không gửi trường này.

9router tiếp tục dùng payload generations mở rộng bên dưới. Các giao thức legacy edit JSON và Responses giữ tương thích; chúng không đại diện mặc định cho sub2api. `AI_IMAGE_*` dưới đây chỉ áp dụng chế độ legacy.

# Đặc Tả Kỹ Thuật Image Provider Specs

Đặc tả cấu trúc request HTTP API cho các provider tạo ảnh tương thích OpenAI của project.

---

## 1. Provider: OpenAI Edits API (`AI_IMAGE_TYPE=edit`)

Endpoint: `POST {AI_IMAGE_URL}/images/edits` (adapter JSON legacy).

### Request Payload:
```json
{
  "model": "gpt-image-2",
  "prompt": "input_file_0.png wearing a navy polo shirt...",
  "n": 1,
  "size": "auto",
  "quality": "auto",
  "background": "auto",
  "image_detail": "high",
  "output_format": "png",
  "response_format": "b64_json",
  "stream": true,
  "images": [
    {
      "id": "input_file_0.png",
      "image_url": "data:image/jpeg;base64,..."
    }
  ]
}
```
*Lưu ý: Chuỗi `[ATTACHED_PHOTO]` trong prompt người dùng sẽ tự động được chuyển thành `input_file_0.png`.*

---

## 2. Provider: OpenAI Generations Flat Image (`AI_IMAGE_TYPE=9router`)

Endpoint: `POST {AI_IMAGE_URL}/images/generations` (9router).

### Request Payload:
```json
{
  "model": "cx/gpt-5.6-sol-image",
  "prompt": "the attached reference image wearing a navy polo shirt...",
  "n": 1,
  "size": "auto",
  "quality": "auto",
  "background": "auto",
  "image_detail": "high",
  "output_format": "png",
  "response_format": "b64_json",
  "stream": true,
  "image": "data:image/jpeg;base64,..."
}
```
*Lưu ý: Chuỗi `[ATTACHED_PHOTO]` trong prompt người dùng sẽ tự động được chuyển thành `the attached reference image`.*

---

## 3. Provider: Multimodal Responses API (`AI_IMAGE_TYPE=response`)

Endpoint: `POST {AI_IMAGE_URL}/responses` (OmniRoute).

### Request Payload:
```json
{
  "model": "cx/gpt-5.6-sol-image",
  "input": [
    {
      "role": "user",
      "content": [
        {
          "type": "input_image",
          "image_url": "data:image/jpeg;base64,...",
          "detail": "high"
        },
        {
          "type": "input_text",
          "text": "the input image wearing a navy polo shirt..."
        }
      ]
    }
  ],
  "tools": [
    {
      "type": "image_generation",
      "model": "cx/gpt-5.6-sol-image",
      "action": "edit",
      "quality": "auto",
      "size": "auto",
      "output_format": "png"
    }
  ],
  "tool_choice": {
    "type": "image_generation"
  }
}
```
