# 🗺️ KẾ HOẠCH TRAINING DATA DU LỊCH - 3 THÀNH PHỐ MIỀN TRUNG

> **Phạm vi:** Đà Nẵng – Hội An – Huế
> **Mục tiêu:** Mở rộng dataset từ 1 thành phố hiện tại (Đà Nẵng) lên 3 thành phố, đảm bảo chất lượng & đa dạng.

---

## 1. Phân tích hiện trạng

### 1.1 Dataset hiện tại (`data/places.csv`)

| Thành phố | Số địa điểm | Category chính | Toạ độ | Mô tả |
|-----------|-------------|----------------|--------|--------|
| **Đà Nẵng** | 905 (99.4%) | sightseeing (92%) | ~250 có | ~350 có |
| **Hội An** | 0 | – | – | – |
| **Huế** | 0 | – | – | – |
| Lỗi encoding | 5 | – | – | – |

### 1.2 Hạn chế quan trọng

1. **City field = "Da Nang"** toàn bộ → cần sửa schema/logic để phân biệt
2. **CITY_PATTERNS** trong `src/query_extractor.py:50` chỉ có `da nang` → cần thêm `hoi an`, `hue`
3. **CITY_MAP** trong `src/recommender.py:140` chỉ map variants của "da nang"
4. **`placesdetail.csv` rỗng** → không trả lời được câu hỏi lịch sử/đặc điểm
5. **Category mất cân đối** – 92% sightseeing, thiếu food/hotel/event

---

## 2. Yêu cầu chất lượng dataset mới

### 2.1 Tiêu chí một địa điểm "đạt chuẩn"

| Trường | Bắt buộc | Khuyến nghị |
|--------|----------|-------------|
| `id` | ✅ | UUID hoặc auto-increment |
| `name` | ✅ Tên tiếng Việt | Tên tiếng Anh (nếu có) |
| `city` | ✅ Chuẩn hoá: `Da Nang` / `Hoi An` / `Hue` | – |
| `category` | ✅ 1 trong: sightseeing/food/hotel/event | Subcategory |
| `description` | ✅ ≥ 30 ký tự | 100-300 ký tự, có thông tin hữu ích |
| `address` | ✅ | Số nhà, đường, phường/quận |
| `lat`, `lon` | ✅ ≠ 0 | Từ Google Maps/OSM |
| `rating` | ✅ 0.0 - 5.0 | Từ Google/TripAdvisor |
| `review_count` | ✅ | Số review thực |
| `avg_cost` | ✅ | Theo giá hiện tại (VND) |
| `duration_min` | ✅ | Phút |
| `open_time` / `close_time` | – | Nếu có |
| `tags` | ✅ | Phân cách `;` |
| `image_url` | – | Từ nguồn chính thức |

### 2.2 Mục tiêu số lượng

| Thành phố | Sightseeing | Food | Hotel | Event | **Tổng** |
|-----------|-------------|------|-------|-------|----------|
| **Đà Nẵng** (chuẩn hoá) | 200 | 80 | 50 | 30 | **360** |
| **Hội An** | 120 | 60 | 40 | 20 | **240** |
| **Huế** | 150 | 70 | 50 | 25 | **295** |
| **TỔNG** | 470 | 210 | 140 | 75 | **~895** |

→ Tổng cộng **~900 địa điểm chất lượng cao** cho 3 thành phố (tương đương dataset hiện tại nhưng chất lượng hơn nhiều).

---

## 3. CÁC PHƯƠNG ÁN TRAINING DATA

### 📊 So sánh tổng quan

| Phương án | Chi phí | Thời gian | Chất lượng | Độ bao phủ | Phù hợp khi |
|-----------|---------|-----------|------------|------------|-------------|
| **PA1. Crawl tự động** | Thấp | 1-2 tuần | Trung bình | Rộng | Cần data nhanh, chấp nhận cleanup |
| **PA2. Crawl + LLM Enrich** | Trung bình | 2-3 tuần | Cao | Rộng | Cần chất lượng cao, có OpenAI key |
| **PA3. Nhập tay + API** | Cao (nhân lực) | 3-4 tuần | Rất cao | Vừa | Cần data "premium" cho từng địa danh |
| **PA4. Hybrid (Khuyến nghị)** | Trung bình | 2-3 tuần | Cao | Rất rộng | Cân bằng tốc độ & chất lượng |
| **PA5. Mua data từ vendor** | Cao ($) | 3-7 ngày | Tuỳ vendor | Tuỳ vendor | Có ngân sách, cần gấp |

---

### 🔹 PHƯƠNG ÁN 1: Crawl tự động hoàn toàn (Budget thấp, nhanh)

**Mô tả:** Tái sử dụng hệ thống scraper hiện tại + mở rộng thêm nguồn cho Hội An & Huế.

**Các bước thực hiện:**

1. **Bổ sung nguồn crawl** trong `scraper/config.yaml`:
   - `https://hoiantourism.gov.vn/` (Hội An)
   - `https://huecitytour.vn/` (Huế)
   - `https://thuathienhue.gov.vn/` (Huế - Sở Du lịch)
   - Wikipedia: `/wiki/Hội_An`, `/wiki/Huế`
   - TripAdvisor API (nếu có key)

2. **Viết parser mới**:
   - `scraper/parsers/hoi_an_tourism.py`
   - `scraper/parsers/hue_tourism.py`
   - `scraper/parsers/wikipedia_hoi_an.py`
   - `scraper/parsers/wikipedia_hue.py`

3. **Cập nhật logic city**:
   - Tự động detect city từ URL/địa chỉ
   - Normalize về `Da Nang` / `Hoi An` / `Hue`

4. **Chạy pipeline**:
   ```bash
   python scraper/runner.py --cities "da nang,hoi an,hue"
   python scraper/normalizer.py
   python scraper/dedupe.py
   ```

5. **Rebuild embeddings**:
   ```bash
   python src/build_index.py
   python -c "from src.recommender import Recommender; r = Recommender(); r.compute_embeddings()"
   ```

**Ưu điểm:**
- ✅ Chi phí thấp (chỉ tốn bandwidth)
- ✅ Tận dụng code hiện có
- ✅ Nhanh, dễ chạy lại khi cần update

**Nhược điểm:**
- ❌ Dữ liệu thô, cần clean nhiều
- ❌ Mô tả ngắn, thiếu chi tiết lịch sử
- ❌ Toạ độ có thể thiếu (~30-40%)
- ❌ Rating/review có thể không có

**Ước tính:**
- ⏱️ Thời gian: 5-10 ngày (code + test + cleanup)
- 💰 Chi phí: ~0 (chỉ tốn điện/internet)
- 👥 Nhân lực: 1 dev

---

### 🔹 PHƯƠNG ÁN 2: Crawl + LLM Enrichment (Khuyến nghị cho chất lượng cao)

**Mô tả:** Crawl tự động ở PA1, sau đó dùng **LLM (GPT-4o-mini)** để enrich dữ liệu (generate description, infer category, fill missing fields).

**Pipeline chi tiết:**

```
[Crawl] → [Normalize] → [Dedupe] → [LLM Enrich] → [Human Spot-check] → [Final CSV]
                                                      ↓
                                            [Compute Embeddings]
```

**Bước 1: Crawl** (giống PA1)
- Crawl ~1500-2000 raw rows
- Quality: 60% tốt, 40% cần fix

**Bước 2: LLM Enrichment** (script mới: `scraper/llm_enrich.py`)

```python
# Pseudo-code
for each row in raw_data:
    if row['description'] is empty OR len < 50:
        prompt = f"""
        Bạn là chuyên gia du lịch. Viết mô tả 100-200 ký tự về:
        Tên: {row['name']}
        Thành phố: {row['city']}
        Tags: {row['tags']}
        
        Bao gồm: điểm nổi bật, hoạt động chính, đối tượng phù hợp.
        Trả về JSON: {{"description": "...", "highlights": "..."}}
        """
        enriched = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        row['description'] = enriched['description']
        row['highlights'] = enriched['highlights']
    
    if row['lat'] == 0 OR row['lon'] == 0:
        # Dùng Google Geocoding API
        coords = geocode(f"{row['name']}, {row['city']}, Vietnam")
        row['lat'], row['lon'] = coords
```

**Bước 3: Smart category inference**
- Dùng LLM phân loại lại category chính xác hơn
- Sub-category: `beach` / `temple` / `museum` / `street_food` / `seafood` / ...

**Bước 4: Spot-check**
- Lấy mẫu 50-100 rows kiểm tra tay
- Fix các lỗi LLM hallucination

**Ưu điểm:**
- ✅ Mô tả phong phú, tự nhiên
- ✅ Category chính xác hơn
- ✅ Có thể generate thêm `highlights`, `tips`, `nearby_attractions`
- ✅ Vẫn giữ được tốc độ của crawl tự động

**Nhược điểm:**
- ❌ Tốn chi phí OpenAI (~$10-30 cho 1000 rows với gpt-4o-mini)
- ❌ LLM có thể hallucinate → cần verify
- ❌ Phụ thuộc API OpenAI

**Ước tính:**
- ⏱️ Thời gian: 10-15 ngày
- 💰 Chi phí: ~$30-50 OpenAI + $10 Google Geocoding
- 👥 Nhân lực: 1-2 người

---

### 🔹 PHƯƠNG ÁN 3: Nhập tay chất lượng cao (Premium)

**Mô tả:** Tuyển CTV/tình nguyện viên hoặc tự nhập tay ~300-500 địa điểm "top" cho mỗi thành phố, với thông tin đầy đủ & chính xác.

**Cấu trúc data mỗi thành phố:**

```
Đà Nẵng (300 địa điểm TOP):
├── Sightseeing (150)
│   ├── Bà Nà Hills, Cầu Vàng, Cầu Rồng, Ngũ Hành Sơn...
│   ├── Bãi biển Mỹ Khê, Non Nước, Bắc Mỹ An
│   └── Sơn Trà, Hải Vân Quan, Linh Ứng...
├── Food (60)
│   ├── Bún chả cá, Mì Quảng, Bánh tráng cuốn thịt heo
│   ├── Hải sản: Bé Mặn, Mộc, Hồng Phát
│   └── Cafe rooftop, view sông Hàn
├── Hotel (50)
│   ├── 5*: InterContinental, Hyatt, Vinpearl
│   ├── 4*: Novotel, Hilton, Belle Maison
│   └── Resort: Fusion Maia, Naman Retreat
└── Event (40)
    ├── Lễ hội Pháo hoa Quốc tế
    ├── Festival Biển
    └── Chợ đêm Helio, Sơn Trà

Hội An (240 địa điểm TOP):
├── Phố cổ Hội An (UNESCO)
├── Các hội quán, chùa, miếu
├── Làng nghề: gốm Thanh Hà, mộc Kim Bồng
├── Biển An Bàng, Cửa Đại
└── Food: Cao lầu, Mì Quảng Hội An, Bánh mì Phượng

Huế (300 địa điểm TOP):
├── Đại Nội (Kinh thành Huế)
├── Lăng tẩm: Tự Đức, Minh Mạng, Khải Định
├── Chùa: Thiên Mụ, Từ Đàm
├── Sông Hương, Núi Ngự
└── Food: Bún bò Huế, Cơm hến, Bánh bèo
```

**Quy trình:**
1. Lên danh sách TOP địa điểm (Google Maps rating ≥ 4.0, hoặc guidebooks)
2. Chia cho 2-3 CTV (mỗi người 1 thành phố)
3. CTV crawl thông tin từ:
   - Google Maps (rating, reviews, address, lat/lon)
   - TripAdvisor
   - Website chính thức
   - Wikipedia
4. Nhập vào Google Sheet chung
5. Review chéo giữa các CTV
6. Convert sang CSV

**Template Google Sheet:**
| name | city | category | description | address | lat | lon | rating | review_count | avg_cost | duration_min | open_time | close_time | tags | best_time | image_url | source |

**Ưu điểm:**
- ✅ Chất lượng rất cao, chính xác
- ✅ Có review & rating thật
- ✅ Mô tả phong phú, đa dạng giọng văn
- ✅ Toạ độ chính xác

**Nhược điểm:**
- ❌ Tốn thời gian & nhân lực
- ❌ Khó scale lên nhiều thành phố
- ❌ Phụ thuộc vào chất lượng CTV

**Ước tính:**
- ⏱️ Thời gian: 20-30 ngày
- 💰 Chi phí: ~5-10 triệu VND (thù lao CTV)
- 👥 Nhân lực: 1 PM + 3 CTV

---

### 🔹 PHƯƠNG ÁN 4: HYBRID (Khuyến nghị ⭐)

**Mô tả:** Kết hợp PA1 (crawl) + PA2 (LLM enrich) + PA3 (top địa điểm nhập tay).

**Pipeline:**

```
┌─────────────────────────────────────────────────────┐
│  GIAI ĐOẠN 1: Crawl tự động (PA1)                  │
│  - Crawl 1500-2000 raw rows từ 8-10 nguồn           │
│  - Tự động detect city, normalize schema            │
│  - Output: raw_data.csv (khoảng 1500 rows)           │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  GIAI ĐOẠN 2: LLM Enrichment (PA2)                 │
│  - Generate description cho rows thiếu               │
│  - Infer category chính xác                          │
│  - Generate highlights, tips                         │
│  - Output: enriched_data.csv                         │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  GIAI ĐOẠN 3: Top Places Manual (PA3)               │
│  - Chọn TOP 100 địa điểm mỗi thành phố             │
│  - Verify & enrich từ Google Maps, TripAdvisor       │
│  - Đảm bảo 100% có lat/lon, rating, description    │
│  - Output: top_places.csv (300 rows chất lượng cao)  │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  GIAI ĐOẠN 4: Merge & Deduplicate                   │
│  - Merge enriched + top_places                       │
│  - Dedupe theo (name, city)                          │
│  - Validate schema                                   │
│  - Output: places.csv FINAL (900+ rows)              │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  GIAI ĐOẠN 5: Embeddings & Index                    │
│  - Rebuild TF-IDF                                    │
│  - Recompute embeddings (multilingual-e5-base)      │
│  - Save models/nn_embeds.npy                         │
│  - Test recommender với 3 thành phố                  │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  GIAI ĐOẠN 6: Update Code                            │
│  - Thêm CITY_PATTERNS cho hoi an, hue                │
│  - Update CITY_MAP                                   │
│  - Test query routing                                │
│  - Test multi-city itinerary (ĐN → HA → Huế)         │
└─────────────────────────────────────────────────────┘
```

**Ước tính chi tiết cho PA4:**

| Giai đoạn | Thời gian | Nhân lực | Chi phí |
|-----------|-----------|----------|---------|
| 1. Crawl | 5 ngày | 1 dev | $0 |
| 2. LLM Enrich | 3 ngày | 1 dev | $30 |
| 3. Top places manual | 7 ngày | 1 PM + 2 CTV | $50 (CTV) |
| 4. Merge & validate | 2 ngày | 1 dev | $0 |
| 5. Embeddings | 2 ngày | 1 dev | $5 (compute) |
| 6. Code update | 3 ngày | 1 dev | $0 |
| **TỔNG** | **~22 ngày** | **~3 người** | **~$85** |

**Ưu điểm:**
- ✅ Cân bằng tốc độ & chất lượng
- ✅ Chi phí thấp so với PA3 thuần manual
- ✅ Top địa điểm được verify kỹ
- ✅ Long tail được LLM enrich

**Nhược điểm:**
- ❌ Phức tạp hơn các PA khác
- ❌ Cần quản lý nhiều nguồn data

---

### 🔹 PHƯƠNG ÁN 5: Mua data từ vendor bên ngoài

**Mô tả:** Mua dataset du lịch Việt Nam từ các vendor như:
- **Google Places API** (trả phí theo request)
- **Foursquare API** (có free tier)
- **DataCove / Apify** (scraped data)
- **Local vendor**: VnTrip, Traveloka (B2B API)

**Cách thực hiện:**

1. **Google Places API** (~$32/1000 requests):
   ```python
   import googlemaps
   gmaps = googlemaps.Client(key='YOUR_KEY')
   
   # Search places ở Hội An
   results = gmaps.places(query='tourist attraction', location=(15.8801, 108.3380), radius=10000)
   ```
   - Lấy: name, address, lat/lon, rating, types, opening_hours
   - Ưu: data chính xác, real-time
   - Nhược: tốn tiền, chỉ có thông tin cơ bản (không có description dài)

2. **Foursquare Places API** (Free tier 950 calls/day):
   - Tương tự Google nhưng miễn phí hơn

3. **Apify TripAdvisor scraper** ($49/month):
   - Có sẵn dataset TripAdvisor cho Việt Nam
   - Bao gồm reviews, rating, photos

**Ước tính:**
- ⏱️ Thời gian: 3-7 ngày
- 💰 Chi phí: $50-200 tuỳ vendor
- 👥 Nhân lực: 1 dev

---

## 4. KẾ HOẠCH TRIỂN KHAI CHI TIẾT (PA4 - Khuyến nghị)

### 4.1 Timeline

```
Tuần 1 (Ngày 1-5): Crawl & Normalize
├── Ngày 1-2: Bổ sung config sources (Hội An, Huế)
├── Ngày 2-3: Viết parsers mới (2 parsers)
├── Ngày 3-4: Chạy crawl pipeline, debug
└── Ngày 5: Normalize + dedupe → raw_data.csv

Tuần 2 (Ngày 6-10): LLM Enrichment
├── Ngày 6: Viết script llm_enrich.py
├── Ngày 7-8: Chạy enrich (background job)
├── Ngày 9: Review output, fix lỗi LLM
└── Ngày 10: Validate schema → enriched_data.csv

Tuần 3 (Ngày 11-17): Top Places Manual
├── Ngày 11-12: List TOP 100 places/thành phố
├── Ngày 13-15: CTV nhập data vào Google Sheet
├── Ngày 16: Review chéo
└── Ngày 17: Export top_places.csv

Tuần 4 (Ngày 18-22): Merge & Deploy
├── Ngày 18: Merge + dedupe final
├── Ngày 19-20: Recompute embeddings
├── Ngày 21: Update code (CITY_PATTERNS, etc.)
└── Ngày 22: Testing, deploy
```

### 4.2 Checklist theo thành phố

#### 🌊 ĐÀ NẴNG (chuẩn hoá từ data hiện tại)

**Tasks:**
- [ ] Review 905 rows hiện tại, phân loại:
  - [ ] ~250 rows chất lượng cao (giữ nguyên)
  - [ ] ~400 rows chất lượng trung bình (LLM enrich)
  - [ ] ~250 rows rác (xoá hoặc enrich mạnh)
- [ ] Phân bổ lại category:
  - [ ] Sightseeing: 200 (từ 833 hiện tại → lọc TOP)
  - [ ] Food: 80 (hiện gần như không có)
  - [ ] Hotel: 50 (cần crawl từ Booking/Agoda)
  - [ ] Event: 30 (cần thêm lễ hội, chợ đêm, show)
- [ ] Bổ sung toạ độ (~600 rows đang thiếu)
- [ ] Crawl `placesdetail.csv` cho 50 địa danh chính

#### 🏮 HỘI AN (~240 địa điểm mới)

**Nguồn crawl:**
- [ ] https://hoiantourism.gov.vn/ (Sở Du lịch Hội An)
- [ ] https://whc.unesco.org/en/list/948 (UNESCO - Phố cổ Hội An)
- [ ] Wikipedia: `/wiki/Hội_An`, `/wiki/Phố_cổ_Hội_An`
- [ ] Google Places API
- [ ] TripAdvisor

**Top 20 địa điểm PHẢI CÓ:**
1. Phố cổ Hội An (UNESCO)
2. Chùa Cầu (Lai Viễn Kiều)
3. Hội quán Phúc Kiến
4. Hội quán Triều Châu
5. Hội quán Hải Nam
6. Nhà cổ Tấn Ký
7. Nhà cổ Phùng Hưng
8. Bảo tàng Văn hoá dân gian Hội An
9. Làng gốm Thanh Hà
10. Làng mộc Kim Bồng
11. Biển An Bàng
12. Biển Cửa Đại
13. Cù Lao Chàm
14. Rừng dừa Bảy Mẫu
15. Xưởng đèn lồng Hội An
16. Chợ đêm Hội An
17. Bánh mì Phượng
18. Cao lầu Thanh
19. Mì Quảng Bà Mua
20. Khách sạn: Anantara, Four Seasons The Nam Hai

#### 🏛️ HUẾ (~300 địa điểm mới)

**Nguồn crawl:**
- [ ] https://thuathienhue.gov.vn/
- [ ] https://huecity.vn/
- [ ] Wikipedia: `/wiki/Huế`, `/wiki/Kinh_thành_Huế`
- [ ] Google Places API
- [ ] TripAdvisor

**Top 20 địa điểm PHẢI CÓ:**
1. Đại Nội (Kinh thành Huế)
2. Ngọ Môn
3. Điện Thái Hoà
4. Tử Cấm Thành
5. Hưng Miếu
6. Chùa Thiên Mụ
7. Lăng Tự Đức
8. Lăng Minh Mạng
9. Lăng Khải Định
10. Lăng Gia Long
11. Chùa Từ Đàm
12. Núi Ngự Bình
13. Sông Hương
14. Cầu Trường Tiền
15. Chợ Đông Ba
16. Đại học Huế
17. Bún bò Huế O Phượng
18. Cơm hến Nàng Buổi
19. Bánh bèo, bánh nậm
20. Khách sạn: Azerai La Residence, Pilgrimage Village

---

## 5. Code Updates cần thiết

### 5.1 Cập nhật `src/query_extractor.py` (line 50-60)

```python
# Thêm vào CITY_PATTERNS
CITY_PATTERNS = {
    'da nang': [r'đà nẵng', r'da nang', r'danang', r'dn'],
    'hoi an': [r'hội an', r'hoi an', r'hoian'],
    'hue': [r'huế', r'hue'],
    # Optional: multi-city
    'central vietnam': [r'miền trung', r'central vietnam', r'ba miền trung'],
}
```

### 5.2 Cập nhật `src/recommender.py` (line 140)

```python
CITY_MAP = {
    "dn": "da nang",
    "danang": "da nang",
    "đà nẵng": "da nang",
    "da nang": "da nang",
    # Hội An
    "hoian": "hoi an",
    "hội an": "hoi an",
    # Huế
    "hue": "hue",
    "huế": "hue",
}
```

### 5.3 Update logic multi-city trong recommender

```python
def recommend_multi_city(self, query, cities, days_per_city, budget_total):
    """Lập lịch trình nhiều thành phố (ĐN → Hội An → Huế)"""
    per_city_budget = budget_total / len(cities)
    full_itinerary = []
    current_day = 1
    
    for city, days in zip(cities, days_per_city):
        city_rec = self.recommend(
            query=query,
            city=city,
            top_k=200,
        )
        city_itinerary = self._build_itinerary(
            city_rec, days=days, 
            per_day_budget=per_city_budget,
            start_day=current_day
        )
        full_itinerary.extend(city_itinerary)
        current_day += days
    
    return full_itinerary
```

---

## 6. Tiêu chí thành công (KPIs)

| KPI | Mục tiêu | Cách đo |
|-----|----------|---------|
| Số địa điểm/thành phố | ≥ 240 (Hội An), ≥ 300 (Huế) | Count rows in places.csv |
| Tỷ lệ có toạ độ | ≥ 95% | Count rows where lat,lon ≠ 0 |
| Tỷ lệ có description ≥ 30 chars | ≥ 95% | Filter + count |
| Tỷ lệ có rating > 0 | ≥ 90% | Filter + count |
| Phân bố category | sightseeing 50%, food 25%, hotel 15%, event 10% | Group by category |
| Test query "Đi Hội An 2 ngày" | Trả về ≥ 5 địa điểm Hội An | Manual test |
| Test query "Tour 3 miền trung 5 ngày" | Trả về lịch trình qua 3 thành phố | Manual test |
| Latency recommendation | < 3s | Time API call |
| Q&A accuracy (Cầu Rồng ở đâu?) | ≥ 80% trả lời đúng | Manual test 20 câu |

---

## 7. Rủi ro & Mitigation

| Rủi ro | Xác suất | Impact | Mitigation |
|--------|----------|--------|------------|
| Website chính phủ block IP | Trung bình | Cao | Dùng proxy, retry, backoff |
| LLM hallucinate thông tin | Cao | Trung bình | Spot-check 20% output, dùng GPT-4 cho sample test |
| Google API hết quota | Thấp | Cao | Fallback sang OSM/Nominatim |
| CTV nhập sai data | Trung bình | Trung bình | Review chéo, validation script |
| Embeddings chậm với dataset lớn | Thấm | Trung bình | Dùng FAISS hoặc approximate NN |

---

## 8. Bước tiếp theo (Action Items)

### Ngay lập tức (1-2 ngày)
- [ ] User xác nhận chọn phương án nào (PA1-PA5)
- [ ] Lên danh sách TOP 50 địa điểm mỗi thành phố
- [ ] Chuẩn bị Google Sheet template cho CTV

### Tuần 1
- [ ] Bắt đầu crawl pipeline (nếu chọn PA1/PA2/PA4)
- [ ] Viết scrapers mới cho Hội An & Huế
- [ ] Update code để support 3 thành phố

### Tuần 2-3
- [ ] LLM enrichment (nếu chọn PA2/PA4)
- [ ] Manual data entry cho top places (nếu chọn PA3/PA4)

### Tuần 4
- [ ] Merge, validate, deploy
- [ ] Testing với user

---

**Tác giả:** Cursor Assistant
**Ngày tạo:** 04/10/2026
**Trạng thái:** Draft v1.0 - chờ user feedback