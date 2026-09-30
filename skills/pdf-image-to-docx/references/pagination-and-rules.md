# 📏 QUY TẮC CĂN TRANG 1:1 & KỶ LUẬT TOÀN VẸN VĂN BẢN (PAGINATION & FIDELITY RULES)

> Bộ nguyên tắc bất di bất dịch đảm bảo tài liệu Word được sinh ra khớp tuyệt đối 100% với bản PDF / Ảnh gốc cả về số trang, cấu trúc lẫn từng câu chữ.

---

## 📐 1. QUY CHUẨN KHỔ GIẤY ENVELOPE C5 & CĂN LỀ NARROW
* **Kích thước trang (Page Size):** Bắt buộc thiết lập khổ **Envelope C5** ($162\text{ mm} \times 229\text{ mm}$ hay $6.38\text{ inch} \times 9.02\text{ inch}$).
* **Căn lề (Margins):** Bắt buộc cấu hình lề **Narrow** ($0.5\text{ inch}$ hay $12.7\text{ mm}$ ở cả 4 cạnh: Top, Bottom, Left, Right).
* **Vùng nội dung khả dụng (Printable Width):** Rộng đúng $5.38\text{ inch}$ ($136.6\text{ mm}$). Mọi bảng biểu, banner, thẻ so sánh phải được tính toán độ rộng nằm trọn vẹn trong $5.38\text{ inch}$ này để không bị tràn lề.

---

## 🎯 2. CÔNG THỨC TOÁN HỌC CĂN TRANG 1:1
* **Quy tắc cơ bản:** Nếu tệp PDF gốc có **$N$ trang**, tệp Word `.docx` sinh ra bắt buộc phải có đúng **$N$ trang**.
* **Số ngắt trang tường minh:** Số lần gọi `add_explicit_page_break(doc)` (tương ứng thẻ XML `<w:br w:type="page"/>`) phải đúng bằng:
  $$\text{Số ngắt trang} = N - 1$$
* **Trang cuối cùng:** Không bao giờ chèn ngắt trang ở cuối trang thứ $N$ (tránh sinh ra 1 trang trắng thừa ở cuối văn bản).
* **Kiểm soát mật độ từng trang:**
  - Font chữ mặc định: Arial 10pt, khoảng cách dòng 1.15, `space_after = 6pt`.
  - Nếu một trang có quá nhiều nội dung, giảm nhẹ `space_after` xuống 3-4pt để nội dung không bị tràn tự nhiên sang trang tiếp theo trước lệnh ngắt trang tường minh.

---

## 🔒 3. KỶ LUẬT SẮT ĐÁ: TUYỆT ĐỐI KHÔNG ĐƯỢC BỊA NỘI DUNG (ZERO HALLUCINATION)
1. **Tuyệt đối không bịa thêm chữ:** Giữ nguyên vẹn 100% câu từ, số liệu, tên riêng, thuật ngữ, dấu câu từ bản scan/ảnh gốc. Tuyệt đối không thêm nhận định cá nhân, không thêm lời bình luận, không "làm mượt câu văn" nếu bản gốc không có.
2. **Không làm mất chữ (No Omission):** Không được bỏ qua bất kỳ đoạn văn, lưu ý, ghi chú, chú thích nào.
3. **Không tóm tắt (No Summarization):** Chuyển đổi chính xác nguyên bản, không tóm tắt hay rút ngắn nội dung tác giả.
4. **Đối chiếu chéo (Cross-grounding):** Khi có đồng thời file `.docx` thô và file `.pdf` scan:
   - Lấy câu từ chính xác từ `.docx` thô (để tránh lỗi chính tả do OCR).
   - Lấy ngắt trang, vị trí bảng, hình vẽ, màu sắc và cấu trúc trình bày từ `.pdf` scan.
5. **Xử lý chỗ mờ:** Nếu gặp chữ quá mờ, ghi chú `[chữ mờ/cần đối chiếu]`, tuyệt đối KHÔNG tự sáng tác ra từ khác thay thế.

---

## 🚫 3. CÁCH LY TIÊU ĐỀ ĐẦU TRANG & CHÂN TRANG (HEADER/FOOTER ISOLATION)
* **Vấn đề thường gặp:** Các công cụ OCR hoặc trích xuất văn bản thô thường vô tình bốc cả dòng tiêu đề chạy ở mép trên (`TÊN SÁCH / TIÊU ĐỀ CHẠY`, `CHƯƠNG 43...`) và số trang ở mép dưới (`256`, `257`) dán vào giữa thân bài.
* **Quy tắc xử lý:**
  1. Loại bỏ 100% các dòng running header và số trang này ra khỏi danh sách văn bản thân bài.
  2. Trong mã nguồn khởi tạo Word (`docx.Document()`), ngắt liên kết `header.is_linked_to_previous = False` và xóa sạch toàn bộ paragraph trong `section.header` và `section.footer`.

---

## 🌲 4. HỆ THỐNG ĐIỀU HƯỚNG BÊN TRÁI (LEFT NAVIGATION TREE)
Người đọc mở tệp Word cần điều hướng nhanh qua thanh bên trái (Navigation Pane / Document Map):
* **Heading 1:** Dành cho Phần lớn (`PHẦN V`) và Tên chương (`CHƯƠNG 43: ...`).
* **Heading 2:** Dành cho các đề mục lớn trong chương (`1. CÔNG CỤ SEO BẮT BUỘC`, `2. CÔNG THỨC TIÊU ĐỀ`, `GHI NHỚ & LÀM NGAY`).
* **Kỹ thuật lồng Banner:** Khi đặt tiêu đề Heading 2 trong ô bảng có màu nền, đoạn văn bên trong ô phải được gán trực tiếp style `Heading 2` (`p.style = doc.styles['Heading 2']`). Word vẫn sẽ nhận diện và đưa vào Navigation Pane bình thường.

---

## 🕵️ 5. XỬ LÝ CÁC DỊ THƯỜNG TRONG BẢN SCAN VẬT LÝ
1. **Trang bị nhảy số (Skipped Pages):**
   - Trong quá trình scan sách vật lý, đôi khi có trang bị quét thiếu (ví dụ: từ trang 268 nhảy thẳng sang 270).
   - Cần kiểm tra tính liên tục của văn bản: nếu câu văn ở cuối trang trước khớp với đầu trang sau, giữ nguyên cấu trúc scan; nếu mất đoạn, kiểm tra file text thô để bổ sung.
2. **Trang scan bị ngược / xoay 180 độ:**
   - Dùng script xoay ảnh lại hoặc đọc ngược để đảm bảo không sót dữ liệu thị giác và bảng biểu của trang đó.
