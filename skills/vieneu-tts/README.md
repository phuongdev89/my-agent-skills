# VieNeu-TTS Skill (Vietnamese On-Device Neural TTS)

Kỹ năng tạo giọng đọc tiếng Việt **cục bộ (On-Device)**, chất lượng cao 48kHz, hỗ trợ nhân bản giọng nói (Instant Voice Cloning) và gắn tag cảm xúc trực tiếp.

Thư mục skill này hoàn toàn độc lập, có thể sao chép trực tiếp sang bất kỳ dự án AI Agent nào khác.

---

## 1. Cấu trúc Thư mục Skill

```
vieneu-tts/
├── README.md                 # Hướng dẫn chi tiết cho Developer và AI Agent
├── SKILL.md                  # Khai báo kỹ năng chuẩn cho hệ thống Agent (Antigravity/Cursor/Claude)
└── scripts/
    └── generate_voice.py     # Script CLI tự động sinh file âm thanh và đo độ dài (WAV)
```

---

## 2. Hướng dẫn Dành Riêng Cho AI Agent (Agent Protocol)

Khi nhận lệnh tạo giọng đọc qua **`vieneu-tts`**, Agent **BẮT BUỘC** thực hiện theo quy trình kiểm tra sau:

### Bước 1: Kiểm tra xem môi trường đã có thư viện `vieneu` chưa
Chạy lệnh shell:
```bash
python -c "import vieneu"
```

### Bước 2: Xử lý khi người dùng CHƯA cài đặt package (`ModuleNotFoundError`)
Nếu lệnh trên trả về lỗi chưa có module `vieneu`, Agent xử lý như sau:
1. **Nếu Agent có quyền chạy lệnh (`run_command`)**: Chủ động chạy lệnh cài đặt:
   ```bash
   # Chạy trên CPU (Rất nhẹ, tối ưu ONNX Runtime, không cần GPU):
   pip install vieneu

   # Hoặc nếu máy có GPU NVIDIA CUDA (nếu muốn tăng tốc tối đa):
   pip install "vieneu[cuda]"
   ```
2. **Nếu Agent KHÔNG có quyền tự chạy pip hoặc môi trường bị khóa**: Phải thông báo ngay cho người dùng:
   > *"Dự án chưa cài đặt thư viện `vieneu`. Bạn vui lòng mở terminal và chạy lệnh: `pip install vieneu` (hoặc `pip install vieneu[cuda]` nếu có GPU NVIDIA) rồi nhắn lại để mình tiếp tục nhé!"*

### Bước 3: Lưu ý tải Model lần đầu (First-run Cache)
- Khi chạy lần đầu tiên, thư viện `vieneu` sẽ tự động tải trọng số mô hình `pnnbao-ump/VieNeu-TTS-v3-Turbo` (~300MB) về thư mục cache Hugging Face (`~/.cache/huggingface/hub/`). Quá trình này diễn ra một lần duy nhất, sau đó hoạt động offline 100% không cần mạng.

---

## 3. Cách Sử Dụng CLI (`scripts/generate_voice.py`)

Agent hoặc Developer có thể gọi trực tiếp script từ terminal:

### A. Đọc văn bản bằng giọng dựng sẵn (Preset Voice)
```bash
python scripts/generate_voice.py \
  --text "Chào bạn! Chiếc áo này mặc lên form cực kỳ tôn dáng luôn nhé [cười]." \
  --voice "Đoan Trang" \
  --output "output_audio.wav"
```

### B. Đọc từ file kịch bản (.txt)
```bash
python scripts/generate_voice.py \
  --text-file "script.txt" \
  --voice "Minh Quân" \
  --output "output_audio.wav"
```

### C. Nhân bản giọng nói (Instant Voice Cloning) từ audio mẫu 3–8 giây
```bash
python scripts/generate_voice.py \
  --text "Chất vải thun cotton này sờ vào mát rượi luôn mọi người ơi!" \
  --ref-audio "path/to/koc_sample_5s.wav" \
  --output "output_audio.wav"
```

### D. Liệt kê toàn bộ danh sách giọng có sẵn
```bash
python scripts/generate_voice.py --list-voices
```

---

## 4. Định dạng Đầu Ra Chuẩn (JSON Output)

Script in ra stdout kết quả JSON chuẩn giúp Agent bắt được thông số kỹ thuật:
```json
{
  "status": "success",
  "mode": "preset_voice",
  "voice": "Đoan Trang",
  "output_file": "D:\\path\\to\\output_audio.wav",
  "duration_seconds": 4.4,
  "sample_rate": 48000,
  "file_size_bytes": 422444
}
```

> [!IMPORTANT]
> **Dynamic Duration Rule**: Sử dụng giá trị `duration_seconds` thực tế từ JSON để căn chỉnh độ dài video hoặc phân cảnh. Tuyệt đối không cố định thời lượng video là 28s.

---

## 5. Danh mục Giọng Đọc Dựng Sẵn (Preset Voices)

| Khu vực | Tên giọng | Đặc điểm |
| :--- | :--- | :--- |
| **Miền Bắc** | **`Minh Quân`** *(Mặc định)* | Nam Hà Nội, tự nhiên, chuẩn tin tức / podcast |
| | **`Đoan Trang`** | Nữ ấm áp, thanh lịch, KOC review đời sống |
| | **`Hà My`** | Nữ tươi sáng, nhẹ nhàng |
| | **`Tiến Dũng`** | Nam trầm ấm, chững chạc |
| **Miền Nam** | **`Thảo Trinh`** | Nữ Sài Gòn truyền cảm, ngọt ngào |
| | **`Bảo Nam`** | Nam trẻ trung, sôi nổi |
| | **`Lan Hương`** | Nữ dịu dàng, tự nhiên |
| **Miền Trung** | **`Hương Giang`** | Nữ Huế nhẹ nhàng, duyên dáng |
| | **`Văn Trọng`** | Nam Quảng Nam / Đà Nẵng ấm áp |

### Tag biểu cảm hỗ trợ:
Bạn có thể chèn trực tiếp các tag biểu cảm vào câu thoại:
- `[cười]` : Thêm tiếng cười nhẹ nhàng tự nhiên.
- `[thở dài]` : Thở dài nhẹ, tạo cảm giác lắng đọng.
- `[hắng giọng]` : Hắng giọng tự nhiên trước khi nói.
