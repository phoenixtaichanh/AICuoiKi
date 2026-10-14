# 🏗️ KIẾN TRÚC & LUỒNG DỮ LIỆU

## Sơ đồ tổng quan

```
┌──────────────────────────────────────────────────────────────┐
│                        USER (Browser)                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  ui.html (HTML + CSS + Vanilla JS)                     │  │
│  │  - Chat UI                                             │  │
│  │  - Login Modal                                         │  │
│  │  - Image Upload                                        │  │
│  └─────────────────────┬──────────────────────────────────┘  │
└────────────────────────┼─────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Server (main.py)                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Endpoints:                                            │  │
│  │  - /itinerary    - /ask          - /ask_photo          │  │
│  │  - /smart_query  - /search       - /llm_process        │  │
│  │  - /place_details - /auth/login   - /auth/register      │  │
│  └─────────────────────┬──────────────────────────────────┘  │
└────────────────────────┼─────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┬──────────────┐
         ▼               ▼               ▼              ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐   ┌──────────┐
   │Recom-    │    │Q&A       │    │Vision QA │   │LLM       │
   │mender    │    │System    │    │(HF/      │   │Processor │
   │(src/     │    │(src/     │    │Gemini/   │   │(OpenAI/  │
   │recommen- │    │qa.py)    │    │OpenAI)   │   │Gemini)   │
   │der.py)   │    │          │    │          │   │          │
   └────┬─────┘    └────┬─────┘    └────┬─────┘   └────┬─────┘
        │               │               │              │
        │               │               │              │
   ┌────▼─────┐    ┌────▼─────┐    ┌────▼─────┐   ┌────▼─────┐
   │  E5      │    │  E5      │    │  BLIP /  │   │  GPT-4o  │
   │ Embedding│    │ Embedding│    │  Gemini  │   │  /Gemini │
   │ (Bi-     │    │ + TF-IDF │    │  Vision  │   │          │
   │ encoder) │    │ + Fuzzy  │    │  Model   │   │          │
   └────┬─────┘    └────┬─────┘    └──────────┘   └──────────┘
        │               │
        │               │
   ┌────▼─────┐    ┌────▼─────┐
   │  BGE     │    │ Place    │
   │ Rerank   │    │ Details  │
   │ (Cross-  │    │ Manager  │
   │ encoder) │    │          │
   └────┬─────┘    └──────────┘
        │
        ▼
   ┌─────────────────────────────────────────────┐
   │              DATA LAYER                      │
   │  - data/places.csv (905 rows)                │
   │  - data/placesdetail.csv (EMPTY!)            │
   │  - models/nn_embeds.npy (905 × 768)          │
   │  - models/tfidf_matrix.npz                   │
   └─────────────────────────────────────────────┘
```

---

## Luồng xử lý Itinerary

```
User Query: "Đi Đà Nẵng 3 ngày 5 triệu, thích biển và ẩm thực"
   │
   ▼
[1. QueryExtractor]
   - extract_budget_with_context() → 5,000,000 VND (total)
   - extract_days() → 3
   - extract_travel_companion() → "solo" (default)
   - extract_city() → "da nang"
   │
   ▼
[2. LLM Processor] (optional, if enabled)
   - Call OpenAI GPT-4o-mini
   - Extract: preferences=["beach", "food"], intent="itinerary"
   - Enhance query
   │
   ▼
[3. Recommender.recommend()]
   ├─► Filter by city="Da Nang" (case-insensitive, contains)
   ├─► Bi-Encoder (multilingual-e5-base)
   │   - Encode query → 768-dim vector
   │   - Cosine similarity với 905 embeddings
   │   - Top 200 candidates
   │
   ├─► Keyword Boosting
   │   - Nếu keyword trong name: +0.3
   │   - Nếu keyword trong desc: +0.15
   │   - Nếu keyword trong tags: +0.1
   │
   ├─► Cross-Encoder Reranking (bge-reranker-v2-m3)
   │   - Rerank top 50
   │   - Scores 0-1
   │
   ├─► Diversity Filter (cosine < 0.85)
   │   - Loại bỏ places quá giống nhau
   │
   └─► Return: 200 ranked results
   │
   ▼
[4. Recommender.itinerary()]
   ├─► Categorize: S(sightseeing), F(food), H(hotel), E(event)
   ├─► Per day budget = 5M / 3 = 1.67M
   ├─► Per day allocation:
   │   - Hotel: 50% = 833K
   │   - Food: 25% = 416K (lunch + dinner)
   │   - Event: 15% = 250K
   │   - Sightseeing: free
   │
   ├─► For each day (1, 2, 3):
   │   ├─► Morning: pick sightseeing (open_time < 12:00)
   │   ├─► Lunch: pick food (avg_cost ~25% per_day_budget)
   │   ├─► Afternoon: pick sightseeing (distance < 50km)
   │   ├─► Evening: pick event (open_time > 18:00)
   │   └─► Hotel: pick hotel (avg_cost ~50% per_day_budget)
   │
   ├─► Distance check (haversine) giữa các slot
   ├─► Diversity check (không trùng ngày)
   │
   └─► Return: 3-day itinerary
   │
   ▼
[5. PlanGuard.validate_itinerary()]
   - Validate budget (≤ 5M + 15% overrun)
   - Validate distance (≤ 50km/ngày)
   - Validate time slots (giờ mở/đóng)
   │
   ▼
[6. ExplainAbility.explain_full_itinerary()]
   - Generate reasons cho từng recommendation
   │
   ▼
[7. Response JSON] → Frontend
```

---

## Luồng xử lý Q&A

```
User Query: "Cầu Rồng ở đâu?"
   │
   ▼
[1. QASystem.answer_question()]
   │
   ├─► _fuzzy_match_name("Cầu Rồng ở đâu?")
   │   - Match với place_names trong places.csv
   │   - Score: fuzz.token_sort_ratio
   │   - Threshold: 70
   │   - Match: "Cầu Rồng" (score 95)
   │
   ├─► _extract_question_type()
   │   - Detect: "ở đâu" → question_type = "location"
   │
   ├─► _get_place_info(idx)
   │   - Return: name, category, address, opening_hours, price, rating
   │
   └─► Format answer từ PlaceDetailsManager
       - placesdetail.csv (HIỆN RỖNG) → chỉ trả về info cơ bản
   │
   ▼
[2. Optional: Google Search]
   - Nếu enabled, bổ sung thông tin từ Google
   │
   ▼
[3. Response JSON]
```

---

## Luồng xử lý Vision Q&A

```
User upload: cau_rong.jpg
   │
   ▼
[1. /ask_photo endpoint]
   - Save file tạm vào temp_uploads/
   │
   ▼
[2. Vision QA (provider: huggingface/gemini/openai)]
   │
   ├─► HuggingFace (default, local):
   │   - Model: Salesforce/blip-image-captioning-base
   │   - Caption: "a dragon bridge over a river at night"
   │
   ├─► Gemini (fallback):
   │   - Model: gemini-2.0-flash-exp
   │   - Response: "Đây là Cầu Rồng tại Đà Nẵng, Việt Nam"
   │
   └─► OpenAI (last fallback):
       - Model: gpt-4o-mini
   │
   ▼
[3. Match caption/response với places.csv]
   - Fuzzy match → "Cầu Rồng"
   │
   ▼
[4. Get place details từ matched place]
   │
   ▼
[5. Response JSON] → Frontend
```

---

## Database Schema

### places.csv
```python
{
    "id": int,                    # PRIMARY KEY
    "name": str,                  # Tên địa điểm (tiếng Việt)
    "city": str,                  # "Da Nang" | "Hoi An" | "Hue"
    "category": str,              # sightseeing | food | hotel | event | cultural | shopping | park | museum | beach
    "avg_cost": float,            # VND
    "duration_min": int,          # Phút
    "price_level": str,           # $ | $$ | $$$
    "open_time": str,             # "08:00"
    "close_time": str,            # "22:00"
    "closed_days": str,           # "Mon" | "" (comma-separated nếu nhiều)
    "rating": float,              # 0.0 - 5.0
    "review_count": int,
    "popularity": float,          # 0.0 - 1.0
    "address": str,
    "tags": str,                  # "tag1;tag2;tag3"
    "best_time": str,             # "All year" | "Morning" | "Evening" | "Weekend night"
    "description": str,
    "lat": float,
    "lon": float,
    "image_url": str
}
```

### placesdetail.csv (hiện rỗng)
```python
{
    "place_id": str,
    "place_name": str,
    "history": str,               # Lịch sử hình thành
    "highlights": str,            # Điểm nổi bật
    "cultural_info": str,         # Thông tin văn hoá
    "events": str,                # Sự kiện
    "architecture": str,          # Kiến trúc
    "significance": str,          # Ý nghĩa
    "visitor_tips": str,          # Mẹo du lịch
    "nearby_attractions": str,    # Địa điểm gần
    "detailed_description": str,
    "images": str,
    "videos": str,
    "source_urls": str,
    "last_updated": str
}
```

---

## Models (cached)

| File | Size | Mô tả |
|------|------|-------|
| `models/nn_embeds.npy` | 540 KB | Embeddings 905 × 768 (float32) |
| `models/tfidf_vectorizer.joblib` | 54 KB | TF-IDF vectorizer |
| `models/tfidf_matrix.npz` | 30 KB | Sparse TF-IDF matrix |
| `models/ml_classifier.joblib` | 19 KB | ML classifier (chưa dùng) |

---

## Performance Notes

| Operation | Latency | Bottleneck |
|-----------|---------|------------|
| Cold start (load models) | 10-15s | Sentence-Transformers load |
| Bi-encoder encode | ~50ms | CPU (không có GPU) |
| Cross-encoder rerank (50 docs) | ~2s | Model inference |
| TF-IDF search | <10ms | Sparse matrix lookup |
| LLM call (OpenAI) | ~1-3s | Network + API |
| Vision QA (HuggingFace local) | ~3-5s | Image processing |
| Vision QA (OpenAI) | ~2-4s | Network + API |
| **Total `/itinerary`** | **~3-5s** | Cross-encoder rerank |

---

## Deployment Considerations

Hiện tại app chạy local (uvicorn). Để deploy production cần:

1. **WSGI server**: Gunicorn + Uvicorn workers
2. **Reverse proxy**: Nginx
3. **Container**: Docker
4. **Cloud**: AWS ECS / GCP Cloud Run / Azure Container Apps
5. **Storage**: S3 / GCS cho images
6. **CDN**: CloudFlare
7. **Monitoring**: Prometheus + Grafana
8. **Logging**: ELK Stack

Cấu hình gợi ý cho 1000 req/day:
- 2 vCPU, 4GB RAM
- Auto-scale 2-4 instances
- Redis cache cho embeddings
