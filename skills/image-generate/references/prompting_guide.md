# Cẩm Nang Prompting Tạo Ảnh KOC & Sản Phẩm (Prompting Guide)

Tài liệu quy chuẩn kỹ thuật xây dựng câu lệnh (Prompt Engineering) chuyên sâu cho video ngắn (TikTok, YouTube Shorts, Reels) chuẩn tỷ lệ dọc 9:16.

---

## 1. Cấu Trúc Khung Prompt Chuẩn (Master Prompt Formula)

Một prompt tạo ảnh chất lượng cao cần tuân thủ cấu trúc 5 tầng sau:

```
[Chủ thể chính & Hành động] + [Chi tiết sản phẩm / Trang phục] + [Góc máy & Khung hình 9:16] + [Bối cảnh & Ánh sáng Studio] + [Chất lượng ảnh & Phong cách thể hiện]
```

### Ví dụ chuẩn:
> *"Một nữ KOC người Việt trẻ trung khoảng 22 tuổi, nụ cười tươi tắn tự nhiên, đang cầm trên tay và giới thiệu chiếc áo thun polo màu xanh navy phối sọc trắng ở cổ. Vải áo cotton gai rõ từng thớ sợi dệt sắc nét, logo thêu tinh tế trước ngực. Khung hình chụp chân dung nửa người khổ dọc 9:16, góc máy ngang tầm mắt, ống kính 85mm f/1.8 tạo độ sâu trường ảnh, hậu cảnh quán cà phê phong cách tối giản mờ ảo (bokeh mềm mại). Ánh sáng tự nhiên buổi sáng dịu nhẹ kết hợp đèn studio hắt sáng dịu lên gò má. Ảnh chụp chân thực (photorealistic), chuẩn màu da người châu Á, sắc nét 4K."*

---

## 2. Quy Chuẩn Cho Từng Dạng Ảnh Trong Sản Xuất Video

### A. Chân dung KOC (KOC Identity & Facial Consistency)
- **Độ tuổi & Biểu cảm**: Luôn mô tả độ tuổi cụ thể (20-25 tuổi), biểu cảm thân thiện, gần gũi như bạn bè chia sẻ trải nghiệm thực tế.
- **Màu da & Nét mặt**: Chỉ định rõ nét đẹp người Việt/Đông Nam Á tự nhiên, tránh da trắng bạch giả tạo hoặc mặt bị biến dạng kiểu AI hoạt hình.
- **Ánh sáng**: `Soft studio lighting, Rembrandt lighting, natural catchlight in eyes` (ánh sáng tự nhiên phản chiếu trong mắt tạo sức sống).

### B. Ảnh Chi Tiết Sản Phẩm (Product Texture & Fabric Dossier)
Bám sát thông số bóc tách từ ảnh thực tế của sản phẩm:
- **Chất liệu vải**: `breathable pique cotton texture, clearly visible weave pattern, wrinkle-free, premium stitching` (thớ vải dệt nổi rõ, đường may đôi tinh xảo).
- **Chi tiết phụ**: Cổ áo bo dệt, cúc áo khắc chìm, nhãn mác vải, màu sắc chuẩn mã HEX hoặc mô tả chính xác (navy, olive green, pastel beige...).
- **Góc chụp sản phẩm**:
  - `Macro close-up`: Cận cảnh bề mặt chất liệu hoặc đường chỉ may.
  - `Flat lay / Ghost mannequin`: Trải phẳng hoặc ma-nơ-canh tàng hình để thấy rõ toàn phom dáng.

### C. Khung Hình & Tỷ Lệ Dọc (Vertical 9:16 Framing)
- **Tỷ lệ**: Mặc định luôn là `9:16` (1024x1792 hoặc 1080x1920) để vừa khít màn hình điện thoại.
- **Bố cục an toàn (Safe Zone)**:
  - Chủ thể luôn nằm trong 70% trung tâm khung hình.
  - Tránh đặt chi tiết quan trọng ở 15% mép dưới (nơi hiện caption, thanh điều khiển TikTok/Reels) và 10% mép trên (nơi hiện tiêu đề/nút quay lại).

---

## 3. Danh Sách Từ Khóa Cấm & Cần Tránh (Negative Constraints)

Khi gửi prompt tới model AI, cần loại bỏ hoặc đưa vào negative prompt các yếu tố sau:
- **Lỗi giải phẫu cơ thể**: `extra fingers, deformed hands, distorted face, asymmetrical eyes, double heads, unnatural poses`.
- **Chất lượng kém**: `blurry, low resolution, jpeg artifacts, overexposed, oversaturated, plastic skin, 3d render look, cartoon, anime` (nếu cần ảnh người thật).
- **Chi tiết rác**: `watermark, signature, unwanted text, gibberish letters, logo brand counterfeit`.
- **KOC Identity Rule**: Tuyệt đối không mô tả KOC có các đặc điểm robot, cyborg hay ảo hóa. KOC luôn là người thật.
