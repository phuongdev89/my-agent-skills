---
name: muse-chat
description: Trò chuyện nhiều lượt với Muse (trợ lý cá nhân do Meta xây dựng) qua gateway Muse2API cục bộ — brainstorm ý tưởng, hỏi cơ chế Facebook/Reels. Tự tìm cấu hình theo thứ tự .muse/config.json → biến môi trường MUSE_ENDPOINT_URL / MUSE_API_KEY; chỉ hỏi người dùng endpoint/API key khi cả hai nguồn đều thiếu, hỏi đúng một lần rồi lưu lại.
---

# Muse Chat

Dùng skill này khi người dùng muốn hỏi/discuss/brainstorm với Muse. Muse mạnh nhất với chủ đề Facebook/Meta (Reels, talking-about, gắn nhãn AI, chính sách kiếm tiền) — route các câu hỏi đó về đây. Lưu ý Muse là trợ lý cá nhân do Meta xây dựng, KHÔNG phải đội nội bộ Facebook: không có dữ liệu không công khai, và nó tự đánh dấu phần không chắc chắn — vẫn cần đối chiếu khi ra quyết định.

## Bước 1 — Kiểm tra cấu hình (làm trước tiên, bắt buộc)

Chạy một lệnh duy nhất, script tự đi tìm và gộp cấu hình:

```bash
python "<thư-mục-skill-này>/scripts/muse_chat.py" config show
```

Thứ tự ưu tiên (từng trường gộp dần, thiếu mục nào mới đi tìm mục đó ở nguồn sau):

1. **`<project>/.muse/config.json`** — giá trị đã lưu từ lần hỏi trước, ưu tiên cao nhất.
2. **Biến môi trường cục bộ của máy** — `MUSE_ENDPOINT_URL`, `MUSE_API_KEY`. Endpoint đặt URL gốc (`http://localhost:18610/v1`) hay URL đầy đủ (`.../v1/chat/completions`) đều được — script tự chuẩn hoá.

Riêng `account_id` (dạng `acc_…`) do người dùng tự cung cấp, chỉ lưu qua `config set`, không đọc từ biến môi trường. Model cố định `muse-chat`, không cần cấu hình.

Kết quả:

- **Đủ `endpoint` + `api_key`** (từ bất kỳ nguồn nào): dùng luôn, KHÔNG hỏi lại người dùng. `config show` in kèm nguồn từng giá trị (`[file config]` / `[biến môi trường ...]`) và thoát 0.
- **Thiếu (thoát 2)**: hỏi người dùng **đúng những mục còn thiếu**:
  1. "API endpoint là gì?" (gợi ý mặc định: `http://localhost:18610/v1/chat/completions` — gateway Docker cục bộ)
  2. "API key là gì?" (dạng `m2a-…`; hỏi thêm account ID dạng `acc_…` nếu người dùng có)

  Sau đó lưu vào `.muse/` bằng lệnh (không tự tay ghi file để tránh làm hỏng JSON/thread đang có):

  ```bash
  python "<thư-mục-skill-này>/scripts/muse_chat.py" config set --endpoint "http://localhost:18610/v1/chat/completions" --api-key "m2a-..." --account-id "acc_..."
  ```

  Nếu người dùng muốn giữ thông tin trong biến môi trường thì hướng dẫn đặt `MUSE_ENDPOINT_URL` / `MUSE_API_KEY` (setx trên Windows hoặc export trong shell) — khỏi cần lưu file.

  Xác nhận `.muse/` đã nằm trong `.gitignore` của project (file chứa key bí mật). Không bao giờ in nguyên key ra hội thoại, log hay lệnh — script tự che key khi hiển thị. Muốn xem cấu hình hiệu dụng: `config show`; muốn đổi: chạy lại `config set`.

## Bước 2 — Gửi tin và nhận trả lời

Script chỉ dùng thư viện chuẩn Python, không cần cài package. Với tin dài/tiếng Việt, viết nội dung ra file UTF-8 bằng Write tool rồi gửi bằng `--file` (ổn định nhất trên Windows):

```bash
python "<thư-mục-skill>/scripts/muse_chat.py" ask --file ".scratch/muse/<topic>/draft.txt" --topic "<topic>"
python "<thư-mục-skill>/scripts/muse_chat.py" ask --text "Câu ngắn gọn" --topic "<topic>"
python "<thư-mục-skill>/scripts/muse_chat.py" ask --file draft.txt --new-thread   # mở thread mới
```

Mỗi lượt `ask` chỉ gửi MỘT tin user mới — Muse giữ lịch sử hội thoại phía server theo thread. Script tự: gửi `"stream": true` (bắt buộc với gateway này), parse SSE, khử bản replay lặp, lưu `msg_NN.json` / `reply_NN.raw` / `reply_NN.txt` vào `.scratch/muse/<topic>/`, in trả lời sạch ra stdout kèm đường dẫn.

## Thread

- Lần đầu (chưa có thread trong config) script gửi `"thread": null` → gateway tạo thread mới; script tự trích URL `https://muse.ai/thread/<uuid>` từ response và lưu vào config. Các lần sau tự dùng lại.
- Người dùng có thể mở URL thread trên muse.ai để đọc lại toàn bộ hội thoại — đưa thread này cho người dùng sau lượt đầu tiên.
- `--new-thread` khi người dùng muốn chủ đề riêng (kênh mới, đề tài mới).

## Gotchas (đã xử lý trong script, nhưng cần biết khi đọc kết quả)

- **Stub reply**: Muse hay trả 1 dòng ngắn kiểu "để tôi kiểm tra lại" — đó KHÔNG phải trả lời thật. Script tự cảnh báo khi reply ngắn bất thường; khi đó gửi một tin nhắc ngắn ("nối tiếp nhé") thì bản đầy đủ sẽ tới lượt sau. Đôi khi bản đầy đủ chỉ hiện trên UI muse.ai — người dùng có thể dán lại.
- Trước câu hỏi lớn, nhắc Muse **"trả lời trong ĐÚNG MỘT TIN NHẮN, đừng tách nhiều tin"** và yêu cầu đánh dấu rõ điều gì chắc chắn / điều gì là giả định.
- `stream: false` trả tin CŨ (stale) — đừng bao giờ dùng.
- HTTP 200 chưa phải trả lời đầy đủ — luôn kiểm tra nội dung reply (độ dài, có phải stub không) trước khi kết luận.

## Nghiệm thu mỗi lượt

1. Reply có nội dung trọn vẹn (không phải stub 1 dòng).
2. File `msg_NN.json` + `reply_NN.txt` đã ghi vào `.scratch/muse/<topic>/`.
3. Báo cho người dùng: thread URL (lần đầu), đường dẫn transcript, và nội dung trả lời.
