# Cinematic & Photorealistic AI Images Guide (Từ Tao Prompts)

Cẩm nang chuyên sâu trích xuất từ tài liệu 50 trang của Tao Prompts về tạo ảnh siêu thực (Photorealistic) và điện ảnh (Cinematic) trong Midjourney.

---

## 1. Cấu Trúc Prompt & Quy Luật Trọng Số Thứ Tự Từ (Word Order Matters!)

### Quy luật cốt lõi:
* **Từ khóa đứng trước có trọng số lớn hơn**: Những từ/cụm từ đặt ở đầu prompt sẽ được mô hình AI ưu tiên thể hiện mạnh nhất.
* **Kỹ thuật Đảo Vị Trí (Switch Word Order)**: Nếu bạn muốn góc máy cụ thể (ví dụ `low angle shot`) mà AI vẫn vẽ góc ngang bình thường, hãy **chuyển cụm từ góc máy lên đầu prompt**:
  * *Thất bại:* `german barbarian, with dark striped face paint, scary, roman empire, Extreme low angle shot from below...`
  * *Thành công:* `Extreme low angle shot from below, german barbarian, with dark striped face paint, scary, roman empire...`
* **Quy tắc phối màu trang phục (Color Bleeding Trap)**: Màu sắc xuất hiện trước sẽ dễ bị AI gán cho trang phục lớn nhất.
  * *Sai:* `wearing a pink tie, a blue shirt, and a khaki blazer` ➔ Toàn bộ áo vest bị biến thành màu hồng!
  * *Đúng:* `wearing a khaki blazer, a blue shirt, and a pink tie` ➔ Áo vest giữ màu kaki, cà vạt màu hồng.

### Template Prompt Chuẩn:
```text
[Camera Angle / Shot] [Subject] [Details / Action] [Mood] [Style / Genre] [Lighting] [Color Grading] [Camera Lens / Film Stock] [Parameters]
```

* **Đầu Prompt (Start)**: Chủ thể (Subject), Góc máy quan trọng (Camera angle).
* **Giữa Prompt (Middle)**: Phong cách (Style keywords), Thể loại (Genre), Ánh sáng (Lighting).
* **Cuối Prompt (End)**: Chỉnh màu (Color grading), Ống kính & Thông số máy ảnh (Camera specs, Film stock), Tham số (`--ar`, `--s`, `--style raw`).

---

## 2. Ánh Sáng Điện Ảnh (Cinematic Lighting)

* **Thời điểm trong ngày**: `{morning, noon, sunset, night time}`.
* **Golden Hour**: Ánh sáng vàng dịu ngọt hoàng hôn/bình minh (`summer golden hour`).
* **Thời tiết tạo mood**: `{sunny, overcast, foggy, rainy}`.
* **Hướng sáng & Vị trí nguồn sáng**:
  * `natural lighting`: Ánh sáng ban ngày chân thực.
  * `light from behind`: Nguồn sáng chiếu từ sau lưng chủ thể.
  * `silhouette lighting`: Ánh sáng tạo bóng đen ngược sáng ma mị, giấu chi tiết mặt.
  * `silhouette lighting and side light`: Ngược sáng kết hợp viền sáng một bên mặt.
  * `lighting through glass / window`: Ánh sáng xuyên qua cửa sổ/kính kèm bóng đổ kẻ sọc lên mặt (`shadows on face`).
  * `volumetric lighting / light rays`: Các luồng tia sáng quét qua không gian khói sương.
* **Màu ánh sáng đặc biệt**:
  * `neon`: Ánh sáng neon rực rỡ, bão hòa cao (`Futuristic japanpunk, purple and blue`).
  * `blacklight`: Ánh sáng cực tím phát quang huyền ảo (`glow in the dark effect`).
  * `whitelight`: Ánh sáng trắng tinh khiết tạo tia sáng mạnh.
  * `candle light`, `studio lighting`, `instagram lighting`.

---

## 3. Màu Sắc & Phim Điện Ảnh (Color Grading & Film Stock)

* **Tông màu cơ bản**:
  * `cool-toned color grading`: Tông xanh & xám, lạnh lùng, nghiêm nghị, trầm buồn.
  * `warm-toned color grading`: Tông vàng, cam, nâu ấm cúng, hoài niệm.
  * `black and white photo`: Trắng đen cổ điển, vượt thời gian (`national geographic`).
  * `muted color tones`: Giảm độ bão hòa, tạo chất điện ảnh gritty, sâu lắng (`dark blue and mahogany color tones`).
  * `vintage color grading`: Phong cách retro film thập niên 70-90.
* **Bảng màu phim nổi tiếng**:
  * `desaturated colors`: Tông màu bạc, u ám, tuyệt vọng, chiến tranh hoặc bùn lầy.
  * `pastel colors`: Tông phấn hồng, xanh nhạt, tươi sáng, mộng mơ (`cinestill 50`).
* **Film Stock & Máy ảnh kinh điển tạo chất hạt siêu thực**:
  * `kodak portra 160 / 400 / 800`: Tiêu chuẩn vàng chân dung, da người chân thật, mềm mại.
  * `cinestill 50 / cinestill 800t`: Đậm chất điện ảnh hoài cổ, quầng sáng ấm quanh bóng đèn.
  * `lomochrome`: Màu sắc dị biệt, siêu thực, phá cách.
  * `kodak ektar 100`, `fujifilm`, `velvia`, `agfa vista`.
  * `shot on a canon EOS`, `shot on an iphone --style raw`, `polaroid`, `disposable camera`.
* **Tiêu cự (Focal Length)**: Thêm `35 mm` hoặc `50 mm` vào cuối prompt để xóa bỏ cảm giác "nhựa AI" và tăng tối đa tính chân thực quang học.

---

## 4. Phong Cách, Đạo Diễn & Cảm Xúc (Styling & Genre)

* **Thể loại phim**: `{horror, fantasy, scifi, indie, western, dystopian}` film.
* **Phong cách Đạo diễn**:
  * `quentin tarantino color palette`: Màu sắc pop culture tương phản mạnh, táo bạo.
  * `wes anderson color palette`: Tông pastel đối xứng, vintage, retro ngọt ngào.
* **Hậu tố phong cách (Suffix Tokens)**:
  * Hậu tố `-punk`: `cyberpunk`, `spacepunk`, `steampunk`, `japanpunk`.
  * Hậu tố `-core`: `samuraicore`, `legioncore`, `greencore`, `bluecore`, `yellowcore`.
* **Biểu cảm chân dung (Emotions)**:
  * Midjourney mặc định mặt người hơi vô cảm hoặc cười nhẹ. Hãy chỉ định rõ: `{happy, somber, tired, scared} expression` để ảnh có hồn.

---

## 5. Tham Số Midjourney Tối Ưu (Parameters)

* **`--ar` (Aspect Ratio)**:
  * `--ar 16:9`: Tỷ lệ màn ảnh rộng điện ảnh chuẩn.
  * `--ar 5:2` hoặc `--ar 2.39:1`: Siêu rộng (Ultra-wide cinematic).
  * `--ar 9:16`: Tỷ lệ dọc chuẩn Facebook Reels, TikTok, Story.
  * `--ar 4:3`: Tỷ lệ ảnh cổ điển hoặc máy ảnh medium format.
* **`--style raw`**: Kích hoạt chế độ Raw Mode. Giúp Midjourney bớt tự ý "vẽ đẹp lung linh kiểu tranh vẽ", bám sát mô tả nhiếp ảnh thực tế và ít bị làm mịn da quá đà.
* **`--s` (Stylize - từ 0 đến 1000)**:
  * `--s 0` - `--s 50`: Tự nhiên nhất, bám sát ảnh chụp đời thực, ít thêm thắt nghệ thuật.
  * `--s 250`: Cân bằng vàng (mức khuyên dùng cho cinematic).
  * `--s 500` - `--s 1000`: Nghệ thuật hóa cao, lộng lẫy nhưng có thể mất chất thật.
