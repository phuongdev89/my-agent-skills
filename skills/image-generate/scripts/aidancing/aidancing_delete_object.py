#!/usr/bin/env python3
"""Xoá vật thể khỏi ảnh bằng AI (1 ảnh + prompt mô tả vật cần xoá)"""
import sys
import time
import argparse
from pathlib import Path
import requests

BASE_URL = "https://image.aidancing.net"
JOB_TYPE = "DELETE_OBJECT"

def delete_object(image_path: str, prompt: str, output_path: str = None, timeout: int = 180) -> str:
    img_file = Path(image_path)
    if not img_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {image_path}")

    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"{BASE_URL}/image-delete",
        "Origin": BASE_URL,
    })
    s.get(f"{BASE_URL}/image-delete", timeout=15)

    print(f"[*] Upload: {img_file.name}")
    mime = "image/png" if img_file.suffix.lower() == ".png" else "image/jpeg"
    with open(img_file, "rb") as f:
        files = {"image1": (img_file.name, f, mime)}
        data = {"type": JOB_TYPE, "prompt": prompt}
        res = s.post(f"{BASE_URL}/jobs", files=files, data=data, timeout=60)

    if res.status_code not in (200, 201):
        raise RuntimeError(f"Gửi job thất bại: {res.status_code} - {res.text}")

    print(f"[*] Đang xoá vật thể theo prompt: '{prompt}'...")
    start, last_status = time.time(), None
    while time.time() - start < timeout:
        time.sleep(3)
        r = s.get(f"{BASE_URL}/jobs?type={JOB_TYPE}", timeout=15)
        if r.status_code != 200: continue
        jobs = r.json()
        if not jobs: continue

        job = jobs[0]
        status = job.get("status")
        if status != last_status:
            print(f"    Trạng thái: {status} ({int(time.time() - start)}s)")
            last_status = status

        if status == "COMPLETED":
            url = job.get("outputUrl")
            if url.startswith("/"): url = BASE_URL + url
            if not output_path:
                output_path = str(img_file.parent / f"{img_file.stem}_deleted{img_file.suffix}")
            img_res = s.get(url, timeout=30)
            img_res.raise_for_status()
            with open(output_path, "wb") as out:
                out.write(img_res.content)
            print(f"[+] Thành công: {output_path}")
            return output_path
        elif status == "FAILED":
            raise RuntimeError(f"AI thất bại: {job.get('error')}")

    raise TimeoutError(f"Hết thời gian chờ ({timeout}s)")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Xoá vật thể khỏi ảnh bằng AI")
    p.add_argument("image", help="Đường dẫn file ảnh đầu vào")
    p.add_argument("prompt", help="Vật thể cần xoá (VD: 'xoá cái chai nước', 'xoá người đứng sau')")
    p.add_argument("-o", "--output", default=None, help="Đường dẫn file kết quả")
    args = p.parse_args()
    try:
        delete_object(args.image, args.prompt, args.output)
    except Exception as e:
        print(f"[-] Lỗi: {e}", file=sys.stderr)
        sys.exit(1)
