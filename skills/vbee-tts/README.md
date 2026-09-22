# Vbee-TTS Skill (Vietnamese Cloud Neural TTS)

Kỹ năng tạo giọng đọc tiếng Việt qua nền tảng Cloud API chuyên biệt của **Vbee AIVoice** (vbee.vn). Giọng đọc đạt chuẩn phòng thu 48kHz với ngữ điệu đa dạng khắp 3 miền Bắc, Trung, Nam.

Thư mục skill này hoàn toàn độc lập, có thể sao chép trực tiếp sang bất kỳ dự án AI Agent nào khác mà không cần cấu hình phức tạp.

---

## 1. Cấu trúc Thư mục Skill

```
vbee-tts/
├── README.md                     # Hướng dẫn chi tiết cho Developer và AI Agent
├── SKILL.md                      # Khai báo kỹ năng chuẩn cho hệ thống Agent
└── scripts/
    └── generate_vbee_voice.py    # Script CLI tự động gọi Cloud API, tải audio và đo thời lượng thực tế
```

---

## 2. Hướng dẫn Dành Riêng Cho AI Agent (Agent Protocol)

Khi nhận lệnh tạo giọng đọc qua **`vbee-tts`**, Agent **BẮT BUỘC** thực hiện theo quy trình kiểm tra sau:

### Bước 1: Kiểm tra Biến Môi Trường (API Credentials)
Script tự động tìm `VBEE_APP_ID` và `VBEE_ACCESS_TOKEN` từ các nguồn:
1. File `.env` tại thư mục hiện tại (`cwd`)
2. File `.env` tại thư mục gốc dự án
3. Biến môi trường hệ thống (`os.environ`)

### Bước 2: Xử lý khi người dùng CHƯA cấu hình thông tin Vbee
Nếu script trả về lỗi `status: "error"` hoặc phát hiện thiếu khóa, Agent **TUYỆT ĐỐI KHÔNG đoán mò hay tự bịa khóa**. Agent phải xuất thông báo rõ ràng cho người dùng:

> *"Để sử dụng Vbee-TTS, bạn cần cung cấp thông tin tài khoản API từ Vbee.vn. Vui lòng mở file `.env` và bổ sung 2 dòng sau:*
> ```env
> VBEE_APP_ID=điền_app_id_tại_đây
> VBEE_ACCESS_TOKEN=điền_access_token_tại_đây
> ```
> *(Bạn có thể lấy thông tin này tại trang quản lý API của https://vbee.vn).*
> 
> *Gợi ý: Nếu chưa có tài khoản Vbee, bạn có thể bảo mình chuyển sang dùng skill `vieneu-tts` (chạy hoàn toàn cục bộ miễn phí, không cần tài khoản) hoặc `gemini-tts` nhé!"*

### Bước 3: Kiểm tra FFmpeg (Tùy chọn)
- Nếu người dùng yêu cầu xuất file định dạng `.mp3`, script sẽ dùng FFmpeg để chuyển đổi từ file gốc nếu cần. Nếu máy chưa có FFmpeg, script sẽ tự động bảo lưu file dưới dạng `.wav` nguyên bản.

---

## 3. Cách Sử Dụng CLI (`scripts/generate_vbee_voice.py`)

### A. Đọc trực tiếp văn bản bằng giọng Thu Trang (KOC Review, miền Bắc)
```bash
python scripts/generate_vbee_voice.py \
  --text "Chào bạn! Đây là mẫu giọng đọc Thu Trang của Vbee nhé." \
  --voice "thutrang" \
  --output "output.mp3"
```

### B. Đọc từ file kịch bản (.txt) với giọng Ngọc Huyền (Thuyết minh tin tức)
```bash
python scripts/generate_vbee_voice.py \
  --text-file "kịch_bản.txt" \
  --voice "ngochuyen" \
  --speed 1.05 \
  --output "output.mp3"
```

### C. Liệt kê toàn bộ các giọng đọc và alias có sẵn
```bash
python scripts/generate_vbee_voice.py --list-voices
```

---

## 4. Định dạng Đầu Ra Chuẩn (JSON Output)

Script xuất kết quả chuẩn JSON ra stdout:
```json
{
  "status": "success",
  "engine": "vbee",
  "voice_code": "hn_female_thutrang_48k-fhg",
  "output_file": "D:\\path\\to\\output.mp3",
  "duration_seconds": 3.84,
  "file_size_bytes": 61440,
  "audio_format": "mp3"
}
```

> [!IMPORTANT]
> **Dynamic Duration Rule**: Luôn dùng trường `duration_seconds` trả về từ JSON để căn chỉnh độ dài dựng video. Tuyệt đối không cố định thời lượng video là 28s.

---

## 5. Bảng Alias Giọng Đọc Phổ Biến

Agent có thể truyền trực tiếp tên alias ngắn gọn qua tham số `--voice`:

| Miền | Alias | Tên giọng & Phong cách | Mã Vbee Đầy Đủ |
| :--- | :--- | :--- | :--- |
| **Bắc** | `thutrang` | **Thu Trang** — Nữ (KOC Review sôi nổi, tự nhiên) | `hn_female_thutrang_48k-fhg` |
| | `ngochuyen` | **Ngọc Huyền** — Nữ (Chuẩn tin tức, thuyết minh) | `hn_female_ngochuyen_full_48k-fhg` |
| | `maiphuong` | **Mai Phương** — Nữ (Truyền cảm, dịu dàng) | `hn_female_maiphuong_vdts_48k-fhg` |
| | `manhdung` | **Mạnh Dũng** — Nam (Đọc báo, tài chính, chững chạc) | `hn_male_manhdung_news_48k-fhg` |
| | `ducanh` | **Đức Anh** — Nam (Năng động, trẻ trung) | `hn_male_ducanh_48k-fhg` |
| **Nam** | `thaotrinh` | **Thảo Trinh** — Nữ (Truyền cảm, ấm áp) | `sg_female_thaotrinh_48k-fhg` |
| | `minhhoang` | **Minh Hoàng** — Nam (Gần gũi, ấm áp) | `sg_male_minhhoang_48k-fhg` |
| | `lanhuong` | **Lan Hương** — Nữ (Nhẹ nhàng, thanh thoát) | `sg_female_lanhuong_48k-fhg` |
| **Trung**| `huonggiang` | **Hương Giang** — Nữ Huế (Dịu dàng, đằm thắm) | `hue_female_huonggiang_48k-fhg` |
| | `duyphuong` | **Duy Phương** — Nam Huế (Trầm ấm, truyền cảm) | `hue_male_duyphuong_48k-fhg` |

*(Có thể truyền bất kỳ mã voice_code nào khác từ thư viện Vbee vào tham số `--voice`).*
