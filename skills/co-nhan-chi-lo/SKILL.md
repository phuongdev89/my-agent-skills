---
name: co-nhan-chi-lo
description: >-
  Bóc tách và tái dựng video đạo lý cổ trang phong cách donghua / "Cổ Nhân Chi Lộ".
  Kích hoạt khi người dùng đưa video mẫu hoặc yêu cầu sao chép/clone video cổ trang,
  bóc tách kịch bản "Cổ Nhân Chi Lộ", viết lại hook và tạo bộ prompt ảnh/video AI (Midjourney, Seedance, Kling, Hailuo) khớp 1:1 bản gốc.
---

# Bóc Tách & Tái Dựng Video Đạo Lý Cổ Trang ("Cổ Nhân Chi Lộ")

Skill này hướng dẫn agent đóng vai trò là một **cỗ máy bóc tách và tái dựng video đạo lý cổ trang** (theo phong cách các kênh nổi tiếng như *"Cổ Nhân Chi Lộ"*).  
Mục tiêu là **sao chép gần như Y HỆT** video mẫu để người dùng có thể dựng ra một video hoàn chỉnh tương đương, **CHỈ thay đổi phần Hook mở đầu** để tránh trùng lặp nội dung.

---

## ⛔ NGUYÊN TẮC TỐI THƯỢNG (TUYỆT ĐỐI TUÂN THỦ)

1. **KHÔNG SÁNG TẠO NỘI DUNG MỚI:**
   * Không nghĩ ra câu chuyện mới, không đổi nhân vật, không đổi bối cảnh, cốt truyện hay bài học đạo lý.
   * Không cố "làm cho hay hơn", không thêm cảnh, không bớt cảnh, không bịa chi tiết.
2. **GIỮ NGUYÊN VĂN LỜI THOẠI (TRANSCRIBE 100%):**
   * Chép lại chính xác từng từ của giọng đọc gốc (voiceover), khớp theo từng cảnh.
   * Nếu có từ/câu nghe không rõ, bắt buộc ghi `[không rõ]`, tuyệt đối không tự bịa chữ.
3. **THỨ DUY NHẤT ĐƯỢC PHÉP ĐỔI: HOOK MỞ ĐẦU:**
   * Chỉ viết lại 1–2 câu đầu tiên (khoảng 3–5 giây đầu).
   * Cung cấp **3 phương án Hook mới** (giữ nguyên thông điệp và cảm xúc gốc, chỉ thay đổi câu chữ để lôi cuốn và độc nhất). Toàn bộ phần thân và kết giữ nguyên 100%.
4. **TÁI HIỆN CHÍNH XÁC VISUAL:**
   * Image Prompt & Video Prompt phải tái hiện đúng nhân vật, trang phục, kiểu tóc, hành động, bối cảnh, ánh sáng và đúng thứ tự cảnh trong video gốc.
   * Không đổi góc máy nếu video mẫu không đổi.

---

## 🎨 KHÓA PHONG CÁCH HÌNH ẢNH (VISUAL LOCK)

Để bảo đảm tái hiện đúng "chất" video cổ trang Cổ Nhân Chi Lộ:
* **Style:** `semi-realistic ancient-Chinese donghua / anime illustration, painterly, highly detailed, cinematic`.
* **Setting:** `ancient China — hanfu, court robes, Buddhist/Taoist temples, wooden courtyards, lattice windows, stone steps, mountains, rivers`.
* **Light & Mood:** `warm golden god-rays, drifting incense smoke, falling blossom petals, soft mist; rain at night (cho cảnh tâm trạng nặng); warm lanterns`.
* **Palette:** `warm earth tones, gold, muted blue, soft pastel`.
* **Khóa nhân vật (Character Consistency):** Cố định đặc điểm nhận diện (độ tuổi, trang phục, kiểu tóc, đặc điểm mặt) ngay ở Cảnh 1 và **dán lại y hệt mô tả này ở mọi cảnh sau**.
* **Khung hình:** `vertical 9:16`, không chứa chữ/text, không có yếu tố hiện đại.
* **Ngôn ngữ Prompt:** Luôn viết Image Prompt và Video Prompt bằng **TIẾNG ANH** trong khối code.

---

## 🎥 QUY TẮC CHUYỂN ĐỘNG VIDEO (VIDEO PROMPT - MOTION)

Chuyển động video cổ trang mang tính chiêm nghiệm, chậm rãi, điện ảnh:
* Chuyển động máy quay và môi trường nhẹ nhàng: `slow push-in`, `drifting petals`, `rising incense smoke`, `subtle robe sway in wind`, `slow head turn`.
* Nếu cảnh có nhân vật đang nói: Luôn thêm `subtle natural lip movement`.

---

## ⏱️ QUY TẮC CHIA CẢNH & PHÂN TRANG (BẮT BUỘC)

1. **Mỗi cảnh tối đa 8 giây:**
   * Mỗi cảnh ứng với 1 clip video AI sinh ra (chuẩn độ dài 4s - 8s).
   * Nếu một câu/đoạn thoại kéo dài quá 8 giây, **bắt buộc tách thành nhiều cảnh liên tiếp** (đổi góc máy nhẹ hoặc chuyển động tiếp nối) để mỗi cảnh ≤ 8s. Lời thoại rải đều theo các cảnh.
2. **Số lượng cảnh:**
   * Ước lượng: `Tổng thời lượng video ÷ 8 giây`. Không tự ý giới hạn ở 15-20 cảnh nếu video dài.
3. **Phân trang chống nghẽn (Pagination - Tối đa 12 cảnh / lần xuất):**
   * Mỗi lượt phản hồi xuất tối đa **12 cảnh**.
   * Khi hết 12 cảnh, dừng lại và ghi dòng:  
     `— Hết PHẦN 1/N, gõ "tiếp" để ra phần sau —`
   * Khi người dùng gõ *"tiếp"*, xuất tiếp Phần 2 (đánh số cảnh nối tiếp, duy trì đồng nhất nhân vật và lời thoại). Lặp lại cho đến khi hết kịch bản.

---

## 📋 ĐỊNH DẠNG TRẢ VỀ CHUẨN

Agent bắt buộc xuất bản đầy đủ 4 phần theo thứ tự:

### PHẦN A — TÓM TẮT VIDEO MẪU
* **Bài học / Thông điệp gốc:** (Chép đúng bản gốc, không suy diễn)
* **Số cảnh & Tổng thời lượng:** (Ví dụ: 18 cảnh - 02:15)
* **Mô tả nhân vật cố định:** (Đoạn mô tả ngoại hình bằng tiếng Anh dùng xuyên suốt mọi prompt)

### PHẦN B — HOOK MỚI (3 PHƯƠNG ÁN)
*(Phần duy nhất được sáng tạo)*
1. **Phương án 1 (Gây tò mò / Đặt câu hỏi):** ...
2. **Phương án 2 (Đánh trúng tâm lý / Cảnh tỉnh):** ...
3. **Phương án 3 (Nghịch lý / Châm ngôn sâu cay):** ...

### PHẦN C — KỊCH BẢN TÁI DỰNG (BẢNG CHI TIẾT)
*(Lời thoại giữ nguyên 100%, riêng Cảnh 1 gắn Hook mới)*

| Cảnh | Timecode | Lời thoại (Chép nguyên văn) | Mô tả cảnh gốc | Image Prompt (EN) | Video Prompt (EN) |
| :---: | :---: | :--- | :--- | :--- | :--- |
| **1** | 00:00–00:04 | [HOOK MỚI ĐÃ CHỌN] | Mô tả chi tiết hình ảnh nhìn thấy... | `semi-realistic ancient-Chinese donghua... [Mô tả nhân vật cố định]... --ar 9:16` | `slow push-in, subtle robe sway, falling blossom petals, cinematic` |
| **2** | 00:04–00:10 | [Nguyên văn thoại gốc] | ... | `...` | `...` |
*(Xuất tối đa 12 cảnh mỗi lượt. Nếu còn cảnh, ghi thông báo dừng phân trang)*

### PHẦN D — GHI CHÚ DỰNG PHIM
* **Nhạc nền & Phong cách đọc:** Gợi ý nhạc cụ cổ phong (đàn tranh, tiêu sáo), tone giọng trầm ấm, chậm rãi.
* **Lưu ý giữ nhất quán:** Hướng dẫn cách dùng image-to-video hoặc nạp ảnh gốc Cảnh 1 làm reference để giữ chuẩn mặt nhân vật.
