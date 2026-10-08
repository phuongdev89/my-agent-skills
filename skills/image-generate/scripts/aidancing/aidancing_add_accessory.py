#!/usr/bin/env python3
"""Thêm phụ kiện cho nhân vật bằng AI (2 ảnh: ảnh nhân vật + ảnh phụ kiện)"""
import sys
import time
import argparse
from pathlib import Path
import requests

BASE_URL = "https://image.aidancing.net"
JOB_TYPE = "ADD_ACCESSORY"

def add_accessory(person_img: str, accessory_img: str, prompt: str = "", output_path: str = None, timeout: int = 180) -> str:
    p_file = Path(person_img)
    a_file = Path(accessory_img)
    for f in (p_file, a_file):
        if not f.exists():
            raise FileNotFoundError(f"Không tìm thấy: {f}")

    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"{BASE_URL}/image-add-outfit",
        "Origin": BASE_URL,
    })
    s.get(f"{BASE_URL}/image-add-outfit", timeout=15)

    print(f"[*] Upload: Nhân vật={p_file.name}, Phụ kiện={a_file.name}")
    with open(p_file, "rb") as f1, open(a_file, "rb") as f2:
        files = {
            "image1": (p_file.name, f1, "image/png" if p_file.suffix.lower() == ".png" else "image/jpeg"),
            "image2": (a_file.name, f2, "image/png" if a_file.suffix.lower() == ".png" else "image/jpeg"),
        }
        data = {"type": JOB_TYPE, "prompt": prompt or "Thêm phụ kiện"}
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
                output_path = str(p_file.parent / f"{p_file.stem}_acc{p_file.suffix}")
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
    p = argparse.ArgumentParser(description="Thêm phụ kiện cho nhân vật bằng AI (2 ảnh)")
    p.add_argument("person", help="Ảnh nhân vật")
    p.add_argument("accessory", help="Ảnh phụ kiện (kính, mũ, túi, đồng hồ...)")
    p.add_argument("-p", "--prompt", default="", help="Mô tả vị trí/cách đeo (tuỳ chọn)")
    p.add_argument("-o", "--output", default=None, help="Đường dẫn file kết quả")
    args = p.parse_args()
    try:
        add_accessory(args.person, args.accessory, args.prompt, args.output)
    except Exception as e:
        print(f"[-] Lỗi: {e}", file=sys.stderr)
        sys.exit(1)
