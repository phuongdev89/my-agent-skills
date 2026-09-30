# 🎨 HƯỚNG DẪN ĐỊNH DẠNG BẢNG & TÁI TẠO SƠ ĐỒ THỊ GIÁC (TABLE STYLING GUIDE)

> Tài liệu chuẩn hóa kỹ thuật tái tạo hình ảnh, sơ đồ, ma trận đối chiếu và hộp thông tin thành bảng Word (Table) sắc nét, chuyên nghiệp và có thể copy/edit nội dung.

---

## 🌈 1. HỆ THỐNG BẢNG MÀU CHUẨN (COLOR PALETTE)

| Tông màu | Mục đích sử dụng | Mã Hex Nền (`shd`) | Mã Hex Viền (`border`) | Mã Hex Chữ / Badge |
| :--- | :--- | :---: | :---: | :---: |
| **Slate (Trung tính)** | Banner đề mục, văn bản mặc định | `#E2E8F0` / `#F8FAFC` | `#CBD5E1` / `#94A3B8` | `#0F172A` / `#334155` |
| **Blue (Chủ đạo / Công nghệ)** | Số chương, quy trình, link, bước làm | `#EFF6FF` / `#DBEAFE` | `#93C5FD` / `#2563EB` | `#1E3A8A` / `#2563EB` |
| **Emerald (Tích cực / Đúng)** | Cột "ĐÚNG", "REMAKE", ưu điểm, mẹo | `#ECFDF5` / `#D1FAE5` | `#A7F3D0` / `#10B981` | `#065F46` / `#059669` |
| **Rose / Red (Tiêu cực / Sai)** | Cột "SAI", "REUP", cảnh báo, rủi ro | `#FEF2F2` / `#FEE2E2` | `#FECACA` / `#EF4444` | `#991B1B` / `#DC2626` |
| **Amber (Chú ý / Mẹo)** | Lưu ý quan trọng, tip thực chiến | `#FFFBEB` / `#FEF3C7` | `#FDE68A` / `#F59E0B` | `#92400E` / `#D97706` |
| **Dark Slate (Callout)** | Khung QR Code, video hướng dẫn, link bio | `#0F172A` | Không viền (`none`) | `#FFFFFF` / `#38BDF8` |

---

## 📐 2. KÍCH THƯỚC VÙNG TRÌNH BÀY A4
- **Kích thước trang:** Rộng 8.27 inch (21 cm) x Cao 11.69 inch (29.7 cm).
- **Căn lề lề trái/phải:** 0.75 inch mỗi bên.
- **Chiều rộng khả dụng (Print Width):** $8.27 - (0.75 \times 2) = \mathbf{6.77\text{ inch}}$ (~17.2 cm).
- **Căn chỉnh bảng:** Luôn đặt `tbl.alignment = WD_TABLE_ALIGNMENT.CENTER`.
- **Phân bổ chiều rộng cột:**
  - Bảng 1 cột (Banner / Callout): `cell.width = Inches(6.77)`
  - Bảng 2 cột (So sánh 2 bên): `cell.width = Inches(3.32)` (chừa khoảng đệm)
  - Bảng 3 cột: `cell.width = Inches(2.22)`
  - Bảng 4 cột: `cell.width = Inches(1.66)`
  - Bảng 5 cột: `cell.width = Inches(1.33)`

---

## 🧩 3. CÁC MẪU SƠ ĐỒ THỊ GIÁC ĐIỂN HÌNH

### Mẫu 1: Ma Trận Đối Chiếu Tương Phản (Contrast Comparison Cards)
Dùng khi tài liệu có sơ đồ đối lập giữa cách làm sai và cách làm đúng, phương pháp cũ vs mới.
* **Cột trái (Tiêu cực):** Nền đỏ nhạt (`#FEF2F2`), viền đỏ (`#FECACA`), tiêu đề badge đỏ đậm (`❌ REUP - Copy nguyên video`).
* **Cột phải (Tích cực):** Nền xanh lá nhạt (`#ECFDF5`), viền xanh (`#A7F3D0`), tiêu đề badge xanh lá (`✔ REMAKE - Sáng tạo thông minh`).
* **Hàm hỗ trợ:** `docx_helpers.add_comparison_cards(doc, left_card, right_card)`

### Mẫu 2: Sơ Đồ Quy Trình Ngang (Process Flow Steps)
Dùng khi tài liệu có các mũi tên chuyển tiếp (Bước 1 → Bước 2 → Bước 3).
* Dựng bảng 1 hàng có $N$ cột tương ứng $N$ bước.
* Hàng đầu mỗi ô: Badge số bước (`BƯỚC 1`, `BƯỚC 2`) màu xanh dương.
* Viền dưới mỗi ô tô đậm màu xanh (`#3B82F6`) tạo điểm nhấn trục quy trình.
* **Hàm hỗ trợ:** `docx_helpers.add_process_steps(doc, steps_list)`

### Mẫu 3: Hộp Hiển Thị Chỉ Số / KPI (Stat Boxes)
Dùng cho các kết quả case study hoặc số liệu nổi bật.
* Dựng bảng 1 hàng 3-5 cột. Nền trắng xám (`#F8FAFC`), viền dưới dày màu xanh (`#2563EB`).
* Số hiển thị to đậm 13-16pt màu xanh thẫm (`#1E3A8A`), nhãn mô tả chữ in hoa 8pt màu xám (`#64748B`).
* Kèm icon thị giác: `▶️`, `👁️`, `🛒`, `💰`, `⏱️`.
* **Hàm hỗ trợ:** `docx_helpers.add_stat_boxes(doc, stats_list)`

### Mẫu 4: Khung Callout QR Code / Video Hướng Dẫn
Dùng khi trong trang có ô QR Code, đường link xem video hoặc nhóm kín.
* Bảng 1x1 ô, nền đen / slate thẫm (`#0F172A`).
* Toàn bộ chữ bên trong màu trắng (`#FFFFFF`) hoặc xanh neon (`#38BDF8`).
* Không viền viền ngoài, padding rộng rãi (`top/bottom=140, left/right=180 dxa`).
* **Hàm hỗ trợ:** `docx_helpers.add_qr_callout(doc, text_runs)`

### Mẫu 5: Banner Đề Mục Heading 2 (Navigation-Enabled Banner)
Dùng cho tất cả các đề mục lớn trong trang.
* Bảng 1x1 ô, nền xám nhạt (`#E2E8F0`), viền trên viền dưới tinh tế.
* Đoạn văn bên trong được gán style `Heading 2` của Word để hiển thị ngay trên Left Navigation Pane.
* **Hàm hỗ trợ:** `docx_helpers.add_heading_2_banner(doc, title_str)`
