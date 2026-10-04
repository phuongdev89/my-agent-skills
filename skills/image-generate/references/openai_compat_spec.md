# Đặc Tả Kỹ Thuật Image Provider Specs

Đặc tả cấu trúc request HTTP API cho các provider tạo ảnh của project và Google AI Studio.

---

## 1. Provider: OpenAI Edits API (`AI_IMAGE_TYPE=edit`)

Endpoint: `POST {AI_IMAGE_URL}/images/edits` (mặc định: ZPro / OpenAI chuẩn).

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

---

## 4. Provider: Google AI Studio Direct (`--use-gemini`)

Endpoint: `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={AI_IMAGE_KEY}`

### Request Payload:
```json
{
  "instances": [
    {
      "prompt": "Chân dung KOC nữ người Việt mặc áo polo..."
    }
  ],
  "parameters": {
    "sampleCount": 1,
    "aspectRatio": "9:16",
    "personGeneration": "ALLOW_ADULT",
    "outputMimeType": "image/png"
  }
}
```
