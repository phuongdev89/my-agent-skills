# Cẩm Nang Góc Máy & Kiểm Soát Khung Hình Midjourney (Từ Tao Prompts)

Cẩm nang chuyên sâu trích xuất từ tài liệu 57 trang của Tao Prompts về toàn bộ góc máy, tiêu cự, hướng nhân vật và kỹ thuật chống zoom lỗi trong Midjourney.

---

## 1. Hướng Nhìn Của Nhân Vật (Subject Direction)

Tưởng tượng máy quay di chuyển quanh nhân vật theo một vòng tròn 360 độ:

* **`centered view`**: Nhìn thẳng trực diện vào ống kính.
* **`side profile shot`**: Nhìn nghiêng hẳn một bên (góc 90 độ), làm nổi bật đường viền sống mũi, quai hàm.
* **`three quarter profile shot`**: Góc nghiêng 3/4, tạo chiều sâu 3D rõ nét nhất cho khuôn mặt.
* **`back view`**: Nhìn từ sau lưng, đặt người xem vào góc nhìn của nhân vật (giống game góc nhìn thứ ba).
* **`back view three quarter profile`**: Góc nhìn nghiêng 3/4 từ phía sau lưng.
* **`looking over the shoulder`**: Nhân vật quay đầu nhìn qua vai về phía ống kính.

---

## 2. Cự Ly Khung Hình & Thủ Thuật "Bẫy Khung Hình" (Camera Shot & Framing Tricks)

Một vấn đề phổ biến là Midjourney thường tự động zoom mặt và bỏ qua lệnh `fullbody shot` hoặc `medium shot`. Cẩm nang cung cấp các thủ thuật thông minh:

### Cự ly căn bản:
* **`extreme close up shot`**: Cực cận cảnh, tập trung đặc tả chi tiết một bộ phận (ví dụ: `extreme close up shot on the eyes`).
* **`close up shot`**: Cận cảnh khuôn mặt, thể hiện cảm xúc sâu sắc.
* **`extreme long shot` / `long shot`**: Toàn cảnh từ rất xa, chủ thể nhỏ bé giữa không gian mênh mông (rất hợp với `--ar 16:9`, `--ar 2:1`, `--ar 5:2`).

### 💡 Thủ thuật Medium Shot (Cắt ngang hông):
* Nếu chỉ viết `medium shot`, AI thường chỉ vẽ ngực trở lên.
* **Giải pháp**: Hãy mô tả một vật thể nằm ở thắt lưng!
  * *Ví dụ:* `medium shot from the waist up... The statue has a short sword on its waist` ➔ Bắt buộc AI phải lùi máy quay để thấy thanh kiếm!

### 💡 Thủ thuật Fullbody Shot (Lấy trọn vẹn toàn thân):
* Nếu dùng khung hình ngang hoặc chỉ viết `fullbody shot`, AI hay zoom vào mặt hoặc cắt ngang chân.
* **Giải pháp 1 (Mô tả đỉnh đầu + Bàn chân cùng lúc)**:
  * *Ví dụ 1:* `fullbody shot... The statue is wearing a helmet and the statue's feet are on a pedestal` (Đội mũ giáp + chân đứng trên bệ).
  * *Ví dụ 2:* `She has a ponytail and is wearing black kneepads and white volleyball shoes` (Tóc đuôi ngựa + băng bảo vệ gối + giày bóng chuyền trắng).
* **Giải pháp 2 (Dùng khung hình dọc)**: Sử dụng `--ar 9:16` để tỷ lệ dọc tự nhiên ép khung hình bao quát toàn thân.

### ⚠️ Cái Bẫy Của Wide Angle Shot (Góc Rộng):
* Nếu bạn yêu cầu `wide angle shot` nhưng lại mô tả chi tiết khuôn mặt (như `she has tired eyes` hay `smiling face`), **Midjourney sẽ ưu tiên chi tiết mặt và tự động zoom lại thành cận cảnh!**
* **Cách khắc phục**: Nếu muốn giữ góc rộng, hạn chế mô tả chi tiết micro trên mặt trong prompt gốc, hoặc dùng tính năng Outpainting (Reframe/Zoom-out) trên giao diện Midjourney.

---

## 3. Góc Máy Điện Ảnh (Camera Angle)

* **`low angle shot from below`**: Máy quay đặt thấp dưới tầm mắt hướng lên. Làm nhân vật trông quyền lực, to lớn, mạnh mẽ và kiêu hãnh hơn. *(Lưu ý: Luôn viết đầy đủ "from below" để ổn định nhất).*
* **`high angle shot from above`**: Máy quay đặt trên cao chúc xuống. Làm nhân vật trông nhỏ bé, yếu thế, mong manh. *(Luôn viết đầy đủ "from above").*
* **`overhead shot`**: Máy quay vuông góc từ trên đỉnh đầu nhìn thẳng xuống (chim nhìn), mang tính bao quát, khách quan và tĩnh lặng.
* **`over the shoulder camera angle`**: Góc máy qua vai nhân vật này nhìn về nhân vật kia, chuẩn phim ảnh cho các cảnh hội thoại đối đáp.

---

## 4. Ống Kính & Hiệu Ứng Quang Học (Camera Lens)

Ống kính giống như một bộ lọc thị giác độc đáo:
* **`fish-eye lens` / `extreme fish-eye lens`**: Ống kính mắt cá tạo độ cong cầu hình cầu cực đại, hiệu ứng thị giác ấn tượng, phá cách.
* **`macro lens photography`**: Chụp macro siêu chi tiết côn trùng, cánh hoa, mống mắt.
* **`tilt-shift photography`**: Tạo hiệu ứng mô hình đồ chơi thu nhỏ (miniature toy-like effect), xóa phông trên dưới.
* **`cracked camera lens`**: Hiệu ứng kính vỡ nứt chằng chịt độc lạ ngay trước ống kính.
* **`selfie photo`**: `selfie photo taken by [Nhân vật] on an iPhone --ar 9:16` tạo ảnh tự sướng cực kỳ đời thường và chân thật.

---

## 5. Khung Hình Trong Khung Hình (Frame-in-Frame)

Sử dụng vật thể trong cảnh để tạo khung hình thứ hai bao quanh chủ thể:
* Tạo cảm giác đắm chìm, riêng tư hoặc ngột ngạt:
  * Nhìn qua lỗ cửa sổ kính: `seen through a small rectangular opening inside a cubicle office` (tạo cảm giác tù túng, cô độc).
  * Nhìn qua cửa sổ máy bay: `taken through an airplane window`.
  * Nhìn qua kính viễn vọng: `seen through a telescope`.
  * Trong kén ngủ tương lai: `sleeping inside a small oval pod` (cảm giác ấm cúng hoặc ngột ngạt).

---

## 6. Góc Máy Cho Phong Cảnh (Landscapes)

* **`satellite shot`**: Ảnh chụp từ vệ tinh ngoài không gian.
* **`bird's eye view`**: Góc nhìn từ trên cao xuống toàn cảnh núi non, rừng rậm, cung đường uốn lượn.
* **`ground level shot from below`**: Đặt máy sát mặt đất ngước lên cỏ cây hoa lá.
* **`camera pointing directly up`**: Ống kính hướng thẳng lên bầu trời (ví dụ lá rụng mùa thu rơi thẳng vào ống kính).
* **`panoramic shot`**: Ảnh toàn cảnh siêu rộng với `--ar 3:1`.

---

## 7. Công Thức Kết Hợp (Mix & Match)

Hãy ghép nối: **[Subject Direction] + [Camera Shot] + [Camera Angle] + [Lens]**:
> *Ví dụ:* `ultra wide-angle, side profile shot from the side, low-angle shot from below, photo of a man standing in new york... --ar 16:9 --quality 2`
