import os
import re
import json
import asyncio
import httpx
from typing import List, Dict, Optional, Any
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field

class ProductSchema(BaseModel):
    title: str = Field(description="Product title")
    images: List[str] = Field(description="List of product image URLs")
    description: str = Field(description="Product description")
    price_original: Optional[float] = Field(description="Original price of the product")
    price_current: Optional[float] = Field(description="Current or discounted price")
    currency: str = Field(description="Currency code like USD, VND")

async def resolve_redirect(url: str) -> str:
    """Resolve redirect links like vn.shp.ee or vt.tiktok.com."""
    if 'vn.shp.ee' in url or 'vt.tiktok.com' in url:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                response = await client.get(url)
                return str(response.url)
        except Exception:
            return url
    return url

async def crawl_product(url: str) -> Optional[Dict[str, Any]]:
    resolved_url = await resolve_redirect(url)
    
    # Custom LLM Endpoint config
    endpoint_url = os.getenv("AI_AGENT_3_ENDPOINT_URL") or os.getenv("AI_AGENT_1_ENDPOINT_URL", "https://omniroute.phuonganh.io.vn/v1")
    if endpoint_url.endswith("/chat/completions"):
        endpoint_url = endpoint_url.replace("/chat/completions", "")
    
    api_key = os.getenv("AI_AGENT_3_API_KEY") or os.getenv("AI_AGENT_1_API_KEY", "sk-03d858f56405a925-8502d0-9876f288")
    model_name = "gemini-3.8-flash"
    
    strategy = LLMExtractionStrategy(
        provider=f"openai/{model_name}", # Compatible
        api_token=api_key,
        base_url=endpoint_url,
        schema=ProductSchema.model_json_schema() if hasattr(ProductSchema, "model_json_schema") else ProductSchema.schema(),
        extraction_type="schema",
        instruction="Extract product details including title, images, description, original price, current price, and currency."
    )

    try:
        async with AsyncWebCrawler(
            headless=True,
            # stealth and bypass_bot_detection are conceptually covered by kwargs in newer crawl4ai versions,
            # using basic params as requested
            kwargs={"stealth": True, "bypass_bot_detection": True}
        ) as crawler:
            result = await crawler.arun(
                url=resolved_url,
                word_count_threshold=10,
                extraction_strategy=strategy,
                cache_mode="bypass",
                # Auto scroll to load lazy content
                js_code="window.scrollTo(0, document.body.scrollHeight);",
                wait_for=2 # wait after scrolling
            )
            if result and result.extracted_content:
                return json.loads(result.extracted_content)
            return None
    except Exception as e:
        print(f"Error crawling product: {e}")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        res = asyncio.run(crawl_product(sys.argv[1]))
        print(json.dumps(res, indent=2, ensure_ascii=False))
