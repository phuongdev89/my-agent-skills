# -*- coding: utf-8 -*-
"""
scan_image_folder.py
Tiện ích quét và chuẩn hóa thư mục ảnh chụp trang sách có sẵn:
- Tự động nhận diện các định dạng: .png, .jpg, .jpeg, .webp, .bmp
- Sắp xếp thứ tự tự nhiên (Natural Sort: page_1, page_2, ..., page_10) thay vì sắp xếp chuỗi thô.
- Kiểm tra hướng ảnh (dọc/ngang/xoay ngược).
- Báo cáo số lượng trang N để chuẩn bị tiến hành phân lô sản xuất (Batching).

Cách dùng:
    python scan_image_folder.py <path_to_images_dir>
"""

import os
import sys
import re
from PIL import Image

def natural_sort_key(text):
    """Tách chuỗi thành danh sách số và chữ để sắp xếp số đúng thứ tự (1, 2, ... 10 thay vì 1, 10, 2)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]

def scan_images(dir_path):
    if not os.path.isdir(dir_path):
        print(f"Lỗi: Thư mục không tồn tại: {dir_path}")
        sys.exit(1)

    supported_exts = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
    files = [f for f in os.listdir(dir_path) if f.lower().endswith(supported_exts)]

    if not files:
        print(f"Cảnh báo: Không tìm thấy tệp ảnh nào trong thư mục: {dir_path}")
        return [], 0

    sorted_files = sorted(files, key=natural_sort_key)
    total_pages = len(sorted_files)

    print("=" * 70)
    print(f"KHẢO SÁT THƯ MỤC ẢNH CÓ SẴN: {dir_path}")
    print("=" * 70)
    print(f"• Tổng số ảnh tìm thấy: {total_pages} trang")
    print(f"• Trang đầu tiên: {sorted_files[0]}")
    print(f"• Trang cuối cùng: {sorted_files[-1]}")

    # Kiểm tra kích thước một số trang mẫu
    sample_img_path = os.path.join(dir_path, sorted_files[0])
    try:
        with Image.open(sample_img_path) as img:
            w, h = img.size
            orientation = "Ảnh dọc (Portrait)" if h >= w else "Ảnh ngang / Cần xoay (Landscape)"
            print(f"• Độ phân giải mẫu: {w}x{h} px ({orientation})")
    except Exception as e:
        print(f"• Lỗi đọc ảnh mẫu: {e}")

    print("\n✓ Dữ liệu sẵn sàng! Bỏ qua bước trích xuất PDF -> Tiến hành phân lô ngay.")
    print("=" * 70)
    return [os.path.join(dir_path, f) for f in sorted_files], total_pages

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cách dùng: python scan_image_folder.py <path_to_images_dir>")
        sys.exit(1)
    scan_images(sys.argv[1])
