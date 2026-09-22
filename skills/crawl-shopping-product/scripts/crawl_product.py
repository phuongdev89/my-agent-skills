import argparse
import json
import os
import requests
import sys
import asyncio
from pathlib import Path
from urllib.parse import urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from parsers.fallback_parser import parse_html_fallback

# Attempt to import crawl_core from parent directory or specific path
try:
    # Adjust this path based on where crawl_core.py actually is
    src_dir = scripts_dir.parent.parent.parent.parent / 'src'
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from crawl_core import crawl_product as crawl_product_llm
except ImportError:
    crawl_product_llm = None

def download_images(images, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    downloaded = []
    for i, img_url in enumerate(images):
        try:
            resp = requests.get(img_url, timeout=10)
            if resp.status_code == 200:
                ext = "jpg"
                filename = f"image_{i}.{ext}"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
                downloaded.append(filepath)
        except Exception as e:
            print(f"Error downloading {img_url}: {e}")
    return downloaded

import datetime

async def run_crawl(args):
    print(f"Crawling {args.url} using method: {args.method}")
    
    output_path = args.output
    images_dir = args.download_images
    
    if args.session_dir:
        session_dir = Path(args.session_dir).resolve()
        if not output_path:
            output_path = str(session_dir / "output" / "product_data.json")
        if not images_dir:
            images_dir = str(session_dir / "downloads")
    elif not output_path and not images_dir:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        session_dir = Path(f"./scratch/{today}_crawl-shopping-product_default").resolve()
        output_path = str(session_dir / "output" / "product_data.json")
        images_dir = str(session_dir / "downloads")
    
    if not output_path:
        output_path = "product_data.json"
        
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    if images_dir:
        Path(images_dir).mkdir(parents=True, exist_ok=True)
    
    product_data = {
        "title": "Sample Product",
        "images": [],
        "description": "Sample description",
        "price": {"current_price": 100000, "currency": "VND"},
        "platform": "unknown",
        "source_url": args.url
    }
    
    success_llm = False
    if args.method in ["llm", "auto"]:
        if crawl_product_llm:
            try:
                llm_data = await crawl_product_llm(args.url)
                if llm_data:
                    product_data.update(llm_data)
                    success_llm = True
            except Exception as e:
                print(f"LLM crawl failed: {e}")
        else:
            print("crawl_product_llm not found in crawl_core.")

    if not success_llm and args.method in ["fallback", "auto"]:
        try:
            html = requests.get(args.url).text
            parsed_data = parse_html_fallback(html, args.url)
            product_data.update(parsed_data)
        except Exception as e:
            print(f"Error in fallback parser: {e}")

    if images_dir and product_data.get("images"):
        download_images(product_data["images"], images_dir)
        
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(product_data, f, ensure_ascii=False, indent=2)
        
    print(f"Data saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Crawl shopping product")
    parser.add_argument("--url", required=True, help="Product URL")
    parser.add_argument("--output", default=None, help="Output JSON file")
    parser.add_argument("--download-images", help="Directory to save downloaded images", type=str)
    parser.add_argument("--method", choices=["llm", "fallback", "auto"], default="auto", help="Crawling method")
    parser.add_argument("--session-dir", type=Path, help="Directory to save session data")
    
    args = parser.parse_args()
    asyncio.run(run_crawl(args))

if __name__ == "__main__":
    main()
