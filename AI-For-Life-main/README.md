# 🗺️ AI Travel Assistant - Hệ thống Gợi ý Du lịch Thông minh

Hệ thống AI hỗ trợ lập lịch trình du lịch và trả lời câu hỏi về địa điểm sử dụng các công nghệ AI tiên tiến.

---

## 📋 MÔ TẢ DỰ ÁN

### Chức năng chính:
1. **Lập lịch trình du lịch** - Tự động tạo itinerary dựa trên sở thích, ngân sách, số ngày
2. **Q&A về địa điểm** - Trả lời câu hỏi về thông tin địa điểm du lịch
3. **Vision Q&A** - Nhận diện địa danh từ ảnh và cung cấp thông tin
4. **Gợi ý thông minh** - Sử dụng AI để recommend địa điểm phù hợp

### Công nghệ sử dụng:
- **Embedding**: Sentence Transformers (E5) và Bi-Encoder (BGE)
- **Reranking**: Cross-Encoder (BGE Reranker)
- **Similarity**: Cosine Similarity
- **Text Processing**: Regex, Heuristics, Fuzzy Matching
- **Geographic**: Haversine Distance
- **Vision AI**: Hugging Face (local, miễn phí, mặc định) / Gemini / OpenAI
- **LLM**: OpenAI / Gemini (tùy chọn)
- **Search**: Google Search API (tùy chọn)

---

## 🚀 CÀI ĐẶT VÀ CHẠY

### Bước 1: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Bước 2: Cấu hình API Keys

**File `.env` đã có sẵn** - Chỉ cần thêm các keys còn thiếu nếu muốn dùng:

Mở file `.env` trong thư mục gốc và thêm (nếu cần):

```env
# Google Search API (TÙY CHỌN - thêm nếu có)
GOOGLE_SEARCH_API_KEY=your-google-api-key
GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id

# LLM Provider (TÙY CHỌN - thêm nếu muốn dùng)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

**Lưu ý:**
- **Vision Q&A**: Mặc định dùng **Hugging Face** (local, miễn phí, không cần API key) - đã cấu hình trong `.env`
- Có thể đổi sang Gemini hoặc OpenAI bằng cách set `VISION_PROVIDER=gemini` hoặc `VISION_PROVIDER=openai` trong `.env`
- `OPENAI_API_KEY` và `GEMINI_API_KEY` đã có trong `.env` - có thể dùng nếu muốn đổi provider
- `GOOGLE_SEARCH_API_KEY` và `LLM_PROVIDER` là **TÙY CHỌN** - hệ thống vẫn chạy bình thường nếu không có

### Bước 3: Chạy server

```bash
python main.py
```

Hoặc:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Bước 4: Truy cập

- **Web UI**: Mở file `ui.html` trong trình duyệt
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/

---

## 📁 CẤU TRÚC DỰ ÁN

```
AI-For-Life-main/
├── main.py                 # Main API server
├── ui.html                 # Web UI
├── .env                    # API keys (đã có sẵn)
├── requirements.txt        # Dependencies
├── diagrams.puml          # PlantUML diagrams
│
├── src/
│   ├── recommender.py      # Core recommendation engine
│   ├── qa.py               # Q&A system
│   ├── query_extractor.py  # Extract info from query
│   ├── plan_guard.py       # Validate itinerary
│   ├── explain_ability.py  # Explain recommendations
│   ├── google_search.py    # Google Search API
│   ├── llm_processor.py    # LLM processing
│   ├── vision_qa_openai.py # Vision Q&A với OpenAI
│   └── ...
│
├── data/
│   ├── places.csv          # Dữ liệu địa điểm (1043+ places)
│   ├── placesdetail.csv    # Thông tin chi tiết về địa điểm
│   └── ...
│
├── scraper/                # Hệ thống crawl dữ liệu
│   ├── runner.py           # Orchestrator
│   ├── normalizer.py       # Normalize data
│   ├── dedupe.py           # Deduplicate
│   └── parsers/            # Parsers cho các nguồn
│       ├── opendata_danang.py
│       ├── tourism_danang_gov.py
│       ├── wikipedia_parser.py
│       └── ...
│
├── crawl_all_sources.py     # Crawl tất cả nguồn (places.csv)
├── crawl_place_details_full.py  # Crawl chi tiết (placesdetail.csv)
├── run_full_crawl.py       # Crawl đầy đủ (cả 2 bước)
├── normalize_places_format.py  # Normalize format
├── fix_categories.py        # Fix categories
├── analyze_categories.py    # Analyze categories
└── final_summary.py         # Summary statistics
│
└── models/
    ├── nn_embeds.npy        # Precomputed embeddings
    └── ...
```

---

## 📥 CRAWL DỮ LIỆU (Tùy chọn)

Hệ thống đã có sẵn dữ liệu trong `data/places.csv` (1043+ địa điểm). Nếu muốn cập nhật hoặc crawl thêm:

### Crawl từ các nguồn chính thức:
1. **OpenData Đà Nẵng** - https://opendata.danang.gov.vn/
2. **Sở Du lịch Đà Nẵng** - https://tourism.danang.gov.vn/
3. **Smart City API** - http://123.31.12.154:8080/TravelAPI/
4. **Tổng cục Du lịch Việt Nam** - https://vietnamtourism.gov.vn/
5. **Wikipedia** - https://vi.wikipedia.org/

### Cách chạy:

**1. Crawl tất cả nguồn (places.csv):**
```bash
python crawl_all_sources.py
```

**2. Crawl thông tin chi tiết (placesdetail.csv):**
```bash
python crawl_place_details_full.py
```

**3. Crawl đầy đủ (cả 2 bước):**
```bash
python run_full_crawl.py
```

**4. Normalize format:**
```bash
python normalize_places_format.py
```

**5. Fix categories:**
```bash
python fix_categories.py
```

**6. Xem thống kê:**
```bash
python final_summary.py
```

### Lưu ý:
- Crawl có thể mất thời gian (vài phút đến vài giờ)
- Script tự động đợi giữa các request để tránh rate limit
- Dữ liệu đã crawl sẽ được lưu, không crawl lại nếu đã có
- Backup tự động được lưu trong `backups/`

---

## 🎯 CÁC TÍNH NĂNG

### 1. Lập lịch trình (Itinerary Planning)
- Tự động extract: budget, số ngày, thành phố, travel companion từ query
- Default: 3 triệu VND, 1 ngày, solo travel (đi 1 mình)
- Validate itinerary: budget, khoảng cách, thời gian
- Giải thích tại sao recommend các địa điểm

**API Endpoint:**
```
GET /itinerary?q=tham quan biển và ẩm thực&days=2&budget_total=5000000
```

### 2. Q&A System
- Trả lời câu hỏi về địa điểm
- Sử dụng `placesdetail.csv` cho thông tin chi tiết (lịch sử, điểm nổi bật, v.v.)
- Fuzzy matching và semantic search

**API Endpoint:**
```
GET /ask?q=Cầu Rồng ở đâu?
```

### 3. Vision Q&A
- Upload ảnh để nhận diện địa danh
- Hỗ trợ: **Hugging Face** (local, miễn phí, mặc định), **Gemini** (miễn phí), OpenAI
- Sử dụng database 100+ địa danh để cải thiện độ chính xác
- Tự động query thông tin sau khi nhận diện

**API Endpoint:**
```
POST /ask_photo (upload file)
POST /ask_photo_url?image_url=...
```

### 4. Smart Query
- Tự động phân luồng Q&A hoặc itinerary
- Có thể sử dụng LLM và Google Search để cải thiện kết quả

**API Endpoint:**
```
GET /smart_query?q=Đi Đà Nẵng 3 ngày&use_llm=true&use_google_search=true
```

### 5. Google Search Integration (Tùy chọn)
- Tìm kiếm thông tin bổ sung từ Google
- Tìm kiếm travel tips

**API Endpoint:**
```
GET /search?q=Đà Nẵng du lịch
GET /search_place?place_name=Cầu Rồng
```

### 6. LLM Processing (Tùy chọn)
- Xử lý query tự nhiên với LLM
- Extract thông tin từ query
- Enhance query để cải thiện kết quả

**API Endpoint:**
```
GET /llm_process?q=Đi Đà Nẵng 3 ngày với ngân sách 5 triệu
```

---

## 📊 BIỂU ĐỒ UML

File `diagrams.puml` chứa các biểu đồ PlantUML:

1. **Use Case Diagram** - Các use case của hệ thống
2. **Activity Diagram - Itinerary** - Luồng lập lịch trình
3. **Activity Diagram - Q&A** - Luồng Q&A system
4. **Activity Diagram - Vision** - Luồng Vision Q&A
5. **Class Diagram** - Cấu trúc các class
6. **State Diagram - Query Processing** - Trạng thái xử lý query
7. **State Diagram - System** - Trạng thái khởi tạo hệ thống
8. **Sequence Diagram - Itinerary** - Sequence lập lịch trình
9. **Sequence Diagram - Vision Q&A** - Sequence Vision Q&A

**Xem biểu đồ:**
- Online: https://www.plantuml.com/plantuml/uml/ (paste nội dung từ `diagrams.puml`)
- VS Code: Cài extension "PlantUML"
- IntelliJ: Cài plugin "PlantUML integration"

---

## 🔧 CÁC VIỆC CẦN LÀM

### ✅ Đã hoàn thành:
- [x] Embedding system (E5 + BGE)
- [x] Cosine Similarity
- [x] Cross-Encoder reranking
- [x] Regex & Heuristics
- [x] Haversine Distance
- [x] Plan Guard (validate itinerary)
- [x] Explain Ability (giải thích recommendations)
- [x] Query Extractor (tự động extract thông tin)
- [x] Default values (3 triệu, solo travel)
- [x] Vision Q&A (OpenAI, Gemini, Hugging Face)
- [x] Image upload trong UI
- [x] Q&A.csv database
- [x] Google Search API integration
- [x] LLM integration
- [x] PlantUML diagrams (Use Case, Activity, Class, State, Sequence)

### 📝 Cần làm (nếu muốn mở rộng):
- [ ] Thêm nhiều câu hỏi vào Q&A.csv
- [ ] Cải thiện accuracy của Vision Q&A
- [ ] Thêm nhiều thành phố vào database
- [ ] Tối ưu performance
- [ ] Thêm unit tests
- [ ] Deploy lên production

---

## 📊 API ENDPOINTS CHÍNH

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/` | GET | Health check |
| `/itinerary` | GET | Lập lịch trình |
| `/ask` | GET | Q&A về địa điểm |
| `/ask_photo` | POST | Vision Q&A (upload ảnh) |
| `/ask_photo_url` | POST | Vision Q&A (URL ảnh) |
| `/smart_query` | GET | Smart query với auto-routing |
| `/search` | GET | Google Search |
| `/search_place` | GET | Tìm thông tin địa điểm từ Google |
| `/llm_process` | GET | Xử lý query với LLM |
| `/docs` | GET | API documentation (Swagger) |

---

## 🔑 CẤU HÌNH API KEYS

### File `.env` đã có sẵn với:
- ✅ `OPENAI_API_KEY` - Đã có
- ✅ `GEMINI_API_KEY` - Đã có
- ✅ `OPENAI_VISION_MODEL` - Đã có
- ✅ `GEMINI_VISION_MODEL` - Đã có

### Cần thêm (nếu muốn dùng):
- `GOOGLE_SEARCH_API_KEY` - Google Search API
- `GOOGLE_SEARCH_ENGINE_ID` - Google Search Engine ID
- `LLM_PROVIDER` - LLM provider (openai/gemini)
- `LLM_MODEL` - LLM model name

**Hướng dẫn lấy API keys:**
- **Google Search API**: https://console.cloud.google.com/ → Custom Search API
- **OpenAI**: https://platform.openai.com/ → API Keys
- **Gemini**: https://makersuite.google.com/app/apikey

---

## 🧪 KIỂM TRA

### Kiểm tra các service đã khởi tạo:
```bash
curl http://localhost:8000/
```

### Test Itinerary:
```bash
curl "http://localhost:8000/itinerary?q=tham quan biển&days=2&budget_total=3000000"
```

### Test Q&A:
```bash
curl "http://localhost:8000/ask?q=Cầu Rồng ở đâu"
```

### Test Vision QA:
```bash
curl -X POST "http://localhost:8000/ask_photo" -F "file=@test_images/cau_rong.jpg"
```

---

## 📝 LƯU Ý

1. **File `.env`** không được commit lên Git (đã có trong `.gitignore`)
2. **Vision Q&A**: Mặc định dùng **Hugging Face** (local, miễn phí) - đã cấu hình trong `.env`
3. **OpenAI API Key** và **Gemini API Key** là tùy chọn - chỉ cần nếu muốn đổi provider
4. **Google Search** và **LLM** là tùy chọn, hệ thống vẫn chạy bình thường nếu không có
5. Kiểm tra logs khi khởi động để biết service nào đã được khởi tạo thành công
6. **Dữ liệu**: Đã có sẵn 1043+ địa điểm trong `data/places.csv`, không cần crawl lại nếu không muốn

---

## 🐛 Troubleshooting

### Lỗi Vision Q&A không hoạt động
- **Mặc định**: Dùng Hugging Face (local, miễn phí) - đã cấu hình trong `.env`
- Nếu lỗi, kiểm tra: `HF_USE_API=false` trong `.env` (dùng local model)
- Có thể cần cài: `pip install transformers torch pillow` nếu dùng local model
- Kiểm tra log để xem provider nào đã được khởi tạo

### Lỗi: "Google Search API chưa được cấu hình"
- Đây là cảnh báo, không phải lỗi
- Hệ thống vẫn chạy bình thường
- Chỉ cần thêm keys nếu muốn dùng tính năng Google Search

### Lỗi: "LLM Processor chưa được cấu hình"
- Đây là cảnh báo, không phải lỗi
- Hệ thống vẫn chạy bình thường
- Chỉ cần thêm keys nếu muốn dùng LLM processing

---

## 📚 TÀI LIỆU THAM KHẢO

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Google Custom Search API](https://developers.google.com/custom-search)
- [Sentence Transformers](https://www.sbert.net/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PlantUML Documentation](https://plantuml.com/)

---

## 📄 License

Dự án này được phát triển cho mục đích học tập và nghiên cứu.

---

**Chúc bạn sử dụng vui vẻ! 🎉**
