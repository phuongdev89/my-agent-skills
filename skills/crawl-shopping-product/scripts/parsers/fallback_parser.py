import json
import re
from bs4 import BeautifulSoup
from typing import Dict, Any

def parse_html_fallback(html: str, url: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, 'html.parser')
    result = {
        "title": "",
        "images": [],
        "description": "",
        "price": {
            "current_price": 0.0,
            "currency": "VND"
        },
        "platform": "unknown",
        "source_url": url
    }
    
    # Try JSON-LD
    json_ld_tags = soup.find_all('script', type='application/ld+json')
    for tag in json_ld_tags:
        try:
            data = json.loads(tag.string)
            if isinstance(data, dict):
                if data.get('@type') == 'Product':
                    result['title'] = data.get('name', result['title'])
                    result['description'] = data.get('description', result['description'])
                    
                    offers = data.get('offers', {})
                    if isinstance(offers, dict):
                        result['price']['current_price'] = float(offers.get('price', 0))
                        result['price']['currency'] = offers.get('priceCurrency', 'VND')
                    
                    img = data.get('image')
                    if img:
                        if isinstance(img, list):
                            result['images'].extend(img)
                        elif isinstance(img, str):
                            result['images'].append(img)
        except Exception:
            pass

    # OpenGraph meta tags
    if not result['title']:
        og_title = soup.find('meta', property='og:title')
        if og_title: result['title'] = og_title['content']
        
    if not result['description']:
        og_desc = soup.find('meta', property='og:description')
        if og_desc: result['description'] = og_desc['content']

    og_image = soup.find('meta', property='og:image')
    if og_image and og_image['content'] not in result['images']:
        result['images'].append(og_image['content'])
        
    return result
