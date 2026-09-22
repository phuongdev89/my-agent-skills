# crawl-shopping-product Skill

Skill cào dữ liệu có cấu trúc từ đường dẫn sản phẩm trên các sàn thương mại điện tử lớn (**Shopee**, **TikTok Shop**, **Lazada**), tự động phân giải link rút gọn di động (`vn.shp.ee`, `vt.tiktok.com`).

Skill này kết hợp sức mạnh của thư viện **`crawl4ai`** (Playwright stealth, chống chặn bot, tự cuộn lazy-load) cùng chiến lược trích xuất **`LLMExtractionStrategy`** qua OpenAI-compatible endpoint cấu hình trong `.env`, đồng thời trang bị tầng dự phòng **Fallback Parser** (JSON-LD + OpenGraph) nhanh và ổn định.

---

## 1. Cấu trúc Thư mục

```text
crawl-shopping-product/
├── README.md                      # Hướng dẫn chi tiết cho Developer và KOC Agent
├── SKILL.md                       # Định nghĩa skill chuẩn hệ thống Antigravity
├── schemas/
│   └── product.py                 # Pydantic Schemas (ShoppingProduct, ProductPrice, ImageItem)
└── scripts/
    ├── crawl_core.py              # Core engine crawl4ai + LLMExtractionStrategy + Redirect Resolver
    ├── crawl_product.py           # CLI điều phối chính + Tự động tải ảnh về thư mục
    └── parsers/
        └── fallback_parser.py     # Parser dự phòng trích xuất JSON-LD Schema & OpenGraph tags
```

---

## 2. Các Trường Dữ Liệu Bóc Tách

| Trường | Kiểu | Mô tả |
|---|---|---|
| `title` | `str` | Tiêu đề sản phẩm chuẩn hóa |
| `images` | `List[str]` | Danh sách URL ảnh sản phẩm sắc nét (ảnh bìa, ảnh chi tiết) |
| `description` | `str` | Mô tả sản phẩm, chất liệu vải, kiểu dáng, xuất xứ |
| `price` | `object` | `current_price` (giá bán hiện tại), `original_price`, `currency` (mặc định VND) |
| `platform` | `str` | Nền tảng sàn TMĐT (`shopee`, `tiktok`, `lazada`, `unknown`) |
| `source_url` | `str` | URL gốc của sản phẩm |

> [!IMPORTANT]
> **Kỷ luật KOC (Antigravity Rules)**: Trường `price` (giá sản phẩm) và mã SKU chỉ dùng để lưu hồ sơ kỹ thuật (`product_data.json`) hỗ trợ phân khúc đối tượng người xem. **TUYỆT ĐỐI KHÔNG** đưa giá tiền hay mã SKU vào lời thoại hoặc kịch bản video KOC.

---

## 3. Cấu hình Môi trường (.env)

Skill tự động nhận diện cấu hình OpenAI-compatible từ `.env` hệ thống:

```env
# ==============================================================================
# SHOPPING PRODUCT CRAWLER (crawl-shopping-product)
# ==============================================================================
# Endpoint OpenAI-compatible (mặc định: https://api.openai.com/v1)
SHOPPING_CRAWLER_ENDPOINT_URL=https://api.openai.com/v1
SHOPPING_CRAWLER_API_KEY=<YOUR_API_KEY>
SHOPPING_CRAWLER_MODEL=gpt-4o
SHOPPING_CRAWLER_HEADLESS=true
```

---

## 4. Hướng dẫn Sử dụng (CLI)

### A. Chế độ Tự động (Khuyến nghị)
Tự động thử trích xuất bằng LLM qua `crawl4ai`. Nếu mạng lỗi hoặc trang chặn, tự động chuyển sang Fallback parser:
```bash
python .agents/skills/crawl-shopping-product/scripts/crawl_product.py \
  --url "https://shopee.vn/product/12345/67890" \
  --output "product_data.json" \
  --download-images "./03_visuals"
```

### B. Chế độ Fallback nhanh (Không tốn Token LLM)
Trích xuất trực tiếp bằng HTTP request và BeautifulSoup (OpenGraph + JSON-LD):
```bash
python .agents/skills/crawl-shopping-product/scripts/crawl_product.py \
  --url "https://vn.shp.ee/xyz123" \
  --method fallback \
  --output "product_data.json"
```

### C. Chế độ Thuần LLM
```bash
python .agents/skills/crawl-shopping-product/scripts/crawl_product.py \
  --url "https://vt.tiktok.com/ZSabc123/" \
  --method llm \
  --output "product_data.json"
```

---

## 5. Dữ liệu Đầu ra Mẫu (`product_data.json`)

```json
{
  "title": "Đầm Dạ Hội Voan Tơ Bồng Bềnh Cúp Ngực Sang Trọng",
  "images": [
    "https://down-vn.img.susercontent.com/file/vn-11134207-7ras8-m8xyz.jpg",
    "https://down-vn.img.susercontent.com/file/vn-11134207-7ras8-m8abc.jpg"
  ],
  "description": "Chất liệu voan tơ cao cấp bồng bềnh, phom xòe tiểu thư, lót lụa mềm mại tôn dáng...",
  "price": {
    "current_price": 389000.0,
    "original_price": 550000.0,
    "currency": "VND"
  },
  "platform": "shopee",
  "source_url": "https://shopee.vn/..."
}
```
Dữ liệu này tương thích trực tiếp với `ProductDossier` trong quy trình sản xuất video KOC.
