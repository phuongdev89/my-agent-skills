# -*- coding: utf-8 -*-
"""
template_assembler.py
File điều phối chính (Master Assembler) để khởi tạo tài liệu, cấu hình giao diện chuẩn,
gọi tuần tự các Batch và lưu tệp DOCX hoàn chỉnh có gắn nhãn thời gian.

Cách dùng:
    python template_assembler.py [--output output_path]
"""

import os
import sys
import argparse
import datetime
from pathlib import Path
import docx

# Nạp module helpers từ thư mục cục bộ hoặc từ thư mục gốc của skill
try:
    import docx_helpers as h
except ImportError:
    _current_dir = Path(__file__).resolve().parent
    if (_current_dir / "docx_helpers.py").exists():
        sys.path.insert(0, str(_current_dir))
    for _parent in _current_dir.parents:
        _skill_scripts = _parent / "skills" / "pdf-image-to-docx" / "scripts"
        if _skill_scripts.exists():
            sys.path.insert(0, str(_skill_scripts))
            break
        _agent_skill_scripts = _parent / ".agents" / "skills" / "pdf-image-to-docx" / "scripts"
        if _agent_skill_scripts.exists():
            sys.path.insert(0, str(_agent_skill_scripts))
            break
    import docx_helpers as h

# Nạp các file batch đã phân chia (ví dụ: batch1, batch2, batch3)
# import batch1
# import batch2
# import batch3

def assemble_document(output_path=None):
    print("--- KHỞI TẠO TÀI LIỆU DOCX ---")
    doc = docx.Document()

    # 1. Cấu hình Envelope C5 tiêu chuẩn, lề Narrow và làm sạch Header/Footer
    h.setup_document_c5_narrow(doc, font_name="Arial", base_font_size=10)

    # 2. Tuần tự nạp từng Batch trang
    # print("Đang biên dịch Batch 1...")
    # batch1.add_batch_1(doc)
    # print("Đang biên dịch Batch 2...")
    # batch2.add_batch_2(doc)
    # print("Đang biên dịch Batch 3...")
    # batch3.add_batch_3(doc)

    # 3. Định danh và lưu file
    if not output_path:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path(__file__).resolve().parent.parent / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(out_dir / f"Document_Final_{timestamp}.docx")
    else:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    doc.save(output_path)
    print(f"\n✓ Xuất tệp thành công tại: {output_path}")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master Assembler for DOCX batches")
    parser.add_argument("--output", "-o", default=None, help="Đường dẫn file DOCX đầu ra")
    args = parser.parse_args()
    assemble_document(args.output)
