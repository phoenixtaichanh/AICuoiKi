# ✅ TODO CHECKLIST - AI Travel Assistant

> Cập nhật: 04/10/2026

---

## 🔴 P0 - ƯU TIÊN CAO (cần làm trước)

### Dataset
- [ ] Mở rộng dataset cho **Hội An** (≥ 240 địa điểm)
- [ ] Mở rộng dataset cho **Huế** (≥ 300 địa điểm)
- [ ] Chuẩn hoá 905 địa điểm Đà Nẵng hiện tại (lọc rác, điền thiếu)
- [ ] Cải thiện phân bố category (food/hotel/event đang thiếu)
- [ ] Bổ sung toạ độ GPS (~600 rows đang thiếu)
- [ ] Crawl `placesdetail.csv` cho top 50-100 địa danh chính (lịch sử, điểm nổi bật, mẹo)

### Code
- [ ] Update `CITY_PATTERNS` trong `src/query_extractor.py` (thêm `hoi an`, `hue`)
- [ ] Update `CITY_MAP` trong `src/recommender.py` (line ~140)
- [ ] Test query routing với 3 thành phố
- [ ] Rebuild embeddings (`models/nn_embeds.npy`)

### Testing
- [ ] Test `/itinerary?q=đi Hội An 2 ngày`
- [ ] Test `/itinerary?q=tour miền trung 5 ngày` (multi-city)
- [ ] Test `/ask?q=Cầu Rồng ở đâu?`
- [ ] Test `/ask_photo` với 3 ảnh test

---

## 🟡 P1 - ƯU TIÊN TRUNG BÌNH

### Tính năng
- [ ] Multi-city itinerary (Đà Nẵng → Hội An → Huế)
- [ ] Distance check giữa các thành phố
- [ ] Tự động detect city từ query (không cần user chỉ định)
- [ ] Cải thiện Vision Q&A accuracy (mở rộng database ảnh địa danh)
- [ ] Thêm weather API (gợi ý theo thời tiết)
- [ ] Thêm tính năng "save itinerary" cho user đã login

### Performance
- [ ] Cache embeddings (hiện compute mỗi lần recommend)
- [ ] Tối ưu cross-encoder (chậm ~2s)
- [ ] Dùng FAISS cho nearest neighbor search
- [ ] Async/await cho các API external (Google, LLM)

### Data quality
- [ ] Validation script (`validate_places.py`) - check schema, lat/lon, rating
- [ ] Auto-detect duplicate places (similarity > 0.9)
- [ ] Spot-check 20% output từ LLM enrich

---

## 🟢 P2 - ƯU TIÊN THẤP (nâng cao)

### Cải tiến
- [ ] Thêm unit tests (`tests/` folder)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Dockerize app
- [ ] Deploy lên cloud (AWS/GCP/Azure)
- [ ] Mobile responsive UI
- [ ] Đa ngôn ngữ (Anh/Việt/Trung/Nhật)
- [ ] Tích hợp booking API (Booking.com, Agoda)
- [ ] Thêm tính năng đánh giá/review cho user
- [ ] Real-time chat với admin

### Mở rộng
- [ ] Thêm **Hà Nội**, **TP.HCM**, **Nha Trang**, **Sapa**, **Phú Quốc**
- [ ] Tour liên tỉnh (Hà Nội - Hạ Long - Sapa)
- [ ] Flight/train recommendation
- [ ] Budget tracker (theo dõi chi tiêu thực tế)

---

## 🐛 BUGS / ISSUES CẦN FIX

- [ ] `placesdetail.csv` rỗng → Q&A về history/highlights không hoạt động
- [ ] Nhiều toạ độ (lat,lon) = 0 → distance calculation sai
- [ ] UI chưa responsive trên mobile
- [ ] Login form chưa kết nối backend (user mới không đăng ký được?)
- [ ] `intfloat/multilingual-e5-base` download lần đầu chậm ~500MB

---

## 📚 DOCUMENTATION

- [ ] API documentation (Swagger - đã có ở `/docs`)
- [ ] Setup guide cho dev mới
- [ ] Architecture diagram (đã có `diagrams.puml`)
- [ ] Contributing guide
- [ ] Changelog

---

## 📊 METRICS TO TRACK

- [ ] Số lượng địa điểm mỗi thành phố
- [ ] Tỷ lệ query thành công
- [ ] Average response time
- [ ] User retention (nếu có login)
- [ ] LLM cost per month
- [ ] Vision Q&A accuracy

---

## Cập nhật tiến độ

| Ngày | Hoàn thành | Ghi chú |
|------|------------|---------|
| 04/10/2026 | Tạo wiki folder | Tổng hợp dự án |
| | | |
