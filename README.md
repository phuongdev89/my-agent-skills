# My Agent Skills

Bộ sưu tập **14 skill** tôi thường dùng cho lập trình, nghiên cứu, tự động hóa trình duyệt và sản xuất nội dung bằng AI — từ lấy dữ liệu sản phẩm đến tạo ảnh, giọng đọc và xử lý video.

Repository chứa hướng dẫn cùng script và tài liệu hỗ trợ. Cài qua [Skills CLI](https://github.com/vercel-labs/skills), sau đó sử dụng trong coding agent của bạn.

## Cài đặt nhanh

Cần có Node.js/npm (để chạy `npx`), Git và một agent được Skills CLI hỗ trợ.

```bash
npx skills add https://github.com/phuongdev89/my-agent-skills
```

Chạy trong terminal tương tác để chọn một hoặc nhiều skill và agent đích theo menu của CLI. Không thêm `--all` nếu bạn muốn tự chọn. Mặc định cài theo project; thêm `-g` để cài ở phạm vi người dùng.

### Xem danh sách trước khi cài

```bash
npx skills add phuongdev89/my-agent-skills --list
```

### Cài một hoặc nhiều skill

```bash
npx skills add phuongdev89/my-agent-skills --skill ffmpeg
npx skills add phuongdev89/my-agent-skills --skill image-generate video-edit video-transcribe
```

### Chọn agent đích

```bash
npx skills add phuongdev89/my-agent-skills --skill ffmpeg --agent codex claude-code
```

### Cài tất cả skill cho một agent

```bash
npx skills add phuongdev89/my-agent-skills --skill "*" --agent codex
```

### Cài global

```bash
npx skills add phuongdev89/my-agent-skills --skill ffmpeg --agent codex -g
```

> `--all` có nghĩa là cài **tất cả skill cho tất cả agent**, không chỉ chọn toàn bộ skill. Nếu môi trường không hỗ trợ symlink, dùng `--copy`. Các tùy chọn do [Skills CLI](https://github.com/vercel-labs/skills#readme) cung cấp, không phải installer riêng trong repo.

## Danh mục skill

Bấm vào tên để đọc quy trình, điều kiện chạy và các tài nguyên đi kèm.

| Skill | Công dụng | Điều kiện đáng chú ý |
| --- | --- | --- |
| [browser-skill](skills/browser-skill/SKILL.md) | Điều khiển trình duyệt Chromium, thao tác trang và kiểm thử UI | CLI `bsk` và browser extension |
| [code-review](skills/code-review/SKILL.md) | Review thay đổi theo tiêu chuẩn code và yêu cầu/spec | Git, điểm so sánh; workflow có sub-agent |
| [diagnosing-bugs](skills/diagnosing-bugs/SKILL.md) | Chẩn đoán lỗi và suy giảm hiệu năng có hệ thống | Môi trường tái hiện và kiểm tra lỗi |
| [research](skills/research/SKILL.md) | Nghiên cứu nguồn đáng tin cậy và lưu kết quả Markdown | Truy cập nguồn; workflow có background agent |
| [graphify](skills/graphify/SKILL.md) | Biến code và tài liệu thành knowledge graph có thể truy vấn | Runtime graphify và phụ thuộc theo loại dữ liệu |
| [crawl-shopping-product](skills/crawl-shopping-product/SKILL.md) | Lấy thông tin sản phẩm Shopee, TikTok Shop, Lazada | Python, Crawl4AI, endpoint LLM theo cấu hình |
| [image-generate](skills/image-generate/SKILL.md) | Tạo/chỉnh sửa ảnh, ảnh KOC và sản phẩm | Tool tạo ảnh của agent hoặc API được cấu hình |
| [gemini-tts](skills/gemini-tts/SKILL.md) | Tạo giọng đọc qua Gemini hoặc gateway tương thích | Python và thông tin truy cập provider |
| [vbee-tts](skills/vbee-tts/SKILL.md) | Tạo giọng đọc tiếng Việt qua Vbee | Python và tài khoản/API Vbee |
| [vieneu-tts](skills/vieneu-tts/SKILL.md) | Tạo giọng tiếng Việt cục bộ bằng VieNeu-TTS | Python, model và tài nguyên máy phù hợp |
| [video-download](skills/video-download/SKILL.md) | Tải video, audio, phụ đề và metadata | yt-dlp; FFmpeg tùy tác vụ |
| [video-transcribe](skills/video-transcribe/SKILL.md) | Phiên âm và xuất SRT, VTT, TXT, JSON | Python; chọn Groq, Gemini hoặc faster-whisper |
| [video-edit](skills/video-edit/SKILL.md) | Cắt, ghép, resize, overlay, đổi tốc độ video | FFmpeg/ffprobe |
| [ffmpeg](skills/ffmpeg/SKILL.md) | Chuyển đổi, nén và xử lý video/audio | FFmpeg |

## Sử dụng sau khi cài

Mở agent tại project cần làm việc; nếu skill chưa xuất hiện, mở lại phiên hoặc làm mới danh sách theo cơ chế của agent. Gọi tên skill trong yêu cầu, ví dụ:

- “Dùng code-review để review thay đổi so với main.”
- “Dùng video-edit cắt video này từ giây 5 đến giây 15.”
- “Dùng video-transcribe tạo phụ đề SRT cho video này.”
- “Dùng vbee-tts đọc đoạn văn này thành giọng tiếng Việt.”

Cách gọi slash command hoặc tự động kích hoạt tùy agent. Không phải agent nào cũng hỗ trợ cùng một cú pháp.

## Tương thích và giới hạn

Skills CLI hỗ trợ nhiều agent, nhưng **cài được file không đồng nghĩa workflow đã chạy thành công trên mọi agent**.

- Mỗi skill có `SKILL.md` với `name` và `description`; script/reference được đặt cạnh hướng dẫn.
- Các workflow có sub-agent, browser extension hoặc tool tạo ảnh cần khả năng tương ứng từ môi trường chạy.
- Cài skill không tự động cài Python package, FFmpeg, browser extension hoặc cấp quyền API.
- Chưa có kiểm thử end-to-end cho toàn bộ 14 skill trên từng agent; xem [ghi chú tương thích](docs/COMPATIBILITY.md).
- Kết quả kiểm tra bằng validator chỉ xác nhận cấu trúc/frontmatter cơ bản, không chứng minh provider hoạt động hoặc chất lượng media.

## Cấu hình và an toàn

Đọc phần thiết lập trong skill trước khi chạy. Chỉ cấu hình biến môi trường mà skill đó yêu cầu; không cần cung cấp key cho những skill không sử dụng API.

- Không commit API key, token, cookie, file `.env` hoặc dữ liệu đăng nhập.
- Kiểm tra file trước khi `git add`; không mặc định repository đã có bộ lọc secret tự động.
- API tạo ảnh, TTS và phiên âm có thể phát sinh phí hoặc gặp quota.
- Chỉ tải/crawl nội dung bạn có quyền sử dụng; tuân thủ điều khoản của nền tảng.
- Với clone giọng, dùng dữ liệu giọng nói có sự cho phép.
- Các workflow có quy tắc `scratch/` cần giữ input/output và file tạm trong thư mục session được hướng dẫn.

## Cấu trúc repository

```text
my-agent-skills/
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── docs/
│   └── COMPATIBILITY.md
├── scripts/
│   └── validate_skills.py
└── skills/
    └── <skill-name>/
        ├── SKILL.md
        ├── scripts/           # Nếu skill có script
        ├── references/        # Nếu có tài liệu bổ sung
        └── agents/            # Metadata riêng cho agent, nếu có
```

## Phát triển và đóng góp

```bash
git clone https://github.com/phuongdev89/my-agent-skills.git
cd my-agent-skills
python scripts/validate_skills.py
```

Validator hiện kiểm tra sự tồn tại của `SKILL.md`, dấu phân cách frontmatter, trường `name`/`description`, tên trùng và tên khớp thư mục. Đây **không phải YAML parser đầy đủ**, chưa kiểm tra link, secret hay runtime dependency.

Để xem CLI nhận diện nội dung local mà không cài:

```bash
npx skills add . --list
```

Xem [CONTRIBUTING.md](CONTRIBUTING.md) khi thêm hoặc sửa skill. Khi thay đổi hành vi hoặc danh mục công khai, cập nhật [CHANGELOG.md](CHANGELOG.md).

## Khắc phục sự cố

| Vấn đề | Cách kiểm tra |
| --- | --- |
| Không hiện menu | Chạy trong terminal tương tác, không dùng `--all` hoặc chế độ bỏ qua xác nhận; có thể chỉ định `--skill` và `--agent` trực tiếp |
| CLI không tìm thấy skill | Chạy `--list`, kiểm tra URL/branch và frontmatter của `SKILL.md` |
| Agent chưa nhận skill | Kiểm tra agent đích và phạm vi project/global, rồi mở lại phiên |
| Lỗi symlink trên Windows | Thử cài với `--copy` |
| Script báo thiếu module/tool | Cài dependency theo hướng dẫn của skill trong môi trường phù hợp |
| API báo lỗi xác thực/quota | Kiểm tra cấu hình, quyền truy cập và quota provider; không đưa key vào issue |

## Changelog, phản hồi và quyền sử dụng

- [Lịch sử thay đổi](CHANGELOG.md)
- [Báo lỗi hoặc đề xuất](https://github.com/phuongdev89/my-agent-skills/issues)
- [Tài liệu Skills CLI](https://github.com/vercel-labs/skills#readme)

Repository hiện chưa có LICENSE ở root. Không mặc định toàn bộ nội dung được cấp phép MIT hoặc một giấy phép chung; cần xác minh nguồn gốc và điều khoản của từng thành phần trước khi tái phân phối.

