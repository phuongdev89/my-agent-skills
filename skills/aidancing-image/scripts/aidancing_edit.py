#!/usr/bin/env python3
"""
Tool chỉnh sửa ảnh tự động qua API image.aidancing.net
Không cần trình duyệt, không cần đăng nhập.
"""
import sys
import time
import argparse
from pathlib import Path
import requests

BASE_URL = "https://image.aidancing.net"

def edit_image(image_path: str, prompt: str, output_path: str = None, timeout: int = 180) -> str:
    img_file = Path(image_path)
    if not img_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {image_path}")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"{BASE_URL}/edit-image",
        "Origin": BASE_URL,
    })

    # Lấy cookie session
    session.get(f"{BASE_URL}/edit-image", timeout=15)

    # Gửi job tạo ảnh
    print(f"[*] Đang tải ảnh lên: {img_file.name}")
    mime = "image/png" if img_file.suffix.lower() == ".png" else "image/jpeg"
    with open(img_file, "rb") as f:
        files = {"image1": (img_file.name, f, mime)}
        data = {"type": "EDIT_IMAGE", "prompt": prompt}
        res = session.post(f"{BASE_URL}/jobs", files=files, data=data, timeout=60)

    if res.status_code not in (200, 201):
        raise RuntimeError(f"Gửi job thất bại: {res.status_code} - {res.text}")

    print(f"[*] Đã gửi job. Prompt: '{prompt}'")
    print("[*] Đang chờ AI xử lý...")

    # Polling kết quả
    start = time.time()
    last_status = None
    while time.time() - start < timeout:
        time.sleep(3)
        r = session.get(f"{BASE_URL}/jobs?type=EDIT_IMAGE", timeout=15)
        if r.status_code != 200:
            continue
        jobs = r.json()
        if not jobs:
            continue

        job = jobs[0]
        status = job.get("status")
        if status != last_status:
            print(f"    Trạng thái: {status} ({int(time.time() - start)}s)")
            last_status = status

        if status == "COMPLETED":
            output_url = job.get("outputUrl")
            if not output_url:
                raise RuntimeError("Job hoàn thành nhưng không có outputUrl")
            if output_url.startswith("/"):
                output_url = BASE_URL + output_url

            # Xác định đường dẫn file lưu
            if not output_path:
                output_path = str(img_file.parent / f"{img_file.stem}_edited{img_file.suffix}")

            print(f"[*] Đang tải ảnh kết quả từ: {output_url}")
            img_res = session.get(output_url, timeout=30)
            img_res.raise_for_status()
            with open(output_path, "wb") as out:
                out.write(img_res.content)

            print(f"[+] Thành công! Đã lưu tại: {output_path}")
            return output_path

        elif status == "FAILED":
            raise RuntimeError(f"AI xử lý thất bại: {job.get('error', 'Unknown error')}")

    raise TimeoutError(f"Hết thời gian chờ ({timeout}s)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Dancing Image Editor CLI")
    parser.add_argument("image", help="Đường dẫn file ảnh đầu vào")
    parser.add_argument("prompt", help="Prompt mô tả nội dung cần sửa")
    parser.add_argument("-o", "--output", help="Đường dẫn file ảnh đầu ra (mặc định: cùng thư mục)", default=None)
    args = parser.parse_args()

    try:
        edit_image(args.image, args.prompt, args.output)
    except Exception as e:
        print(f"[-] Lỗi: {e}", file=sys.stderr)
        sys.exit(1)
