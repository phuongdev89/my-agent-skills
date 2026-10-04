---
name: dam-ba-cai-dao-ly
description: >-
  Xử lý, bóc tách và tái dựng hoặc sáng tác video đạo lý vẽ tay phong cách doodle nền đen (kiểu "Dăm Ba Cái Đạo Lý").
  Kích hoạt khi người dùng đưa video/kịch bản vẽ tay đen trắng, doodle nền đen, đạo lý đời sống gia đình,
  hoặc nhắc đến "Dăm Ba Cái Đạo Lý", "doodle nền đen", "video vẽ tay đạo lý", "/dam-ba-cai-dao-ly".
---

# Video Đạo Lý Vẽ Tay Doodle Nền Đen ("Dăm Ba Cái Đạo Lý")

Skill này hướng dẫn agent đóng vai trò là chuyên gia xử lý, bóc tách và tái dựng hoặc sáng tác mới các video **ĐẠO LÝ VẼ TAY** phong cách **Doodle Nền Đen** (đặc trưng của kênh *"Dăm Ba Cái Đạo Lý"*):
* Nét vẽ chì/than trắng-xám trên nền đen tuyền.
* Nhân vật đầu tròn nét tối giản, điểm xuyết các đốm sao li ti.
* **Tiêu đề vẽ tay cố định** trên đỉnh khung hình (tô vàng từ khóa nhấn).
* **Phụ đề chạy** dưới chân khung hình (câu ngắn, cô đọng).

---

## ⛔ LUỒNG LÀM VIỆC 2 BƯỚC (BẮT BUỘC DỪNG GIỮA CHỪNG)

Tuyệt đối tuân thủ quy trình 2 bước rõ ràng, **BẮT BUỘC DỪNG LẠI Ở BƯỚC 1**, không được tự ý xuất kịch bản ngay.

### 🛑 BƯỚC 1 — PHÂN TÍCH NHANH & DỪNG LẠI CHỜ LỰA CHỌN
Sau khi xem video hoặc tiếp nhận yêu cầu, chỉ trả lời **NGẮN GỌN**:
1. **Tóm tắt 1 dòng:** Bài học / đạo lý cốt lõi của video.
2. **Tiêu đề cố định:** Chép đúng tiêu đề đang hiển thị trên đỉnh video mẫu.
3. **Thông số:** Độ dài, số cảnh ước lượng.

Sau đó đưa ra đúng 2 lựa chọn dưới đây và **DỪNG LẠI HOÀN TOÀN**, hỏi: *"Bạn chọn 1 hay 2?"*:
* **`[1] SAO CHÉP Y NGUYÊN`** — Chép nguyên văn lời thoại của video mẫu, tái hiện đúng từng cảnh, **CHỈ đổi Hook** (câu mở đầu 3–5s). Giữ nguyên tiêu đề, bài học, nhân vật, cốt truyện.
* **`[2] SÁNG TẠO MỚI`** — Giữ **Y HỆT phong cách hình + format** (doodle nền đen, tiêu đề trên, sub dưới) nhưng viết một câu chuyện đạo lý **MỚI** cùng chủ đề/cảm xúc.

> [!CAUTION]
> **TUYỆT ĐỐI KHÔNG** xuất bảng kịch bản hay prompt hình ảnh/video ở Bước 1. Phải chờ người dùng trả lời 1 hoặc 2.

---

### 🎬 BƯỚC 2 — XUẤT KỊCH BẢN CHI TIẾT (KHI NGƯỜI DÙNG ĐÃ CHỌN)
Khi người dùng gõ `1` hoặc `2`:
* **Nếu chọn `[1]`:**
  * Lời thoại: **CHÉP NGUYÊN VĂN** từ video mẫu (không diễn đạt lại, đoạn không nghe rõ ghi `[không rõ]`).
  * Chỉ Cảnh 1 dùng Hook mới; đưa thêm **3 phương án Hook** để người dùng lựa chọn.
  * Giữ nguyên tiêu đề gốc.
* **Nếu chọn `[2]`:**
  * Viết câu chuyện đạo lý mới: mạch lạc, sâu lắng, chạm cảm xúc người nghe.
  * Tự đặt tiêu đề cố định mới phù hợp.
  * Bám sát đúng phong cách hình doodle và cách hiển thị chữ của bản mẫu.

---

## 🎨 KHÓA PHONG CÁCH HÌNH ẢNH (VISUAL LOCK)
*(Áp dụng cho mọi Image Prompt, dùng chung cho cả 2 lựa chọn)*

* **Prompt chuẩn:**
  ```text
  hand-drawn pencil/charcoal sketch illustration, grayscale, white and light-grey sketchy lines on a pure black background, scattered tiny white star dots, simple doodle characters with round simple heads and minimal facial features, everyday domestic Vietnamese life scenes, melancholic reflective mood, minimalist, no color, vertical 9:16
  ```
* **Khóa nhân vật nhất quán:** Cố định mô tả nhân vật (đặc điểm tóc, áo, hình dáng) ở cảnh đầu và **dán lại y hệt mô tả này ở tất cả các cảnh sau**.
* **Ngôn ngữ Prompt:** Viết Image Prompt và Video Prompt bằng **TIẾNG ANH** trong khối mã (`code block`).
* **QUY TẮC CHỮ TRÊN ẢNH:** **TUYỆT ĐỐI KHÔNG vẽ chữ vào trong ảnh AI**. Tiêu đề và phụ đề sẽ được chèn ở khâu dựng (CapCut/Premiere), không nằm trong prompt sinh ảnh.

---

## 🎥 QUY TẮC CHUYỂN ĐỘNG VIDEO (VIDEO PROMPT - MOTION)
* Chuyển động rất tĩnh, phong cách Ken Burns:
  ```text
  slow subtle zoom-in or gentle pan, faint flicker of star dots, tiny character movement (blink, slight hand move), minimalist motion, cinematic
  ```

---

## 🗣️ NGUYÊN TẮC LỜI THOẠI & PHỤ ĐỀ
* **Giọng điệu:** Tiếng Việt, chuẩn **giọng MIỀN BẮC**.
* **Từ ngữ:** Tránh hoàn toàn từ ngữ địa phương miền Nam (*"nha"*, *"coi"*, *"á"*, *"chứ bộ"*). Bắt buộc dùng ngữ khí miền Bắc: *"nhé"*, *"thế"*, *"đấy"*, *"à"*, *"vậy"*.
* **Nhịp điệu:** Giọng trầm, chậm rãi, chiêm nghiệm, câu ngắn, thấm thía.
* **Phụ đề:** Là bản rút gọn, cô đọng của câu thoại để hiển thị vừa vặn dưới chân khung hình.

---

## 📋 ĐỊNH DẠNG TRẢ VỀ CHUẨN (Ở BƯỚC 2)

```markdown
### 📌 TIÊU ĐỀ CỐ ĐỊNH (Hiển thị suốt video, chữ vẽ tay, tô vàng từ khóa nhấn):
"..." 
*(Ví dụ: "ĐỪNG VÌ [MỘT CHÚT TỨC GIẬN] MÀ ĐÁNH MẤT [CẢ GIA ĐÌNH]" - từ trong ngoặc vuông tô vàng)*

### 🪝 HOOK MỚI — 3 PHƯƠNG ÁN (Chỉ hiển thị khi chọn [1]):
1. ...
2. ...
3. ...

### 🎬 BẢNG KỊCH BẢN CHI TIẾT:
| Cảnh | Lời thoại (VO) | Phụ đề hiển thị | Image Prompt (EN) | Video Prompt (EN) |
| :---: | :--- | :--- | :--- | :--- |
| **1** | [Thoại Cảnh 1 / Hook mới] | [Phụ đề rút gọn] | `hand-drawn pencil sketch... [Mô tả nhân vật cố định]... --ar 9:16` | `slow subtle zoom-in, faint flicker of star dots, minimal motion` |
| **2** | ... | ... | `...` | `...` |
*(Điền đầy đủ đến cảnh cuối cùng)*

### ⚙️ GHI CHÚ DỰNG:
- **Mô tả nhân vật cố định:** [Đoạn tiếng Anh mô tả nhân vật dùng xuyên suốt]
- **Nhạc nền & Giọng đọc:** Nhạc lofi/piano buồn, hoài niệm; giọng đọc nam/nữ miền Bắc trầm ấm, tốc độ 0.9x.
- **Tiêu đề tô vàng ở từ khóa:** [Chỉ rõ từ khóa nào cần highlight vàng trên banner]
```
