# Gemini-TTS Skill (Google GenAI & OpenAI-Compatible Audio Generation)

Kỹ năng tạo giọng đọc AI tiếng Việt thế hệ mới với khả năng điều khiển cảm xúc bằng câu lệnh tự nhiên (`--style`). Hỗ trợ chế độ kép:
1. **Google AI Studio chính hãng**: Xuất âm thanh bản địa (Native Audio Modality 24kHz) từ các mô hình `gemini-2.0-flash`, `gemini-2.5-flash`.
2. **OpenAI Compatibility Gateway**: Kết nối qua các trạm trung chuyển (như Omniroute, OneAPI, OpenAI proxy...) hỗ trợ `/v1/audio/speech` hoặc `/v1/chat/completions`.

Thư mục skill này hoàn toàn độc lập và linh hoạt, có thể sao chép trực tiếp sang bất kỳ dự án AI Agent nào khác.

---

## 1. Cấu trúc Thư mục Skill

```
gemini-tts/
├── README.md                      # Hướng dẫn chi tiết cho Developer và AI Agent
├── SKILL.md                       # Khai báo kỹ năng chuẩn cho hệ thống Agent
└── scripts/
    └── generate_gemini_voice.py   # Script CLI chuẩn REST API thuần Python (không cần pip cài thêm)
```

---

## 2. Hướng dẫn Dành Riêng Cho AI Agent (Agent Protocol)

Khi nhận lệnh tạo giọng đọc qua **`gemini-tts`**, Agent **BẮT BUỘC** thực hiện theo quy trình kiểm tra sau:

### Bước 1: Kiểm tra Biến Môi Trường Chuyên Dụng
Script tự động nạp cấu hình độc lập từ file `.env` theo thứ tự:
1. File `.env` tại thư mục hiện tại (`cwd`)
2. File `.env` tại thư mục gốc dự án
3. Biến môi trường hệ thống (`os.environ`)

> [!CAUTION]
> **Quy tắc cách ly khóa (Key Isolation)**: Tuyệt đối **KHÔNG** dùng chung API key của các Agent khác (`AI_AGENT_1_API_KEY`, `AI_AGENT_2_API_KEY`...). `gemini-tts` phải có cấu hình định danh riêng.

---

### Bước 2: Xử lý khi người dùng CHƯA cấu hình khóa
Nếu script trả về lỗi thiếu API key (`GEMINI_TTS_API_KEY`), Agent **TUYỆT ĐỐI KHÔNG đoán mò hay tự sinh khóa**. Agent cần hướng dẫn người dùng lựa chọn 1 trong 2 hình thức:

> *"Để kích hoạt giọng đọc `gemini-tts`, bạn cần cấu hình khóa API riêng trong file `.env`. Bạn có thể chọn 1 trong 2 hình thức sau:*
>
> **Lựa chọn 1: Sử dụng Google AI Studio chính hãng (Khuyên dùng - Biểu cảm cực tự nhiên)**
> 1. Lấy API key miễn phí tại: https://aistudio.google.com/app/apikey
> 2. Mở file `.env` và thêm:
> ```env
> GEMINI_TTS_ENABLE=true
> GEMINI_TTS_API_KEY=điền_key_AIzaSy_vào_đây
> GEMINI_TTS_ENDPOINT_URL=
> GEMINI_TTS_MODEL=gemini-2.0-flash
> GEMINI_TTS_VOICE=Kore
> ```
>
> **Lựa chọn 2: Sử dụng Gateway chuẩn OpenAI Compatibility (Omniroute, OneAPI, OpenAI proxy...)**
> Mở file `.env` và thêm:
> ```env
> GEMINI_TTS_ENABLE=true
> GEMINI_TTS_API_KEY=điền_key_sk_vào_đây
> GEMINI_TTS_ENDPOINT_URL=https://địa_chỉ_gateway_của_bạn/v1/audio/speech
> GEMINI_TTS_MODEL=gemini-2.0-flash
> GEMINI_TTS_VOICE=nova
> ```
>
> *Sau khi lưu file `.env`, bạn nhắn lại để mình tiến hành tạo giọng đọc ngay nhé!"*

---

## 3. Cách Sử Dụng CLI (`scripts/generate_gemini_voice.py`)

Script chạy thuần thư viện chuẩn Python (`urllib`, `wave`, `base64`), **không cần chạy `pip install` bất kỳ gói nào**.

### A. Dùng Google AI Studio kèm câu lệnh chỉ dẫn sắc thái KOC (`--style`)
```bash
python scripts/generate_gemini_voice.py \
  --text "Chào bạn! Chiếc áo polo này mặc lên form cực kỳ tôn dáng luôn nhé." \
  --voice "kore" \
  --style "Hào hứng, tươi vui, phong cách KOC thân thiện chia sẻ trải nghiệm bạn bè" \
  --output "output.wav"
```

### B. Dùng OpenAI Compatibility Gateway
```bash
python scripts/generate_gemini_voice.py \
  --text "Chào bạn! Đây là giọng đọc qua OpenAI compatible gateway." \
  --provider "openai" \
  --voice "nova" \
  --speed 1.05 \
  --format "mp3" \
  --output "output.mp3"
```

### C. Đọc từ file kịch bản (.txt)
```bash
python scripts/generate_gemini_voice.py \
  --text-file "script.txt" \
  --voice "puck" \
  --output "output.wav"
```

### D. Liệt kê toàn bộ các giọng đọc có sẵn của cả 2 hệ thống
```bash
python scripts/generate_gemini_voice.py --list-voices
```

---

## 4. Định dạng Đầu Ra Chuẩn (JSON Output)

Script xuất kết quả chuẩn JSON ra stdout:
```json
{
  "status": "success",
  "engine": "gemini-tts",
  "provider": "aistudio",
  "model": "gemini-2.0-flash",
  "voice": "Kore",
  "output_file": "D:\\path\\to\\output.wav",
  "duration_seconds": 4.15,
  "sample_rate": 24000,
  "file_size_bytes": 199244,
  "audio_format": "wav"
}
```

> [!IMPORTANT]
> **Dynamic Duration Rule**: Luôn dùng trường `duration_seconds` trả về từ JSON để căn chỉnh độ dài video hoặc phân cảnh. Tuyệt đối không cố định thời lượng video là 28s.

---

## 5. Danh Mục Giọng Đọc

### 5.1. Google AI Studio (Prebuilt Voices)
| Voice | Giới tính | Sắc thái & Ứng dụng KOC |
| :--- | :--- | :--- |
| **`Kore`** *(Mặc định)* | Nữ | Ấm áp, êm dịu, thư thái, tự nhiên (rất hợp review thời trang, mỹ phẩm, đời sống) |
| **`Aoede`** | Nữ | Trong trẻo, tươi vui, biểu cảm sinh động (rất hợp clip đồ gia dụng, ẩm thực, unboxing) |
| **`Puck`** | Nam | Năng động, nhiệt huyết, sôi nổi, trẻ trung (rất hợp KOC nam, công nghệ, thể thao) |
| **`Charon`** | Nam | Trầm ấm, chững chạc, uy quyền, điềm tĩnh (rất hợp podcast, bất động sản, tài chính) |
| **`Fenrir`** | Nam | Mạnh mẽ, dứt khoát, lôi cuốn, giọng dày (hợp review đồ nam, gaming, xe) |
| **`Autonoe`** | Nữ | Rõ ràng, dứt khoát, chuẩn mực, rành mạch (hợp giới thiệu tính năng, hướng dẫn) |

### 5.2. OpenAI Compatibility (Standard Voices)
| Voice | Giới tính | Đặc điểm |
| :--- | :--- | :--- |
| **`nova`** *(Mặc định)* | Nữ | Năng động, trẻ trung, tự nhiên (rất hợp KOC review) |
| **`shimmer`** | Nữ | Trong trẻo, nhẹ nhàng, êm tai |
| **`alloy`** | Trung tính | Cân bằng, phổ thông, rõ ràng |
| **`echo`** | Nam | Trầm ấm, truyền cảm |
| **`fable`** | Nam | Biểu cảm, phong cách kể chuyện |
| **`onyx`** | Nam | Trầm sâu, uy lực, nghiêm túc |
