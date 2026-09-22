---
name: research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
---

Spin up a **background agent** to do the research, so you keep working while it reads.

## Quy định Session Directory (Bắt buộc)

Mọi hoạt động thu thập thông tin, tài liệu nguyên bản và kết quả nghiên cứu phải lưu trong session directory:
- **Thư mục gốc**: `./scratch/`
- **Cú pháp định danh**: `./scratch/yyyy-mm-dd_research_công-việc-viết-không-dấu`
  - *Ví dụ*: `./scratch/2026-09-22_research_flux-api-parameters`
- **Cấu trúc thư mục con bắt buộc**:
  - `raw/` (hoặc `input/`): Lưu tài liệu gốc, html/markdown tải về, API spec thô từ primary sources.
  - `output/`: File markdown tổng hợp kết quả nghiên cứu (ví dụ: `RESEARCH_FINDINGS.md`), tài liệu trích dẫn chuẩn hóa.
  - `scripts/`: Script cào dữ liệu tạm, script gọi API thử nghiệm phục vụ nghiên cứu.
  - `temp/`: Chứa dữ liệu parse nháp, response thô tạm thời.
- **Quy tắc cấm xả rác**: Tuyệt đối không ghi file markdown kết quả nghiên cứu, tệp dữ liệu cào hay log thô lung tung ra root repo (`cwd`). Luôn lưu báo cáo vào thư mục `output/` của session directory đã định.

Khởi tạo session trước khi chạy nghiên cứu:
```bash
SESSION_DIR="./scratch/2026-09-22_research_ten-de-tai"
mkdir -p "$SESSION_DIR/raw" "$SESSION_DIR/output" "$SESSION_DIR/scripts" "$SESSION_DIR/temp"
```

## Nhiệm vụ (Job Workflow)

1. Investigate the question against **primary sources** — official docs, source code, specs, first-party APIs — not a secondary write-up of them. Follow every claim back to the source that owns it. Lưu tài liệu thô tải về vào `$SESSION_DIR/raw/`.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save the final markdown report to `$SESSION_DIR/output/` (ví dụ: `$SESSION_DIR/output/RESEARCH_FINDINGS.md`) và thông báo đường dẫn rõ ràng cho người dùng. Không xả file ra thư mục root repo.
