#!/usr/bin/env python3
"""Đổi trang phục bằng AI (2 ảnh: ảnh người mẫu + ảnh trang phục)"""
import sys
import time
import argparse
from pathlib import Path
import requests

BASE_URL = "https://image.aidancing.net"
JOB_TYPE = "OUTFIT_SWAP"

def outfit_swap(person_img: str, outfit_img: str, prompt: str = "", output_path: str = None, timeout: int = 180) -> str:
    p_file = Path(person_img)
    o_file = Path(outfit_img)
    for f in (p_file, o_file):
        if not f.exists():
            raise FileNotFoundError(f"Không tìm thấy: {f}")

    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"{BASE_URL}/outfit-swap",
        "Origin": BASE_URL,
    })
    s.get(f"{BASE_URL}/outfit-swap", timeout=15)

    print(f"[*] Upload: Người={p_file.name}, Trang phục={o_file.name}")
    with open(p_file, "rb") as f1, open(o_file, "rb") as f2:
        files = {
            "image1": (p_file.name, f1, "image/png" if p_file.suffix.lower() == ".png" else "image/jpeg"),
            "image2": (o_file.name, f2, "image/png" if o_file.suffix.lower() == ".png" else "image/jpeg"),
        }
        data = {"type": JOB_TYPE, "prompt": prompt or "Đổi trang phục"}
        res = s.post(f"{BASE_URL}/jobs", files=files, data=data, timeout=60)

    if res.status_code not in (200, 201):
        raise RuntimeError(f"Gửi job thất bại: {res.status_code} - {res.text}")

    print("[*] Đang chờ AI xử lý...")
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
                output_path = str(p_file.parent / f"{p_file.stem}_outfit{p_file.suffix}")
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
    p = argparse.ArgumentParser(description="Đổi trang phục AI (2 ảnh)")
    p.add_argument("person", help="Ảnh người mẫu")
    p.add_argument("outfit", help="Ảnh trang phục mẫu")
    p.add_argument("-p", "--prompt", default="", help="Mô tả bổ sung (tuỳ chọn)")
    p.add_argument("-o", "--output", default=None, help="Đường dẫn file kết quả")
    args = p.parse_args()
    try:
        outfit_swap(args.person, args.outfit, args.prompt, args.output)
    except Exception as e:
        print(f"[-] Lỗi: {e}", file=sys.stderr)
        sys.exit(1)
