---
name: muse-video
description: Tạo video qua gateway Muse2API (muse-video) — text-to-video và image-to-video (ảnh first-frame), luôn chạy bất đồng bộ kèm poll task đến khi xong; tự nạp cấu hình theo thứ tự .muse/config.json → biến môi trường → .env, hỗ trợ pin account_id qua X-Account-ID.
---

# Muse Video

Dùng skill này khi người dùng yêu cầu tạo video qua Muse2API. Đây là API gateway riêng; không phải Aidancing. Dựa theo API reference Muse2API v0.2.0: `POST /videos` luôn trả task async, poll `GET /videos/{task_id}` đến khi `succeeded` rồi tải `result.url`. Skill gọi gateway tại URL người dùng cấu hình và không đổi nhà cung cấp khi lỗi.

## Bước 1 — Cấu hình (làm trước tiên, bắt buộc)

Script tự đi tìm cấu hình theo thứ tự ưu tiên **từng trường gộp dần** (thiếu mục nào mới đi tìm mục đó ở nguồn sau):

1. **`<project>/.muse/config.json`** — file dùng chung với `muse-chat` và `muse-image`; đã `config set` cho muse-chat một lần là skill này dùng luôn, không cần cấu hình lại.
2. **Biến môi trường** — `MUSE_ENDPOINT_URL`, `MUSE_API_KEY`, `MUSE_ACCOUNT_ID` (tên riêng của skill: `MUSEAI_VIDEO_*` làm dự phòng).
3. **`.env`** tại thư mục làm việc hoặc repo skill (đựng các key cùng tên, ưu tiên thấp nhất).

`account_id` (dạng `acc_…`, tùy chọn) cũng nạp theo đúng thứ tự trên, cộng thêm cờ `--account-id` trên lệnh `create` (cao nhất, ghi đè mọi nguồn). Ý nghĩa theo API reference: pin request vào đúng một account trong pool và **tắt failover**. Không set thì gateway tự chọn account.

Kiểm tra nhanh đã đủ cấu hình chưa: chạy một lệnh `create` thật (xem Bước 3) — thiếu endpoint/key script thoát lỗi ngay với thông báo rõ. Script không có lệnh config riêng; muốn lưu cấu hình vào `.muse/config.json` thì dùng `muse_chat.py config set` (chia sẻ chung) hoặc tự đặt biến môi trường.

Endpoint chấp nhận URL gốc (`http://host:18610`, `.../v1`) lẫn URL chat (`.../v1/chat/completions`) — script tự chuẩn hóa về `/v1`. Gửi key bằng `Authorization: Bearer ...`; không in key, không ghi key vào log, không đặt key trực tiếp trong lệnh. Không dùng admin key nếu chỉ cần gọi API video.

## Chọn tham số

- `--prompt`: mô tả video (bắt buộc).
- `--image`: ảnh first-frame cho image-to-video — nhận http(s) URL (gửi nguyên) hoặc đường dẫn file local (script tự đổi thành data URL).
- `--size`: tỷ lệ khung hình dạng `16:9` hoặc `9:16` — chỉ là gợi ý cho upstream, không bảo đảm chính xác.
- `--duration`: độ dài 1-60 giây (giới hạn của API reference).

Video tốn thời gian hơn ảnh đáng kể — mặc định timeout poll 900 giây (`MUSEAI_VIDEO_TIMEOUT`), poll mỗi 5 giây (`MUSEAI_VIDEO_POLL_INTERVAL`). Nếu lệnh `create` timeout nhưng task vẫn chạy trên server, lấy task id từ stderr rồi dò lại bằng lệnh `status` thay vì tạo lại task mới (tránh tốn quota).

## Chạy CLI

Script dùng thư viện chuẩn Python, không cần cài package. Đặt output trong session riêng, ví dụ `.scratch/yyyy-mm-dd_muse-video_ten-tac-vu/`; không ghi đè video nguồn.

```bash
$SkillDir="<đường-dẫn-thư-mục-skill-muse-video>"
python "$SkillDir/scripts/muse_video.py" create --prompt "Quả bóng đỏ lăn trên sàn gỗ, ánh sáng tự nhiên" --size 16:9 --duration 5 --output .scratch/session/bong-do.mp4
python "$SkillDir/scripts/muse_video.py" create --prompt "Người mẫu quay đầu và mỉm cười" --image .scratch/session/frame-dau.png --size 9:16 --duration 8 --output .scratch/session/quay-dau.mp4
python "$SkillDir/scripts/muse_video.py" create --prompt "Sóng biển vỗ bờ cát, cận cảnh" --account-id acc_xxx --output .scratch/session/song-bien.mp4
python "$SkillDir/scripts/muse_video.py" status <task_id> --output .scratch/session/ket-qua.mp4
```

Chạy `python "$SkillDir/scripts/muse_video.py" --help` để xem đầy đủ tùy chọn. `create` gọi JSON `POST /videos` rồi tự poll `GET /videos/{task_id}`; `status` chỉ dò task và in trạng thái — kèm `--output` thì tải video khi task đã `succeeded`.

## Xử lý kết quả và nghiệm thu

- Task thành công có `result.url` trỏ về media gateway (`/v1/media/{name}` phục vụ file không cần auth). Script tải về `--output`; nếu nhận URL tương đối, tự ghép với origin của API. Không gửi API key tới host khác nếu URL kết quả trỏ ra ngoài host gateway.
- Khi lỗi HTTP, hiển thị mã trạng thái và thông báo lỗi đã lọc; không in header xác thực.
- Sau khi chạy, xác nhận file tồn tại, mở được và xem video để so với yêu cầu. Không coi HTTP thành công là nghiệm thu video.
- Báo phương thức/endpoint, task id, model nếu biết, đường dẫn output và mọi sai khác quan sát được. Không khẳng định độ dài, tỷ lệ hay chuyển động đã đạt nếu chưa kiểm tra.

Tài liệu endpoint được mô tả trong API reference Muse2API: `/videos`, `/videos/{task_id}`, `/media/{name}`.
