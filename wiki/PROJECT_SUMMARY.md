# 📋 TỔNG HỢP DỰ ÁN AI Travel Assistant

> **Ngày tạo:** 04/10/2026
> **Trạng thái:** Đang phát triển (v1.0.0)
> **Phạm vi hiện tại:** Chỉ tập trung vào **Đà Nẵng**

---

## 1. Giới thiệu tổng quan

**AI Travel Assistant** là hệ thống AI hỗ trợ **lập lịch trình du lịch** và **trả lời câu hỏi** về các địa điểm du lịch, sử dụng các công nghệ AI tiên tiến (Embedding, Reranking, Vision AI, LLM).

### Chức năng chính
1. 🗓️ **Lập lịch trình thông minh** – tự động tạo itinerary theo budget, số ngày, sở thích
3. 💬 **Q&A địa điểm** – trả lời câu hỏi về thông tin, lịch sử, điểm nổi bật
4. 📸 **Vision Q&A** – nhận diện địa danh từ ảnh upload
5. 🔍 **Smart Query** – tự động phân luồng Q&A hoặc itinerary
6. 🌐 **Google Search & LLM** (tùy chọn) – bổ sung thông tin ngoài

---

## 2. Tech Stack

| Lớp | Công nghệ |
|-----|-----------|
| **Backend** | FastAPI + Uvicorn (Python 3.11) |
| **Embedding** | Sentence-Transformers (`intfloat/multilingual-e5-base`) |
| **Reranking** | Cross-Encoder `BAAI/bge-reranker-v2-m3` |
| **Similarity** | Cosine similarity, TF-IDF (`scikit-learn`) |
| **Vision AI** | HuggingFace (mặc định, miễn phí) / Gemini / OpenAI |
| **LLM** | OpenAI GPT-4o-mini (mặc định) / Gemini |
| **Search** | Google Custom Search API (tùy chọn) |
| **Frontend** | HTML + CSS + Vanilla JS (`ui.html`) |
| **Data** | CSV (`data/places.csv`, `data/placesdetail.csv`) |
| **ML Models** | `models/nn_embeds.npy`, `models/tfidf_*.joblib` |

---

## 3. Cấu trúc thư mục dự án

```
d:\AI-For-Life-main\AI-For-Life-main\
├── main.py                    # FastAPI server (entry point chính)
├── ui.html                    # Web UI chat
├── .env                       # API keys (OpenAI, Gemini, Google Search)
├── requirements.txt           # Python dependencies
├── diagrams.puml              # PlantUML diagrams (9 loại)
├── README.md                  # Tài liệu dự án
├── nguoidung.txt              # User auth (JSON: users + sessions)
│
├── src/                       # Core modules
│   ├── recommender.py         # Engine recommendation chính (1700+ LOC)
│   ├── qa.py                  # Q&A system
│   ├── query_extractor.py     # Trích xuất budget/days/city từ query
│   ├── plan_guard.py          # Validate itinerary (budget, distance, time)
│   ├── explain_ability.py     # Giải thích recommendations
│   ├── google_search.py       # Google Search API
│   ├── llm_processor.py       # LLM processing (OpenAI/Gemini)
│   ├── vision_qa_huggingface.py  # Vision QA local (miễn phí)
│   ├── vision_qa_openai.py    # Vision QA OpenAI
│   ├── gemini_vision_qa.py    # Vision QA Gemini
│   ├── place_details.py       # Quản lý thông tin chi tiết
│   ├── textnorm.py            # Tiền xử lý text tiếng Việt
│   ├── etl.py                 # Load & clean dataset
│   ├── vectorizer.py          # TF-IDF vectorizer
│   ├── user_manager.py        # Quản lý user/session
│   └── schema.py              # Data schema (Destination dataclass)
│
├── data/
│   ├── places.csv             # 905 địa điểm (toàn bộ gán city="Da Nang")
│   ├── placesdetail.csv       # Thông tin chi tiết (hiện TRỐNG - chỉ có header)
│   └── itinerary_dataset.clean.csv  # (không có sẵn, recommender fallback)
│
├── models/
│   ├── nn_embeds.npy          # Embeddings pre-computed (905 × 768)
│   ├── tfidf_vectorizer.joblib
│   ├── tfidf_matrix.npz
│   └── ml_classifier.joblib   # Classifier ML (chưa dùng)
│
├── scraper/                   # Hệ thống crawl dữ liệu
│   ├── config.yaml            # Cấu hình 8 nguồn crawl
│   ├── runner.py              # Orchestrator chính
│   ├── normalizer.py          # Chuẩn hóa schema
│   ├── dedupe.py              # Loại bỏ trùng lặp
│   ├── daily_update.py        # Script cập nhật hàng ngày
│   └── parsers/               # 10 parsers cho các nguồn
│       ├── opendata_danang.py
│       ├── danang_tourism.py
│       ├── tourism_danang_gov.py
│       ├── smartcity_api.py
│       ├── vietnam_tourism.py
│       ├── danangfantasticity.py
│       ├── sunworld_bana.py
│       ├── detail_parser.py
│       ├── wikipedia_parser.py
│       └── base_parser.py
│
├── backups/                   # 19 file backup CSV (lưu theo timestamp)
├── static/                    # CSS + JS cho UI
└── test_images/               # 3 ảnh test (ba_na, cauvang, cau_rong)
```

---

## 4. Dataset hiện tại (data/places.csv)

### 4.1 Schema

| Cột | Kiểu | Mô tả |
|-----|------|--------|
| `id` | int | ID duy nhất |
| `name` | str | Tên địa điểm (tiếng Việt) |
| `city` | str | **LUÔN = "Da Nang"** ← vấn đề |
| `category` | str | sightseeing / cultural / shopping / entertainment / park / museum / beach |
| `avg_cost` | float | Chi phí trung bình (VND) |
| `duration_min` | int | Thời gian tham quan (phút) |
| `price_level` | str | $ / $$ / $$$ |
| `open_time` / `close_time` | str | Giờ mở/đóng |
| `closed_days` | str | Ngày nghỉ (Mon, Tue, …) |
| `rating` | float | 0.0 → 5.0 |
| `review_count` | int | Số review |
| `popularity` | float | 0.0 → 1.0 |
| `address` | str | Địa chỉ chi tiết |
| `tags` | str | Tag phân cách bởi `;` |
| `best_time` | str | All year / Morning / Evening / Weekend night |
| `description` | str | Mô tả ngắn |
| `lat` / `lon` | float | Toạ độ (nhiều row = 0) |
| `image_url` | str | URL ảnh (nhiều row trống) |

### 4.2 Thống kê

| Metric | Count |
|--------|-------|
| Tổng số địa điểm | **905 rows** |
| City = "Da Nang" | **900** (99.4%) |
| City = khác | 5 (lỗi encoding) |
| Category = sightseeing | **833 (92%)** ← mất cân đối |
| Có toạ độ (lat, lon ≠ 0) | **~250** (ước tính) |
| Có rating > 0 | **~400** |
| Có description | **~350** |

### 4.3 Vấn đề hiện tại của dataset

- ❌ **Chỉ có 1 thành phố** (Đà Nẵng), thiếu **Huế** và **Hội An**
- ❌ **Category mất cân đối** – 92% là `sightseeing`, thiếu `food`, `hotel`, `event`
- ❌ **Nhiều toạ độ = 0** → recommender không tính được khoảng cách
- ❌ **Nhiều description trống** → ảnh hưởng embedding
- ❌ **`placesdetail.csv` rỗng** → Q&A về lịch sử/đặc điểm không hoạt động
- ❌ **Không có hotel/food thực tế** → itinerary thiếu lựa chọn
- ❌ **Không có events thực** → lịch trình chưa phong phú

---

## 5. Kiến trúc hệ thống (luồng xử lý)

```
User Query
   │
   ▼
[QueryExtractor] ──► extract {budget, days, city, companion}
   │
   ▼
[LLM Processor] ──► enhance query (optional)
   │
   ▼
[Recommender]
   ├─► Filter by city
   ├─► Bi-Encoder (multilingual-e5-base) → top 200
   ├─► Keyword boost (match trong name/desc/tags)
   ├─► Cross-Encoder rerank (bge-reranker-v2-m3) → top 50
   ├─► Diversity filter (cosine < 0.85)
   └─► Slot optimization (morning/lunch/afternoon/evening/hotel)
   │
   ▼
[PlanGuard] ──► validate {budget, distance ≤50km, time slots}
   │
   ▼
[ExplainAbility] ──► giải thích recommendations
   │
   ▼
JSON Response → Frontend (ui.html)
```

---

## 6. Các API Endpoints chính

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/` | GET | Health check |
| `/itinerary` | GET | Lập lịch trình theo ngày |
| `/ask` | GET | Q&A địa điểm |
| `/ask_photo` | POST | Vision Q&A (upload ảnh) |
| `/ask_photo_url` | POST | Vision Q&A (URL ảnh) |
| `/smart_query` | GET | Auto-route Q&A hoặc itinerary |
| `/search` | GET | Google Search |
| `/search_place` | GET | Google Search theo tên địa điểm |
| `/place_details` | GET | Chi tiết (history/highlights/...) |
| `/llm_process` | GET | Xử lý query với LLM |
| `/auth/login` | POST | Đăng nhập |
| `/auth/register` | POST | Đăng ký |

---

## 7. Cấu hình & Secrets

File `.env` hiện tại đã có:
- ✅ `OPENAI_API_KEY` (sk-proj-…)
- ✅ `OPENAI_VISION_MODEL=gpt-4o-mini`
- ✅ `GEMINI_VISION_MODEL`
- ✅ `GOOGLE_SEARCH_API_KEY`
- ✅ `GOOGLE_SEARCH_ENGINE_ID`
- ✅ `LLM_PROVIDER=openai`
- ✅ `LLM_MODEL=gpt-4o-mini`
- ✅ `VISION_PROVIDER=huggingface` (mặc định local miễn phí)
- ✅ `HF_VISION_MODEL=Salesforce/blip-image-captioning-base`

---

## 8. Tính năng đã hoàn thành ✅

- [x] Embedding system (E5 + BGE)
- [x] Cosine Similarity + Cross-Encoder reranking
- [x] Regex & Heuristics cho text normalization
- [x] Haversine Distance (tính khoảng cách địa lý)
- [x] Plan Guard (validate itinerary)
- [x] Explain Ability (giải thích recommendations)
- [x] Query Extractor (tự động extract budget/days/city/companion)
- [x] Default values (3 triệu VND, 1 ngày, solo)
- [x] Vision Q&A (HuggingFace/Gemini/OpenAI)
- [x] Image upload UI
- [x] Google Search API integration
- [x] LLM integration (OpenAI/Gemini)
- [x] PlantUML diagrams (9 loại: Use Case, Activity, Class, State, Sequence)
- [x] User authentication (3 users demo)

---

## 9. Việc cần làm (TODO)

### 🔴 Ưu tiên cao (P0)

- [ ] **Mở rộng dataset cho Huế & Hội An** (~150-300 places mỗi thành phố)
- [ ] **Crawl/cập nhật `placesdetail.csv`** (lịch sử, đặc điểm, mẹo du lịch) cho 100+ địa danh chính
- [ ] **Cải thiện `category` distribution** – thêm food/hotel/event thực tế
- [ ] **Bổ sung toạ độ GPS** cho các địa điểm đang thiếu (= 0)
- [ ] **Test hệ thống với 3 thành phố** trong query extractor (hiện chỉ có `da nang` pattern)

### 🟡 Ưu tiên trung bình (P1)

- [ ] Thêm validation cho `Hoi An` / `Hue` trong `CITY_PATTERNS` (`src/query_extractor.py:50`)
- [ ] Cập nhật `CITY_MAP` trong `recommender.py:140`
- [ ] Cải thiện `accuracy` của Vision Q&A (mở rộng database ảnh địa danh)
- [ ] Tối ưu performance (hiện recommend mất ~3-5s do cross-encoder)
- [ ] Xử lý multi-city itinerary (Đà Nẵng → Hội An → Huế)
- [ ] Distance check giữa các thành phố (vd: Hội An ↔ Huế ~120km)

### 🟢 Ưu tiên thấp (P2)

- [ ] Thêm unit tests
- [ ] Deploy lên production (Docker, cloud)
- [ ] Mobile responsive UI
- [ ] Thêm tính năng đặt tour/hotel
- [ ] Tích hợp booking API
- [ ] Đa ngôn ngữ (Anh/Việt)

---

## 10. Risks & Technical Debt

| Rủi ro | Mức độ | Ghi chú |
|--------|--------|---------|
| Dataset chỉ 1 thành phố | 🔴 Cao | Cần mở rộng Huế + Hội An |
| `placesdetail.csv` rỗng | 🔴 Cao | Q&A không trả lời được về lịch sử |
| Lat/lon thiếu ~70% | 🟡 TB | Distance-based ranking kém |
| Không có food/hotel | 🟡 TB | Itinerary thiếu ăn/uống |
| Cross-encoder chậm (~2s) | 🟢 Thấp | Có thể cache hoặc dùng model nhỏ hơn |
| OpenAI API key có thể hết hạn | 🟢 Thấp | Cần monitor |

---

## 11. Hướng dẫn chạy nhanh

```bash
# 1. Activate venv (đã có sẵn)
cd d:\AI-For-Life-main\AI-For-Life-main
.venv\Scripts\activate

# 2. Chạy server
python main.py
# hoặc
uvicorn main:app --reload --port 8000

# 3. Mở UI
# Mở file ui.html trong browser

# 4. Test API
curl http://localhost:8000/
curl "http://localhost:8000/itinerary?q=đi đà nẵng 3 ngày 5 triệu"
```

---

## 12. Tài liệu tham khảo nội bộ

- 📄 `diagrams.puml` – 9 sơ đồ UML
- 📄 `README.md` – Tài liệu gốc
- 📁 `wiki/` – Folder tổng hợp này

---

**Tác giả tổng hợp:** Cursor Assistant
**Cập nhật lần cuối:** 04/10/2026