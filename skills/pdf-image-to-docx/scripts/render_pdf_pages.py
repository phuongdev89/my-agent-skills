# -*- coding: utf-8 -*-
"""
render_pdf_pages.py
Tự động xuất toàn bộ các trang của file PDF thành ảnh PNG độ phân giải cao (sử dụng PyMuPDF / fitz).
Cách dùng:
    python render_pdf_pages.py PATH_TO_PDF [output_dir] [dpi]
    hoặc:
    python render_pdf_pages.py --pdf PATH_TO_PDF --session-dir SESSION_DIR [--dpi 150]
Ví dụ:
    python render_pdf_pages.py "sach.pdf" "./pages_png" 150
"""

import os
import sys
import argparse
from pathlib import Path
import fitz  # PyMuPDF

def render_pdf(pdf_path, output_dir=None, dpi=150):
    if not os.path.isfile(pdf_path):
        print(f"Lỗi: Không tìm thấy tệp PDF tại: {pdf_path}")
        sys.exit(1)

    if output_dir is None:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_dir = os.path.join(os.path.dirname(pdf_path), f"{base_name}_pages")

    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"Đang mở tệp '{pdf_path}' ({total_pages} trang)...")

    for i in range(total_pages):
        page = doc[i]
        pix = page.get_pixmap(dpi=dpi)
        out_path = os.path.join(output_dir, f"page_{i+1}.png")
        pix.save(out_path)
        if (i + 1) % 5 == 0 or (i + 1) == total_pages:
            print(f"  ✓ Đã trích xuất trang {i+1}/{total_pages} -> page_{i+1}.png")

    print(f"\nHoàn tất! {total_pages} trang ảnh đã được lưu tại: '{output_dir}'.")
    return output_dir, total_pages

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render PDF pages to high-res PNG images")
    parser.add_argument("pdf_path", nargs="?", default=None, help="Đường dẫn tới tệp PDF nguồn")
    parser.add_argument("output_dir", nargs="?", default=None, help="Thư mục xuất ảnh PNG")
    parser.add_argument("dpi", nargs="?", type=int, default=None, help="Độ phân giải DPI (mặc định 150)")
    parser.add_argument("--pdf", dest="pdf_opt", help="Đường dẫn tệp PDF")
    parser.add_argument("--output-dir", "-o", dest="out_opt", help="Thư mục xuất ảnh PNG")
    parser.add_argument("--session-dir", dest="session_dir", help="Đường dẫn thư mục session (ảnh sẽ lưu vào <session_dir>/temp)")
    parser.add_argument("--dpi", "-d", dest="dpi_opt", type=int, default=150, help="Độ phân giải DPI (mặc định 150)")

    args = parser.parse_args()

    pdf_file = args.pdf_opt or args.pdf_path
    if not pdf_file:
        parser.print_help()
        sys.exit(1)

    if args.session_dir:
        out_directory = args.out_opt or os.path.join(args.session_dir, "temp")
    else:
        out_directory = args.out_opt or args.output_dir

    dpi_val = args.dpi_opt if args.dpi is None else args.dpi
    render_pdf(pdf_file, out_directory, dpi_val)
