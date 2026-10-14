"""
Build plans_simple.json - 24 hard-coded plans with full detail.
Mỗi plan tham chiếu place_id từ places_clean.csv (dataset).
Budget cập nhật theo rule: prompt ví dụ là TỔNG budget (per person).
"""
import json
import pandas as pd
from pathlib import Path

DATA_DIR = Path("D:/AI-For-Life-main/AI-For-Life-main/data")
PLAN_OUT = Path("D:/AI-For-Life-main/AI-For-Life-main/src/plans/plans_simple.json")

df = pd.read_csv(DATA_DIR / "places_clean.csv")
PLACES = {int(r["id"]): r.to_dict() for _, r in df.iterrows()}

def P(pid):
    """Lookup place by id, return clean dict."""
    p = PLACES.get(int(pid))
    if p is None:
        return None
    return {
        "id": int(p["id"]),
        "name": str(p["name"]),
        "category": str(p["category"]),
        "city": str(p["city"]),
        "address": str(p.get("address", "") or ""),
        "rating": float(p["rating"]) if pd.notna(p["rating"]) else 0.0,
        "reviewCount": int(p["review_count"]) if pd.notna(p["review_count"]) else 0,
        "openingTime": str(p.get("open_time", "00:00") or "00:00"),
        "closingTime": str(p.get("close_time", "23:59") or "23:59"),
        "avgCost": int(p["avg_cost"]) if pd.notna(p["avg_cost"]) else 0,
        "priceLevel": str(p.get("price_level", "$") or "$"),
        "tags": str(p.get("tags", "") or ""),
        "durationMinutes": int(p["duration_min"]) if pd.notna(p["duration_min"]) else 60,
    }

def act(time, period, type_, loc, desc, cost_pp=None, dur=None, travel_from_prev=None):
    """Build an activity entry."""
    a = {
        "time": time,
        "period": period,
        "type": type_,
        "location": loc,
        "description": desc,
    }
    if cost_pp is not None:
        a["costPerPerson"] = cost_pp
    elif loc:
        a["costPerPerson"] = loc["avgCost"]
    if dur is not None:
        a["durationMinutes"] = dur
    elif loc:
        a["durationMinutes"] = loc["durationMinutes"]
    if travel_from_prev is not None:
        a["travelFromPreviousMinutes"] = travel_from_prev
    return a

# ============================================================
# ĐÀ NẴNG - 8 PLANS
# ============================================================

# Helper: Lấy restaurant/food cụ thể
DN_FOOD = {
    "my_quang_ba_mua": P(482),         # Mì Quảng Bà Mua
    "bun_cha_ca_ba_lu": P(487),        # Bún chả cá Bà Lữ
    "banh_xeo_ba_duong": P(483),       # Bánh xèo Bà Dưỡng
    "banh_mi_phuong": P(552),          # Bánh Mì Phượng (ĐN)
    "bun_mam_ba_van": P(488),          # Bún mắm bà Vân
    "bun_bo_co_ba": P(550),            # Bún bò Huế Cô Ba
    "hai_san_nam_danh": P(484),        # Hải sản Năm Đảnh
    "hai_san_be_anh": P(506),          # Hải sản Bé Anh
    "banh_beo_ba_be": P(494),          # Bánh bèo nậm lọc Bà Bé
    "kem_bo_co_van": P(489),           # Kem bơ Cô Vân
    "com_ga": P(149),
    "banh_xeo_tom_nhay": P(557),
    "pho_ha_noi": P(549),
}
DN_SIGHT = {
    "my_khe": P(3),
    "ngu_hanh_son": P(12),
    "ba_na": P(4),
    "cau_vang": P(5),
    "cau_rong": P(2),
    "cau_song_han": P(27),
    "cau_tinh_yeu": P(24),
    "son_tra": P(15),
    "chua_linh_ung": P(7),
    "sun_wheel": P(38),
    "cham_museum": P(35),
    "non_nuoc": P(36),
    "cu_lao_cham": P(37),
    "hoa_phu_thanh": P(52),
    "nui_than_tai": P(49),
    "han_market": P(18),
    "con_market": P(25),
    "helio_market": P(17),
    "asia_park": P(26),
    "vincom": P(50),
    "3d_trickeye": P(51),
    "nhatho_conga": P(31),
}
DN_HOTEL = {
    "sana": P(602),                # budget;beach;modern;couple 550k
    "nguyen_gia": P(604),          # 480k beach
    "sea_vista": P(603),            # 400k apt
    "sunview": P(605),             # 420k beach
    "doha": P(606),                # 350k city
    "signature": P(607),           # 500k heritage
    "dn_boutique": P(608),         # 850k city
    "cozy_dn": P(609),             # 900k boutique
    "nalod": P(610),               # 1.2M beach
    "m_village": P(611),           # 700k city
    "m_hotel": P(612),             # 2.3M beach
    "sala": P(613),                # 1.4M beach
    "hyatt": P(58),                # 4.5M resort
    "intercon": P(81),             # 8M ultra luxury
    "premier_village": P(116),     # 5.5M villa
    "marriott": P(117),            # 7M resort
    "wellness": P(118),            # 9M wellness
    "furama": P(515),              # 4.5M resort
    "pullman": P(516),             # 3.8M resort
    "hai_an": P(528),              # 1.8M sea
    "vinpearl_river": P(519),      # 2.4M condotel
    "brilliant": P(522),           # 1.8M river
    "grand_mercure": P(520),       # 2.2M island
    "four_points": P(518),         # 2.8M rooftop
    "novotel": P(82),              # 2.8M river
    "sel_de_mer": P(525),          # 2.2M sea
    "sheraton": P(531),            # 6M conference
    "crowne_plaza": P(532),        # 5M casino
    "naman": P(517),               # 5.5M retreat
}

# === DN01-s: 3N2Đ, 4.5-6tr, 2-3 người (balanced) ===
# budget/người = 4.5-6tr, total = 4.5*2=9tr đến 6*3=18tr. Use ~12tr mid-budget.
DN01 = {
    "id": "DN01-s",
    "city": "Da Nang",
    "title": "Đà Nẵng First Trip 3N2Đ - Khám phá biển và ẩm thực",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 2, "max": 3},
    "budgetPerPerson": {"min": 4500000, "max": 6000000},
    "style": "balanced",
    "hotel": DN_HOTEL["sana"],
    "days": [
        {
            "day": 1,
            "title": "Biển Mỹ Khê + Cầu Rồng",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    DN_FOOD["my_quang_ba_mua"],
                    "Ăn sáng với tô mì Quảng Bà Mua trứ danh"),
                act("09:30-11:30", "Sáng", "attraction",
                    DN_SIGHT["ngu_hanh_son"],
                    "Tham quan Ngũ Hành Sơn - 5 ngọn núi đá vôi với hang động và chùa chiền", travel_from_prev=30),
                act("12:00-13:00", "Trưa", "food",
                    DN_FOOD["banh_xeo_ba_duong"],
                    "Ăn trưa với bánh xèo Bà Dưỡng - đặc sản Đà Nẵng", travel_from_prev=15),
                act("13:00-14:30", "Trưa", "rest",
                    DN_HOTEL["sana"],
                    "Nghỉ trưa tại khách sạn Sana Danang Beach", travel_from_prev=20),
                act("14:30-17:00", "Chiều", "attraction",
                    DN_SIGHT["my_khe"],
                    "Tắm biển Mỹ Khê - 1 trong 6 bãi biển đẹp nhất hành tinh", travel_from_prev=15),
                act("18:30-20:00", "Tối", "food",
                    DN_FOOD["hai_san_be_anh"],
                    "Ăn tối hải sản Bé Anh - view biển Mỹ Khê", travel_from_prev=30),
                act("20:00-21:30", "Tối", "attraction",
                    DN_SIGHT["cau_rong"],
                    "Ngắm Cầu Rồng phun lửa 21:00 + dạo Sông Hàn", travel_from_prev=15),
            ]
        },
        {
            "day": 2,
            "title": "Bà Nà Hills - Cầu Vàng",
            "activities": [
                act("07:00-08:00", "Sáng", "food",
                    DN_FOOD["bun_cha_ca_ba_lu"],
                    "Ăn sáng bún chả cá Bà Lữ - hơn 70 năm tuổi"),
                act("08:00-08:45", "Sáng", "travel", None,
                    "Di chuyển từ Đà Nẵng lên Sun World Bà Nà Hills", travel_from_prev=20),
                act("08:45-16:00", "Cả ngày", "attraction",
                    DN_SIGHT["ba_na"],
                    "Cáp treo Guinness 5.801m, tham quan Cầu Vàng, Làng Pháp, Fantasy Park"),
                act("12:00-13:00", "Trưa", "food",
                    P(509),  # Panorama
                    "Buffet trưa tại Panorama Restaurant view núi"),
                act("17:00-18:00", "Chiều", "rest",
                    DN_HOTEL["sana"],
                    "Về khách sạn nghỉ ngơi", travel_from_prev=45),
                act("18:30-20:00", "Tối", "food",
                    DN_FOOD["hai_san_nam_danh"],
                    "Ăn tối hải sản Năm Đảnh - giá tốt cho cả gia đình"),
                act("20:00-21:30", "Tối", "attraction",
                    DN_SIGHT["helio_market"],
                    "Đi chợ đêm Helio - ăn vặt và mua quà", travel_from_prev=15),
            ]
        },
        {
            "day": 3,
            "title": "Sơn Trà - Linh Ứng - Bảo tàng Chăm",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    DN_FOOD["banh_beo_ba_be"],
                    "Ăn sáng bánh bèo nậm lọc Bà Bé - đặc sản miền Trung"),
                act("08:30-10:00", "Sáng", "attraction",
                    DN_SIGHT["chua_linh_ung"],
                    "Viếng Chùa Linh Ứng - tượng Phật Bà 67m", travel_from_prev=15),
                act("10:00-11:30", "Sáng", "attraction",
                    DN_SIGHT["son_tra"],
                    "Dạo bán đảo Sơn Trà - khám phá thiên nhiên", travel_from_prev=15),
                act("11:30-12:30", "Trưa", "food",
                    DN_FOOD["my_quang_ba_mua"],
                    "Ăn trưa mì Quảng Bà Mua - lần 2 cho đã"),
                act("12:30-14:00", "Trưa", "rest",
                    DN_HOTEL["sana"],
                    "Nghỉ trưa tại khách sạn", travel_from_prev=15),
                act("14:00-16:00", "Chiều", "attraction",
                    DN_SIGHT["cham_museum"],
                    "Bảo tàng Điêu khắc Chăm - di sản Chăm Pa", travel_from_prev=20),
                act("16:00-17:00", "Chiều", "shopping",
                    DN_SIGHT["han_market"],
                    "Mua đặc sản tại Chợ Hàn (mè xửng, mì Quảng gói)", travel_from_prev=15),
                act("18:00", "Tối", "end", None,
                    "Kết thúc chuyến đi, ra sân bay"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 1100000,        # 2 đêm x 550k
        "food": 1500000,         # 3 ngày
        "tickets": 1300000,      # Bà Nà + Ngũ Hành Sơn + Bảo tàng Chăm
        "transport": 600000,     # grab + taxi Bà Nà
        "other": 200000,
    },
    "estimatedTotalPerPerson": 4700000,
}

# === DN02-s: 3N2Đ, 5-7tr, cặp đôi ===
# 2 người x 5-7tr = 10-14tr total budget. Hotel 1.4M (Sala) x 2 nights = 2.8M ok.
DN02 = {
    "id": "DN02-s",
    "city": "Da Nang",
    "title": "Đà Nẵng Romantic 3N2Đ - Honeymoon cặp đôi",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 2, "max": 2},
    "budgetPerPerson": {"min": 5000000, "max": 7000000},
    "style": "romantic",
    "hotel": DN_HOTEL["sala"],   # 1.4M mid-range beach
    "days": [
        {
            "day": 1,
            "title": "Check-in + Cầu Tình Yêu + Sông Hàn",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    P(134),  # Hoi An Roastery style cafe ĐN: dùng 43 Factory
                    "Ăn sáng tại 43 Factory Coffee Roaster - specialty coffee Đà Nẵng"),
                act("09:00-10:00", "Sáng", "hotel",
                    DN_HOTEL["sala"],
                    "Check-in khách sạn Sala Danang Beach - view biển", travel_from_prev=15),
                act("10:00-12:00", "Sáng", "attraction",
                    DN_SIGHT["my_khe"],
                    "Tắm biển Mỹ Khê sáng sớm - nước trong và vắng", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    P(500),  # Thìa Gỗ coffee & lunch
                    "Ăn trưa tại Thìa Gỗ - cafe & Đà Nẵng Souvenirs", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "rest",
                    DN_HOTEL["sala"],
                    "Nghỉ trưa tại phòng khách sạn", travel_from_prev=20),
                act("15:00-17:00", "Chiều", "attraction",
                    DN_SIGHT["cau_tinh_yeu"],
                    "Đi Cầu Tình Yêu - gắn ổ khoá tình yêu", travel_from_prev=15),
                act("17:00-18:30", "Chiều", "attraction",
                    DN_SIGHT["cau_song_han"],
                    "Dạo Sông Hàn ngắm hoàng hôn", travel_from_prev=10),
                act("18:30-20:30", "Tối", "food",
                    P(508),  # La Maison 1888
                    "Dinner La Maison 1888 tại InterContinental - fine dining Pháp", travel_from_prev=15),
                act("20:30-22:00", "Tối", "attraction",
                    DN_SIGHT["cau_rong"],
                    "Cầu Rồng phun lửa 21:00 + chợ đêm Sơn Trà", travel_from_prev=15),
            ]
        },
        {
            "day": 2,
            "title": "Bà Nà Hills - Cầu Vàng - Spa đôi",
            "activities": [
                act("07:00-08:00", "Sáng", "food",
                    DN_FOOD["banh_xeo_ba_duong"],
                    "Ăn sáng bánh xèo Bà Dưỡng"),
                act("08:00-08:45", "Sáng", "travel", None,
                    "Di chuyển lên Sun World Bà Nà Hills", travel_from_prev=20),
                act("08:45-16:00", "Cả ngày", "attraction",
                    DN_SIGHT["ba_na"],
                    "Bà Nà Hills: cáp treo Guinness, Cầu Vàng, Làng Pháp, Fantasy Park"),
                act("12:00-13:30", "Trưa", "food",
                    P(509),  # Panorama
                    "Buffet trưa tại Panorama - view núi Bà Nà"),
                act("17:00-18:30", "Chiều", "hotel",
                    DN_HOTEL["sala"],
                    "Về khách sạn nghỉ ngơi", travel_from_prev=45),
                act("18:30-20:00", "Tối", "food",
                    P(539),  # Waterfront restaurant
                    "Dinner Waterfront - view sông Hàn, steakhouse", travel_from_prev=15),
                act("20:00-22:00", "Tối", "attraction",
                    P(500),  # cafe
                    "Cà phê rooftop & bar dành cho cặp đôi", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Sơn Trà - Ngũ Hành Sơn - Non Nước",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    DN_FOOD["my_quang_ba_mua"],
                    "Ăn sáng mì Quảng Bà Mua"),
                act("08:30-10:30", "Sáng", "attraction",
                    DN_SIGHT["son_tra"],
                    "Đi bán đảo Sơn Trà, viếng Chùa Linh Ứng", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "attraction",
                    DN_SIGHT["chua_linh_ung"],
                    "Chiêm bái tượng Phật Bà 67m tại Chùa Linh Ứng", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    DN_FOOD["hai_san_nam_danh"],
                    "Ăn trưa hải sản Năm Đảnh - view bán đảo", travel_from_prev=20),
                act("14:00-16:00", "Chiều", "attraction",
                    DN_SIGHT["ngu_hanh_son"],
                    "Ngũ Hành Sơn - leo núi ngắm biển", travel_from_prev=25),
                act("16:00-17:30", "Chiều", "attraction",
                    DN_SIGHT["non_nuoc"],
                    "Tắm biển Non Nước - yên tĩnh", travel_from_prev=15),
                act("17:30-19:00", "Chiều", "attraction",
                    P(434),  # Công viên Biển Đông
                    "Ngắm hoàng hôn Công viên Biển Đông", travel_from_prev=10),
                act("19:00-21:00", "Tối", "food",
                    P(508),  # La Maison 1888 (final dinner)
                    "Final dinner La Maison 1888 - fine dining", travel_from_prev=15),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 2800000,        # 2 đêm x 1.4M
        "food": 2400000,         # romantic dining
        "tickets": 1700000,      # Bà Nà + Ngũ Hành Sơn
        "transport": 800000,
        "other": 300000,
    },
    "estimatedTotalPerPerson": 4000000,  # cho 2 người = 8M / 2 = 4M/người
}

# === DN03-s: 4N3Đ, 6-8tr, nhóm 3-4 bạn trẻ ===
# 3-4 người x 6-8tr = 18-32tr total. Use hostel vibe.
DN03 = {
    "id": "DN03-s",
    "city": "Da Nang",
    "title": "Đà Nẵng Adventure 4N3Đ - Nhóm bạn trẻ năng động",
    "duration": "4 ngày 3 đêm",
    "durationDays": 4,
    "durationNights": 3,
    "travelers": {"min": 3, "max": 4},
    "budgetPerPerson": {"min": 6000000, "max": 8000000},
    "style": "adventure",
    "hotel": DN_HOTEL["m_hotel"],   # 2.3M beach, chia 2-3 phòng cho nhóm
    "days": [
        {
            "day": 1,
            "title": "Mỹ Khê + Sơn Trà + Chợ đêm",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    DN_FOOD["bun_cha_ca_ba_lu"],
                    "Ăn sáng bún chả cá Bà Lữ"),
                act("09:00-10:00", "Sáng", "hotel",
                    DN_HOTEL["m_hotel"],
                    "Check-in M Hotel Đà Nẵng - gần biển", travel_from_prev=20),
                act("10:00-12:00", "Sáng", "attraction",
                    DN_SIGHT["my_khe"],
                    "Tắm biển Mỹ Khê - surfing & chụp ảnh nhóm", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    DN_FOOD["hai_san_be_anh"],
                    "Ăn trưa hải sản Bé Anh", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "rest",
                    DN_HOTEL["m_hotel"],
                    "Nghỉ trưa + chơi bể bơi khách sạn", travel_from_prev=15),
                act("15:00-17:30", "Chiều", "attraction",
                    DN_SIGHT["son_tra"],
                    "Phượt bán đảo Sơn Trà - check in cây đa ngàn tuổi", travel_from_prev=20),
                act("18:00-20:00", "Tối", "food",
                    DN_FOOD["hai_san_nam_danh"],
                    "BBQ hải sản Năm Đảnh", travel_from_prev=20),
                act("20:00-22:00", "Tối", "attraction",
                    DN_SIGHT["helio_market"],
                    "Chợ đêm Helio - ăn vặt + quẩy", travel_from_prev=15),
            ]
        },
        {
            "day": 2,
            "title": "Bà Nà Hills - Cầu Vàng",
            "activities": [
                act("07:00-08:00", "Sáng", "food",
                    DN_FOOD["my_quang_ba_mua"],
                    "Ăn sáng mì Quảng Bà Mua"),
                act("08:00-08:45", "Sáng", "travel", None,
                    "Di chuyển lên Sun World Bà Nà Hills", travel_from_prev=20),
                act("08:45-16:00", "Cả ngày", "attraction",
                    DN_SIGHT["ba_na"],
                    "Bà Nà Hills: cáp treo Guinness, Cầu Vàng, Fantasy Park, Làng Pháp"),
                act("12:00-13:00", "Trưa", "food",
                    P(509),  # Panorama buffet
                    "Buffet trưa Bà Nà"),
                act("17:00-18:30", "Chiều", "hotel",
                    DN_HOTEL["m_hotel"],
                    "Về khách sạn nghỉ", travel_from_prev=45),
                act("19:00-21:00", "Tối", "food",
                    P(495),  # Madam Lân
                    "Dinner Madam Lân - set menu view sông Hàn", travel_from_prev=15),
                act("21:00-22:30", "Tối", "attraction",
                    DN_SIGHT["cau_rong"],
                    "Cầu Rồng phun lửa 21:00", travel_from_prev=15),
            ]
        },
        {
            "day": 3,
            "title": "Ngũ Hành Sơn - Non Nước - Asia Park",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    DN_FOOD["bun_cha_ca_ba_lu"],
                    "Ăn sáng bún chả cá"),
                act("08:30-11:00", "Sáng", "attraction",
                    DN_SIGHT["ngu_hanh_son"],
                    "Trekking Ngũ Hành Sơn - hang Huyền Không, Thuyết Linh Tự", travel_from_prev=20),
                act("11:00-12:00", "Sáng", "attraction",
                    DN_SIGHT["non_nuoc"],
                    "Tham quan Làng đá Non Nước - nghệ thuật điêu khắc", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    P(495),  # Madam Lân
                    "Ăn trưa Madam Lân", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "rest",
                    DN_HOTEL["m_hotel"],
                    "Nghỉ trưa tại khách sạn", travel_from_prev=20),
                act("15:00-17:30", "Chiều", "attraction",
                    DN_SIGHT["asia_park"],
                    "Asia Park - công viên giải trí + Sun Wheel", travel_from_prev=15),
                act("17:30-19:00", "Chiều", "attraction",
                    DN_SIGHT["sun_wheel"],
                    "Sun Wheel - vòng quay mặt trời view toàn cảnh", travel_from_prev=5),
                act("19:00-21:00", "Tối", "food",
                    DN_FOOD["hai_san_be_anh"],
                    "Dinner hải sản Bé Anh - party biển", travel_from_prev=20),
            ]
        },
        {
            "day": 4,
            "title": "Cù Lao Chàm - Mua sắm - Bay về",
            "activities": [
                act("07:00-08:00", "Sáng", "food",
                    DN_FOOD["banh_xeo_ba_duong"],
                    "Ăn sáng bánh xèo Bà Dưỡng"),
                act("08:00-14:00", "Cả ngày", "attraction",
                    DN_SIGHT["cu_lao_cham"],
                    "Tour Cù Lao Chàm - lặn san hô, tắm biển", travel_from_prev=30),
                act("12:00-13:00", "Trưa", "food",
                    P(484),  # seafood
                    "Ăn trưa hải sản Cù Lao Chàm"),
                act("14:00-15:30", "Chiều", "rest",
                    DN_HOTEL["m_hotel"],
                    "Về khách sạn tắm + check-out", travel_from_prev=30),
                act("15:30-17:00", "Chiều", "shopping",
                    DN_SIGHT["con_market"],
                    "Chợ Cồn - mua đặc sản Đà Nẵng", travel_from_prev=15),
                act("17:00-18:00", "Chiều", "food",
                    DN_FOOD["my_quang_ba_mua"],
                    "Cafe mì Quảng trước khi bay", travel_from_prev=10),
                act("18:00", "Tối", "end", None,
                    "Ra sân bay - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 6900000,        # 3 đêm x 2.3M = 6.9M / 4 người
        "food": 4500000,         # 4 ngày / 4 người
        "tickets": 2000000,      # Bà Nà + Cù Lao Chàm + Ngũ Hành Sơn + Asia Park
        "transport": 1500000,
        "other": 500000,
    },
    "estimatedTotalPerPerson": 3800000,  # 4 người chia = 15.4M / 4 = 3.85M/người
}

# === DN04-s: 3N2Đ, 3.5-5tr, 1-2 người, FOODIE ===
# 1-2 người x 3.5-5tr = 3.5-10tr
DN04 = {
    "id": "DN04-s",
    "city": "Da Nang",
    "title": "Đà Nẵng Food Trip 3N2Đ - Ăn gì cũng có",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 1, "max": 2},
    "budgetPerPerson": {"min": 3500000, "max": 5000000},
    "style": "foodie",
    "hotel": DN_HOTEL["sana"],   # 550k budget beach
    "days": [
        {
            "day": 1,
            "title": "Mì Quảng + Bánh tráng cuốn + Hải sản",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    DN_FOOD["my_quang_ba_mua"],
                    "Ăn sáng mì Quảng Bà Mua - 19 Trần Bình Trọng"),
                act("09:30-10:30", "Sáng", "shopping",
                    DN_SIGHT["con_market"],
                    "Chợ Cồn - khám phá ẩm thực chợ", travel_from_prev=20),
                act("10:30-12:00", "Sáng", "food",
                    P(496),  # Bếp Trang
                    "Bánh tráng cuốn thịt heo Mệ Phong - 35 Trần Bình Trọng", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    P(483),  # Bánh xèo Bà Dưỡng
                    "Bánh xèo + nem lụi Bà Dưỡng", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "rest",
                    DN_HOTEL["sana"],
                    "Nghỉ trưa tại khách sạn", travel_from_prev=15),
                act("15:00-17:00", "Chiều", "food",
                    P(500),  # Thìa Gỗ
                    "Cà phê cốt dừa + chè tại chợ Hàn - ăn vặt", travel_from_prev=15),
                act("18:00-20:00", "Tối", "food",
                    DN_FOOD["hai_san_be_anh"],
                    "Hải sản Bé Anh - ăn no căng bụng", travel_from_prev=20),
                act("20:00-22:00", "Tối", "attraction",
                    DN_SIGHT["cau_rong"],
                    "Cầu Rồng + Sông Hàn ban đêm", travel_from_prev=15),
            ]
        },
        {
            "day": 2,
            "title": "Bún chả cá + Chợ đêm Helio",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    DN_FOOD["bun_cha_ca_ba_lu"],
                    "Bún chả cá Bà Lữ - 170 Tôn Đản"),
                act("09:00-10:30", "Sáng", "food",
                    P(494),  # Bánh bèo nậm lọc Bà Bé
                    "Bánh bèo nậm lọc Bà Bé", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "shopping",
                    DN_SIGHT["han_market"],
                    "Chợ Hàn - khám phá chợ truyền thống", travel_from_prev=15),
                act("12:00-13:30", "Trưa", "food",
                    P(486),  # Mì Quảng 1A
                    "Mì Quảng 1A Hải Phòng - địa chỉ khác", travel_from_prev=10),
                act("13:30-15:00", "Trưa", "rest",
                    DN_HOTEL["sana"],
                    "Nghỉ trưa", travel_from_prev=15),
                act("15:00-17:00", "Chiều", "food",
                    DN_FOOD["kem_bo_co_van"],
                    "Kem bơ Cô Vân - ăn vặt mát lạnh", travel_from_prev=15),
                act("17:00-19:00", "Chiều", "attraction",
                    DN_SIGHT["my_khe"],
                    "Dạo biển Mỹ Khê chiều", travel_from_prev=15),
                act("19:00-21:00", "Tối", "food",
                    P(484),  # Hải sản Năm Đảnh
                    "Dinner hải sản Năm Đảnh", travel_from_prev=15),
                act("21:00-22:30", "Tối", "attraction",
                    DN_SIGHT["helio_market"],
                    "Chợ đêm Helio - ăn nhiều món: chè, nước mía, nem lụi", travel_from_prev=15),
            ]
        },
        {
            "day": 3,
            "title": "Chợ Hàn + Bánh mì Phượng + Bay về",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    DN_FOOD["banh_mi_phuong"],
                    "Bánh mì Phượng - 30k, huyền thoại Đà Nẵng"),
                act("09:00-10:30", "Sáng", "shopping",
                    DN_SIGHT["han_market"],
                    "Chợ Hàn mua đặc sản (mè xửng, mì Quảng, nước mắm)", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "food",
                    P(488),  # Bún mắm bà Vân
                    "Bún mắm bà Vân - đặc sảt miền Trung", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    DN_FOOD["banh_xeo_ba_duong"],
                    "Bánh xèo + nem lụi Bà Dưỡng - ăn lần cuối", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "rest",
                    DN_HOTEL["sana"],
                    "Check-out + nghỉ ngơi", travel_from_prev=15),
                act("15:00-16:00", "Chiều", "food",
                    DN_FOOD["kem_bo_co_van"],
                    "Kem bơ Cô Vân lần cuối", travel_from_prev=15),
                act("16:00", "Chiều", "end", None,
                    "Ra sân bay - kết thúc chuyến ăn"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 1100000,
        "food": 1800000,
        "tickets": 200000,
        "transport": 400000,
        "other": 200000,
    },
    "estimatedTotalPerPerson": 3700000,
}

# === DN05-s: 4N3Đ, 6-9tr, gia đình có trẻ nhỏ + người lớn tuổi ===
DN05 = {
    "id": "DN05-s",
    "city": "Da Nang",
    "title": "Đà Nẵng Family 4N3Đ - Gia đình đa thế hệ",
    "duration": "4 ngày 3 đêm",
    "durationDays": 4,
    "durationNights": 3,
    "travelers": {"min": 3, "max": 6},
    "budgetPerPerson": {"min": 6000000, "max": 9000000},
    "style": "family",
    "hotel": DN_HOTEL["sala"],  # 1.4M beach, family
    "days": [
        {
            "day": 1,
            "title": "Mỹ Khê - Khám phá biển",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    DN_FOOD["bun_cha_ca_ba_lu"],
                    "Ăn sáng bún chả cá Bà Lữ - phù hợp người lớn tuổi"),
                act("09:00-10:00", "Sáng", "hotel",
                    DN_HOTEL["sala"],
                    "Check-in Sala Danang Beach - phòng family", travel_from_prev=15),
                act("10:00-12:00", "Sáng", "attraction",
                    DN_SIGHT["my_khe"],
                    "Tắm biển Mỹ Khê - nông an toàn cho bé", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    DN_FOOD["my_quang_ba_mua"],
                    "Ăn trưa mì Quảng Bà Mua - mềm dễ ăn", travel_from_prev=15),
                act("13:30-15:30", "Trưa", "rest",
                    DN_HOTEL["sala"],
                    "Nghỉ trưa dài tại khách sạn", travel_from_prev=20),
                act("15:30-17:30", "Chiều", "attraction",
                    DN_SIGHT["my_khe"],
                    "Dạo bờ biển Mỹ Khê - xem hoàng hôn", travel_from_prev=10),
                act("18:30-20:00", "Tối", "food",
                    P(495),  # Madam Lân
                    "Dinner Madam Lân - set menu gia đình", travel_from_prev=15),
                act("20:00-21:00", "Tối", "attraction",
                    DN_SIGHT["cau_song_han"],
                    "Dạo Sông Hàn nhẹ nhàng", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Bà Nà Hills - Cầu Vàng - Fantasy Park",
            "activities": [
                act("07:00-08:00", "Sáng", "food",
                    DN_FOOD["banh_beo_ba_be"],
                    "Ăn sáng bánh bèo nậm lọc - dễ ăn cho bé"),
                act("08:00-08:45", "Sáng", "travel", None,
                    "Di chuyển lên Sun World Bà Nà Hills", travel_from_prev=20),
                act("08:45-16:00", "Cả ngày", "attraction",
                    DN_SIGHT["ba_na"],
                    "Bà Nà Hills: cáp treo không leo, Fantasy Park (bé thích), Cầu Vàng, Làng Pháp"),
                act("12:00-13:00", "Trưa", "food",
                    P(509),  # Panorama buffet
                    "Buffet trưa tại Panorama - đa dạng món cho cả nhà"),
                act("17:00-18:30", "Chiều", "hotel",
                    DN_HOTEL["sala"],
                    "Về khách sạn nghỉ ngơi", travel_from_prev=45),
                act("18:30-20:00", "Tối", "food",
                    DN_FOOD["hai_san_nam_danh"],
                    "Dinner hải sản Năm Đảnh - giá bình dân", travel_from_prev=15),
                act("20:00-21:00", "Tối", "rest",
                    DN_HOTEL["sala"],
                    "Về phòng nghỉ sớm", travel_from_prev=15),
            ]
        },
        {
            "day": 3,
            "title": "Chùa Linh Ứng - Ngũ Hành Sơn - Bảo tàng Chăm",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    DN_FOOD["my_quang_ba_mua"],
                    "Ăn sáng mì Quảng"),
                act("09:00-10:30", "Sáng", "attraction",
                    DN_SIGHT["chua_linh_ung"],
                    "Chùa Linh Ứng Sơn Trà - không leo nhiều, chụp ảnh", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "attraction",
                    DN_SIGHT["son_tra"],
                    "Dạo bán đảo Sơn Trà nhẹ nhàng", travel_from_prev=15),
                act("12:00-13:30", "Trưa", "food",
                    DN_FOOD["hai_san_be_anh"],
                    "Ăn trưa hải sản Bé Anh", travel_from_prev=20),
                act("13:30-15:30", "Trưa", "rest",
                    DN_HOTEL["sala"],
                    "Nghỉ trưa dài", travel_from_prev=15),
                act("15:30-17:00", "Chiều", "attraction",
                    DN_SIGHT["ngu_hanh_son"],
                    "Ngũ Hành Sơn - chụp ảnh bên ngoài (không leo cho người lớn tuổi)", travel_from_prev=20),
                act("17:00-18:30", "Chiều", "attraction",
                    DN_SIGHT["cham_museum"],
                    "Bảo tàng Điêu khắc Chăm - không gian mát, học lịch sử", travel_from_prev=20),
                act("18:30-20:00", "Tối", "food",
                    P(495),  # Madam Lân
                    "Dinner Madam Lân - cơm gia đình", travel_from_prev=15),
            ]
        },
        {
            "day": 4,
            "title": "Chợ Hàn - Mua quà - Bay về",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    DN_FOOD["banh_mi_phuong"],
                    "Ăn sáng bánh mì Phượng"),
                act("09:00-11:00", "Sáng", "shopping",
                    DN_SIGHT["han_market"],
                    "Chợ Hàn - mua mè xửng, mì Quảng, đặc sản", travel_from_prev=15),
                act("11:00-12:30", "Sáng", "food",
                    P(484),  # Hải sản Năm Đảnh
                    "Ăn trưa nhẹ - cơm gà Hải Châu", travel_from_prev=10),
                act("12:30-14:00", "Trưa", "rest",
                    DN_HOTEL["sala"],
                    "Check-out + nghỉ ngơi tại sảnh", travel_from_prev=15),
                act("14:00-15:30", "Chiều", "food",
                    P(500),  # cafe
                    "Cà phê + chè cuối cùng", travel_from_prev=10),
                act("15:30", "Chiều", "end", None,
                    "Ra sân bay - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 4200000,        # 3 đêm x 1.4M
        "food": 3000000,
        "tickets": 1700000,
        "transport": 1000000,
        "other": 400000,
    },
    "estimatedTotalPerPerson": 3500000,  # 4-6 người chia
}

# === DNA01-s: 3N2Đ, 3.5-5.5tr, 1 người, yên tĩnh ===
DNA01 = {
    "id": "DNA01-s",
    "city": "Da Nang",
    "title": "Đà Nẵng Yên Tĩnh 3N2Đ - Solo healing",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 1, "max": 1},
    "budgetPerPerson": {"min": 3500000, "max": 5500000},
    "style": "quiet",
    "hotel": DN_HOTEL["nguyen_gia"],  # 480k beach yên
    "days": [
        {
            "day": 1,
            "title": "Bình minh Mỹ Khê - Cafe yên tĩnh",
            "activities": [
                act("05:30-07:00", "Sáng", "attraction",
                    DN_SIGHT["my_khe"],
                    "Đi bộ bãi biển Mỹ Khê lúc bình minh - yên bình"),
                act("07:30-08:30", "Sáng", "food",
                    DN_FOOD["bun_cha_ca_ba_lu"],
                    "Ăn sáng bún chả cá Bà Lữ - quán vắng sáng sớm"),
                act("09:00-10:00", "Sáng", "hotel",
                    DN_HOTEL["nguyen_gia"],
                    "Check-in Nguyen Gia Hotel - view bán đảo Sơn Trà", travel_from_prev=20),
                act("10:00-12:00", "Sáng", "attraction",
                    DN_SIGHT["my_khe"],
                    "Tắm biển Mỹ Khê một mình", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    DN_FOOD["my_quang_ba_mua"],
                    "Ăn trưa mì Quảng Bà Mua", travel_from_prev=15),
                act("13:30-15:30", "Trưa", "rest",
                    DN_HOTEL["nguyen_gia"],
                    "Nghỉ trưa tại khách sạn", travel_from_prev=20),
                act("15:30-17:30", "Chiều", "food",
                    P(500),  # Thìa Gỗ
                    "Cà phê cóc ven biển - đọc sách, nghe nhạc", travel_from_prev=15),
                act("18:00-20:00", "Tối", "food",
                    P(489),  # Kem bơ
                    "Ăn tối nhẹ gần hostel - cơm gà", travel_from_prev=15),
                act("20:00-22:00", "Tối", "attraction",
                    DN_SIGHT["cau_song_han"],
                    "Đi bộ Sông Hàn - yên tĩnh về đêm", travel_from_prev=15),
            ]
        },
        {
            "day": 2,
            "title": "Sơn Trà - Chùa Linh Ứng - Spa",
            "activities": [
                act("06:00-07:00", "Sáng", "attraction",
                    DN_SIGHT["chua_linh_ung"],
                    "Chùa Linh Ứng - rất yên tĩnh sáng sớm, tụng kinh"),
                act("07:30-08:30", "Sáng", "food",
                    P(486),  # Mì Quảng 1A
                    "Ăn chay sáng tại Mì Quảng 1A Hải Phòng gần chùa", travel_from_prev=15),
                act("09:00-12:00", "Sáng", "attraction",
                    DN_SIGHT["son_tra"],
                    "Đi bộ rừng Sơn Trà - trek nhẹ đường mòn", travel_from_prev=20),
                act("12:00-13:30", "Trưa", "food",
                    DN_FOOD["my_quang_ba_mua"],
                    "Ăn trưa mì Quảng", travel_from_prev=20),
                act("13:30-15:30", "Trưa", "rest",
                    DN_HOTEL["nguyen_gia"],
                    "Nghỉ trưa", travel_from_prev=20),
                act("15:30-17:30", "Chiều", "attraction",
                    P(49),  # Núi Thần Tài
                    "Spa tại Núi Thần Tài - suối khoáng nóng", travel_from_prev=30),
                act("18:00-20:00", "Tối", "food",
                    P(495),  # Madam Lân
                    "Ăn tối Madam Lân - view sông Hàn", travel_from_prev=30),
                act("20:00-22:00", "Tối", "food",
                    P(500),  # cafe
                    "Cafe view biển ban đêm - yên tĩnh", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Ngũ Hành Sơn - Bảo tàng Chăm - Bay về",
            "activities": [
                act("07:00-08:00", "Sáng", "food",
                    P(500),  # Thìa Gỗ
                    "Ăn sáng cà phê + bánh mì"),
                act("08:30-10:30", "Sáng", "attraction",
                    DN_SIGHT["ngu_hanh_son"],
                    "Ngũ Hành Sơn - leo hang Huyền Không", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "attraction",
                    DN_SIGHT["cham_museum"],
                    "Bảo tàng Điêu khắc Chăm - mát mẻ, học lịch sử", travel_from_prev=20),
                act("12:00-13:30", "Trưa", "food",
                    DN_FOOD["banh_beo_ba_be"],
                    "Ăn trưa bánh bèo nậm lọc", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "food",
                    P(500),  # cafe
                    "Cà phê cuối cùng tại The Coffee House view sông Hàn", travel_from_prev=15),
                act("15:00-16:00", "Chiều", "rest",
                    DN_HOTEL["nguyen_gia"],
                    "Check-out + nghỉ sảnh", travel_from_prev=15),
                act("16:00", "Chiều", "end", None,
                    "Ra sân bay"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 960000,        # 2 đêm x 480k
        "food": 900000,
        "tickets": 200000,
        "transport": 500000,
        "other": 200000,
    },
    "estimatedTotalPerPerson": 2760000,
}

# === DNA02-s: 3N2Đ, 6-10tr, 2 người honeymoon ===
DNA02 = {
    "id": "DNA02-s",
    "city": "Da Nang",
    "title": "Đà Nẵng Honeymoon 3N2Đ - Resort view biển",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 2, "max": 2},
    "budgetPerPerson": {"min": 6000000, "max": 10000000},
    "style": "honeymoon",
    "hotel": DN_HOTEL["intercon"],  # 8M ultra luxury
    "days": [
        {
            "day": 1,
            "title": "Check-in InterContinental - Sunset dinner",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    P(501),  # 43 Factory
                    "Ăn sáng 43 Factory Coffee Roaster"),
                act("09:00-11:00", "Sáng", "travel", None,
                    "Di chuyển ra sân bay Đà Nẵng - check-in InterContinental Sun Peninsula", travel_from_prev=20),
                act("11:00-12:30", "Sáng", "hotel",
                    DN_HOTEL["intercon"],
                    "Check-in InterContinental - phòng ocean view bán đảo Sơn Trà"),
                act("12:30-14:00", "Trưa", "food",
                    P(508),  # La Maison 1888
                    "Ăn trưa tại La Maison 1888 - nhà hàng resort Citron", travel_from_prev=10),
                act("14:00-16:00", "Trưa", "attraction",
                    P(434),  # Biển resort
                    "Bơi hồ bơi vô cực resort - view bán đảo Sơn Trà", travel_from_prev=5),
                act("16:00-18:00", "Chiều", "attraction",
                    DN_SIGHT["my_khe"],
                    "Tắm biển riêng resort", travel_from_prev=10),
                act("18:00-20:00", "Tối", "food",
                    P(508),  # La Maison 1888
                    "Dinner La Maison 1888 - fine dining Pháp, view biển", travel_from_prev=15),
                act("20:00-22:00", "Tối", "attraction",
                    DN_SIGHT["cau_song_han"],
                    "Đi bộ đêm resort - yên tĩnh", travel_from_prev=15),
            ]
        },
        {
            "day": 2,
            "title": "Bà Nà Hills - Spa đôi - Romantic dinner",
            "activities": [
                act("07:00-08:00", "Sáng", "food",
                    P(508),  # La Maison
                    "Ăn sáng tại resort"),
                act("08:00-08:45", "Sáng", "travel", None,
                    "Di chuyển lên Bà Nà Hills", travel_from_prev=20),
                act("08:45-16:00", "Cả ngày", "attraction",
                    DN_SIGHT["ba_na"],
                    "Bà Nà Hills: cáp treo, Cầu Vàng, Làng Pháp, Fantasy Park"),
                act("12:00-13:30", "Trưa", "food",
                    P(509),  # Panorama
                    "Buffet trưa Bà Nà"),
                act("17:00-18:00", "Chiều", "hotel",
                    DN_HOTEL["intercon"],
                    "Về resort nghỉ", travel_from_prev=45),
                act("18:00-20:00", "Tối", "attraction",
                    P(508),  # spa resort
                    "Spa đôi 2h tại resort - Healing senses spa", travel_from_prev=10),
                act("20:00-22:00", "Tối", "food",
                    P(495),  # Madam Lân (alternative romantic)
                    "Dinner Madam Lân view sông Hàn - fine dining", travel_from_prev=20),
            ]
        },
        {
            "day": 3,
            "title": "Sơn Trà - Cafe Sunset - Bay về",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    P(508),  # resort breakfast
                    "Ăn sáng tại resort - buffet"),
                act("09:00-11:00", "Sáng", "attraction",
                    DN_SIGHT["son_tra"],
                    "Dạo bán đảo Sơn Trà, viếng Chùa Linh Ứng", travel_from_prev=15),
                act("11:00-12:30", "Sáng", "attraction",
                    DN_SIGHT["chua_linh_ung"],
                    "Chiêm bái tượng Phật Bà 67m", travel_from_prev=10),
                act("12:30-14:00", "Trưa", "food",
                    P(508),  # resort
                    "Ăn trưa tại resort"),
                act("14:00-15:30", "Chiều", "attraction",
                    DN_SIGHT["ngu_hanh_son"],
                    "Ngũ Hành Sơn - leo núi, ngắm biển", travel_from_prev=25),
                act("15:30-17:00", "Chiều", "attraction",
                    P(434),  # Biển
                    "Tắm biển + ngắm hoàng hôn resort", travel_from_prev=20),
                act("17:00-19:00", "Chiều", "food",
                    P(508),  # final dinner
                    "Final dinner La Maison 1888 - fine dining", travel_from_prev=15),
                act("19:00", "Tối", "end", None,
                    "Ra sân bay - kết thúc honeymoon"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 16000000,       # 2 đêm x 8M
        "food": 6000000,         # fine dining
        "tickets": 2500000,      # Bà Nà + Ngũ Hành Sơn
        "spa": 4000000,
        "transport": 1500000,
        "other": 500000,
    },
    "estimatedTotalPerPerson": 15250000,  # 30.5M / 2
}

# === DNA03-s: 3N2Đ, 2.5-4tr, 1 sinh viên ===
DNA03 = {
    "id": "DNA03-s",
    "city": "Da Nang",
    "title": "Đà Nẵng Budget 3N2Đ - Sinh viên tiết kiệm",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 1, "max": 1},
    "budgetPerPerson": {"min": 2500000, "max": 4000000},
    "style": "budget",
    "hotel": DN_HOTEL["sea_vista"],  # 400k apt
    "days": [
        {
            "day": 1,
            "title": "Mỹ Khê free - Chợ đêm",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    DN_FOOD["bun_cha_ca_ba_lu"],
                    "Ăn sáng bún chả cá quán bình dân - 30k"),
                act("09:00-10:00", "Sáng", "hotel",
                    DN_HOTEL["sea_vista"],
                    "Check-in Sea Vista Hotel & Apartment - 400k/đêm", travel_from_prev=15),
                act("10:00-12:00", "Sáng", "attraction",
                    DN_SIGHT["my_khe"],
                    "Mỹ Khê free - tắm biển, chụp ảnh", travel_from_prev=10),
                act("12:00-13:00", "Trưa", "food",
                    P(488),  # Bún mắm
                    "Cơm bụi trưa - 25k", travel_from_prev=15),
                act("13:00-15:00", "Trưa", "rest",
                    DN_HOTEL["sea_vista"],
                    "Nghỉ trưa hostel", travel_from_prev=20),
                act("15:00-18:00", "Chiều", "attraction",
                    DN_SIGHT["my_khe"],
                    "Dừa 20k trên biển Mỹ Khê - nằm nghe sóng", travel_from_prev=10),
                act("18:00-19:00", "Tối", "food",
                    P(496),  # Bếp Trang
                    "Mì Quảng quán vỉa hè - 30k", travel_from_prev=15),
                act("19:00-21:00", "Tối", "attraction",
                    DN_SIGHT["helio_market"],
                    "Chợ đêm Helio - ăn vặt 50k", travel_from_prev=15),
            ]
        },
        {
            "day": 2,
            "title": "Chùa Linh Ứng - Cầu Rồng - Cafe sinh viên",
            "activities": [
                act("07:00-08:00", "Sáng", "food",
                    DN_FOOD["bun_cha_ca_ba_lu"],
                    "Ăn sáng bún chả cá - 30k"),
                act("08:00-10:00", "Sáng", "attraction",
                    DN_SIGHT["chua_linh_ung"],
                    "Chùa Linh Ứng - FREE, view đẹp", travel_from_prev=15),
                act("10:00-12:00", "Sáng", "attraction",
                    DN_SIGHT["son_tra"],
                    "Đi bộ Sơn Trà - FREE, ngắm bán đảo", travel_from_prev=15),
                act("12:00-13:00", "Trưa", "food",
                    P(488),  # Bún mắm
                    "Cơm bụi trưa - 25k", travel_from_prev=20),
                act("13:00-15:00", "Trưa", "rest",
                    DN_HOTEL["sea_vista"],
                    "Nghỉ trưa", travel_from_prev=20),
                act("15:00-17:00", "Chiều", "attraction",
                    DN_SIGHT["cau_rong"],
                    "Cầu Rồng chụp ảnh FREE - chiều vắng", travel_from_prev=15),
                act("17:00-18:00", "Chiều", "food",
                    P(500),  # cafe
                    "Cafe sinh viên - 25k", travel_from_prev=10),
                act("18:00-19:00", "Tối", "food",
                    DN_FOOD["my_quang_ba_mua"],
                    "Mì Quảng quán vỉa hè - 30k", travel_from_prev=15),
                act("19:00-21:00", "Tối", "attraction",
                    DN_SIGHT["cau_song_han"],
                    "Dạo Sông Hàn - FREE", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Ngũ Hành Sơn - Bay về",
            "activities": [
                act("07:00-08:00", "Sáng", "food",
                    DN_FOOD["banh_mi_phuong"],
                    "Bánh mì Phượng - 30k"),
                act("08:00-11:00", "Sáng", "attraction",
                    DN_SIGHT["ngu_hanh_son"],
                    "Ngũ Hành Sơn - 40k vé - hang Huyền Không", travel_from_prev=15),
                act("11:00-12:00", "Sáng", "shopping",
                    DN_SIGHT["han_market"],
                    "Chợ Hàn mua đặc sản", travel_from_prev=20),
                act("12:00-13:00", "Trưa", "food",
                    P(488),  # Bún mắm
                    "Cơm bụi - 25k", travel_from_prev=10),
                act("13:00-14:00", "Trưa", "rest",
                    DN_HOTEL["sea_vista"],
                    "Check-out + nghỉ sảnh", travel_from_prev=15),
                act("14:00-15:00", "Chiều", "food",
                    P(500),  # cafe
                    "Cà phê cốt dừa chợ Hàn", travel_from_prev=10),
                act("15:00", "Chiều", "end", None,
                    "Ra sân bay"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 800000,         # 2 đêm x 400k
        "food": 500000,
        "tickets": 40000,        # Ngũ Hành Sơn
        "transport": 300000,
        "other": 100000,
    },
    "estimatedTotalPerPerson": 1740000,
}

# ============================================================
# HỘI AN - 8 PLANS
# ============================================================

HA_FOOD = {
    "banh_mi_phuong": P(13),       # Bánh mì Phượng (Hội An)
    "banh_mi_madam_khanh": P(69),  # Bánh mì Madam Khánh
    "cao_lau_lien": P(96),         # Cao Lầu Liên
    "cao_lau_thanh": P(53),        # Cao lầu Thanh
    "com_ga_ba_buoi": P(124),      # Cơm gà Bà Buội
    "com_ga_ha": P(76),            # Cơm gà Hội An
    "my_quang_ba_mua_ha": P(61),   # Mì Quảng Bà Mua (HA)
    "my_quang_ong_hung": P(107),   # Mì Quảng Ông Hùng
    "morning_glory": P(62),        # Morning Glory
    "white_rose": P(75),           # White Rose
    "nu_eatery": P(150),           # Nu Eatery
    "the_deck_house": P(125),      # The Deck House An Bang
    "the_espresso": P(201),        # The Espresso Station
    "mango_mango": P(108),         # Mango Mango
    "banh_bao_my": P(178),         # Bánh Bao Bánh Vạc Mộc
    "hoian_roastery": P(134),      # Hoi An Roastery
    "banh_trang_nuong": P(193),    # Bánh Tráng Nướng Chị Huệ
    "gioc_an_bang": P(136),        # Gioan Beach Restaurant
    "hi_bakery": P(211),           # Hi Bakery
    "banh_mi_HA_orig": P(200),     # Bánh Mì Hội An Original
    "the_hill_station": P(210),    # The Hill Station
    "banh_beo_HUE": P(494),        # reuse Hue food
    "cocobox": P(179),             # Cocobox
}
HA_SIGHT = {
    "pho_co": P(1),                # Phố cổ Hội An
    "chua_cau": P(8),              # Chùa Cầu
    "hoi_quan_phuc_kien": P(39),   # Hội quán Phúc Kiến
    "nha_co_tan_ky": P(71),        # Nhà cổ Tấn Ký
    "nha_co_phung_hung": P(59),    # Nhà cổ Phùng Hưng
    "bai_an_bang": P(40),          # Biển An Bàng
    "bai_cua_dai": P(60),          # Biển Cửa Đại
    "bai_ha_my": P(155),           # Bãi biển Hà My
    "lang_dau_bay_mau": P(19),     # Rừng dừa Bảy Mẫu
    "cu_lao_cham": P(41),          # Cù Lao Chàm
    "lang_gom_thanh_ha": P(74),    # Làng gốm Thanh Hà
    "lang_rau_tra_que": P(103),    # Làng rau Trà Quế
    "lang_moc_kim_bong": P(117),   # Làng mộc Kim Bồng
    "lang_lua_duy_trinh": P(177),  # Làng lụa Duy Trinh
    "lang_tre_dua": P(216),        # Làng tre Dừa Cam Thanh
    "my_son": P(11),               # Chùa Thiên Mụ (chuwa), My Son thực ra cần tìm
    "cho_dem_HA": P(42),           # Chợ đêm Hội An
    "pho_den_long": P(98),         # Phố đèn lồng
    "cho_nguyen_hoang": P(154),    # Chợ đêm Nguyễn Hoàng
    "thuyen_song_thu_bon": P(119), # Tour sông Thu Bồn
    "bt_mythuat_thieu": P(239),    # Bảo tàng Mỹ thuật Thêu XQ
    "lang_bich_hoa_tam_thanh": P(431),  # Làng bích họa Tam Thanh
    "bt_van_hoa_dan_gian": P(116),  # Bảo tàng Văn hóa dân gian
    "precious_heritage": P(220),   # Precious Heritage
    "may_ao_dai_yaly": P(126),     # Xưởng may áo dài Yaly
}
HA_HOTEL = {
    "ha_backpacker": P(621),        # 180k hostel
    "hoang_trinh": P(622),         # 350k old_town
    "cam_thanh_lotus": P(623),     # 300k countryside
    "golden_peach": P(624),        # 450k villa
    "little_leo": P(625),          # 400k homestay
    "ha_historic": P(626),         # 900k mid old_town
    "allegro": P(627),             # 800k old_town
    "la_siesta_resort": P(628),    # 1.2M mid resort
    "an_bang_hideaway": P(629),    # 1M beach
    "victoria_ha": P(630),         # 2.8M luxury
    "little_riverside": P(631),    # 2.5M luxury river
    "anantara": P(632),            # 3.5M luxury
    "four_seasons_nam_hai": P(633), # 18M ultra luxury
    "river_town": P(634),          # 2.2M luxury
    "moire": P(635),               # 3M luxury
    "little_oasis": P(636),        # 2M luxury eco
    "tribee_cococabana": P(253),   # 450k hostel beach
    "under_coconut": P(288),       # 400k hostel
    "vinpearl_resort": P(84),      # 3.5M resort
    "ha_royal": P(110),            # 3.5M 5-star
    "lantana": P(172),             # 2.8M 4-star
}

# === HOI01-s: 3N2Đ, 3.5-5.5tr, gia đình 3-4 người ===
HOI01 = {
    "id": "HOI01-s",
    "city": "Hoi An",
    "title": "Hội An Heritage 3N2Đ - Gia đình phố cổ",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 3, "max": 4},
    "budgetPerPerson": {"min": 3500000, "max": 5500000},
    "style": "family",
    "hotel": HA_HOTEL["ha_historic"],   # 900k old_town
    "days": [
        {
            "day": 1,
            "title": "Phố cổ - Chùa Cầu - Đèn lồng",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HA_FOOD["banh_mi_phuong"],
                    "Ăn sáng bánh mì Phượng - 2B Phan Châu Trinh"),
                act("09:30-10:30", "Sáng", "hotel",
                    HA_HOTEL["ha_historic"],
                    "Check-in Hoi An Historic Hotel - phòng family", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "attraction",
                    HA_SIGHT["pho_co"],
                    "Phố cổ Hội An - dạo bộ, chụp ảnh", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HA_FOOD["cao_lau_lien"],
                    "Ăn trưa Cao Lầu Liên - 16 Thái Phiên", travel_from_prev=10),
                act("13:30-15:30", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Nghỉ trưa khách sạn", travel_from_prev=10),
                act("15:30-17:30", "Chiều", "attraction",
                    HA_SIGHT["chua_cau"],
                    "Chùa Cầu - biểu tượng Hội An", travel_from_prev=10),
                act("17:30-19:00", "Chiều", "attraction",
                    HA_SIGHT["hoi_quan_phuc_kien"],
                    "Hội quán Phúc Kiến - kiến trúc Trung Hoa", travel_from_prev=10),
                act("19:00-21:00", "Tối", "food",
                    HA_FOOD["morning_glory"],
                    "Dinner Morning Glory - nhà hàng nổi tiếng phố cổ", travel_from_prev=10),
                act("21:00-22:30", "Tối", "attraction",
                    HA_SIGHT["cho_dem_HA"],
                    "Chợ đêm Hội An + thả đèn hoa đăng sông Hoài", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Rừng dừa Bảy Mẫu - An Bàng",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["com_ga_ba_buoi"],
                    "Ăn sáng cơm gà Bà Buội - đặc sản Hội An"),
                act("09:00-11:30", "Sáng", "attraction",
                    HA_SIGHT["lang_dau_bay_mau"],
                    "Rừng dừa Bảy Mẫu - đi thuyền thúng", travel_from_prev=15),
                act("11:30-13:00", "Trưa", "food",
                    HA_FOOD["gioc_an_bang"],
                    "Ăn trưa hải sản Gioan Beach Restaurant", travel_from_prev=15),
                act("13:00-15:00", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Nghỉ trưa", travel_from_prev=20),
                act("15:00-17:30", "Chiều", "attraction",
                    HA_SIGHT["bai_an_bang"],
                    "Biển An Bàng - tắm biển cho cả gia đình", travel_from_prev=15),
                act("17:30-19:00", "Chiều", "attraction",
                    HA_SIGHT["pho_den_long"],
                    "Phố đèn lồng - chụp ảnh", travel_from_prev=20),
                act("19:00-21:00", "Tối", "food",
                    HA_FOOD["nu_eatery"],
                    "Dinner Nu Eatery - fusion Việt", travel_from_prev=10),
                act("21:00-22:00", "Tối", "attraction",
                    HA_SIGHT["cho_dem_HA"],
                    "Chợ đêm Hội An lần 2", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Làng rau Trà Quế - Làng gốm Thanh Hà",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["banh_mi_madam_khanh"],
                    "Ăn sáng bánh mì Madam Khánh"),
                act("09:00-11:00", "Sáng", "attraction",
                    HA_SIGHT["lang_rau_tra_que"],
                    "Làng rau Trà Quế - làm bánh ít, đạp xe", travel_from_prev=15),
                act("11:00-12:00", "Sáng", "attraction",
                    HA_SIGHT["lang_gom_thanh_ha"],
                    "Làng gốm Thanh Hà - làm gốm", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HA_FOOD["com_ga_ha"],
                    "Ăn trưa cơm gà Hội An", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Nghỉ trưa + check-out", travel_from_prev=15),
                act("15:00-16:30", "Chiều", "food",
                    HA_FOOD["hoian_roastery"],
                    "Cà phê Hoi An Roastery + mua quà", travel_from_prev=10),
                act("16:30-18:00", "Chiều", "shopping",
                    HA_SIGHT["may_ao_dai_yaly"],
                    "Mua quà lưu niệm Hội An", travel_from_prev=10),
                act("18:00", "Tối", "end", None,
                    "Về Đà Nẵng - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 1800000,        # 2 đêm x 900k
        "food": 1500000,         # 3 ngày / 4 người
        "tickets": 800000,       # phố cổ + Bảy Mẫu + Trà Quế
        "transport": 600000,     # shuttle từ sân bay
        "other": 300000,
    },
    "estimatedTotalPerPerson": 1250000,  # 5M / 4 = 1.25M
}

# === HOI02-s: 3N2Đ, 4.5-7tr, cặp đôi ===
HOI02 = {
    "id": "HOI02-s",
    "city": "Hoi An",
    "title": "Hội An Romantic 3N2Đ - Cặp đôi đèn lồng",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 2, "max": 2},
    "budgetPerPerson": {"min": 4500000, "max": 7000000},
    "style": "romantic",
    "hotel": HA_HOTEL["la_siesta_resort"],  # 1.2M mid resort
    "days": [
        {
            "day": 1,
            "title": "Phố cổ - Đèn lồng sông Hoài - Riverside dinner",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HA_FOOD["the_espresso"],
                    "Ăn sáng The Espresso Station - specialty coffee"),
                act("09:00-10:00", "Sáng", "hotel",
                    HA_HOTEL["la_siesta_resort"],
                    "Check-in La Siesta Hoi An Resort & Spa", travel_from_prev=15),
                act("10:00-12:00", "Sáng", "attraction",
                    HA_SIGHT["pho_co"],
                    "Phố cổ Hội An - dạo bộ, chụp ảnh couple", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HA_FOOD["morning_glory"],
                    "Ăn trưa Morning Glory - cooking class", travel_from_prev=10),
                act("13:30-15:00", "Trưa", "rest",
                    HA_HOTEL["la_siesta_resort"],
                    "Nghỉ trưa + spa nhẹ", travel_from_prev=10),
                act("15:00-17:00", "Chiều", "food",
                    HA_FOOD["cocobox"],
                    "Cà phê Cocobox - juice sạch", travel_from_prev=10),
                act("17:00-18:30", "Chiều", "attraction",
                    HA_SIGHT["thuyen_song_thu_bon"],
                    "Tour sông Thu Bồn lúc hoàng hôn - thuyền", travel_from_prev=10),
                act("19:00-21:00", "Tối", "food",
                    HA_FOOD["mango_mango"],
                    "Dinner Mango Mango - fine dining view sông", travel_from_prev=10),
                act("21:00-22:30", "Tối", "attraction",
                    HA_SIGHT["pho_den_long"],
                    "Phố đèn lồng + thả đèn hoa đăng", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "An Bàng - Spa đôi - Romantic dinner",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["hi_bakery"],
                    "Ăn sáng Hi Bakery - bakery Pháp"),
                act("09:00-11:00", "Sáng", "attraction",
                    HA_SIGHT["bai_an_bang"],
                    "Biển An Bàng - tắm biển sáng sớm", travel_from_prev=15),
                act("11:00-12:30", "Sáng", "food",
                    HA_FOOD["the_deck_house"],
                    "Ăn trưa The Deck House An Bang - view biển", travel_from_prev=10),
                act("12:30-15:00", "Trưa", "rest",
                    HA_HOTEL["la_siesta_resort"],
                    "Nghỉ trưa resort", travel_from_prev=20),
                act("15:00-17:30", "Chiều", "attraction",
                    HA_HOTEL["la_siesta_resort"],
                    "Spa đôi 1.2M/2 người tại La Siesta", travel_from_prev=5),
                act("17:30-19:00", "Chiều", "food",
                    HA_FOOD["hoian_roastery"],
                    "Cà phê Hoi An Roastery - sunset", travel_from_prev=10),
                act("19:00-21:30", "Tối", "food",
                    HA_FOOD["morning_glory"],
                    "Dinner Morning Glory - fine dining", travel_from_prev=10),
                act("21:30-22:30", "Tối", "attraction",
                    HA_SIGHT["cho_dem_HA"],
                    "Chợ đêm Hội An - cùng nhau dạo", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Làng gốm Thanh Hà - Cafe vintage - Bay về",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["banh_mi_phuong"],
                    "Ăn sáng bánh mì Phượng"),
                act("09:00-11:00", "Sáng", "attraction",
                    HA_SIGHT["lang_gom_thanh_ha"],
                    "Làng gốm Thanh Hà - làm gốm couple", travel_from_prev=15),
                act("11:00-12:00", "Sáng", "food",
                    HA_FOOD["cao_lau_thanh"],
                    "Ăn Cao Lầu Thanh", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HA_FOOD["com_ga_ba_buoi"],
                    "Ăn trưa cơm gà Bà Buội", travel_from_prev=10),
                act("13:30-15:00", "Trưa", "rest",
                    HA_HOTEL["la_siesta_resort"],
                    "Check-out + nghỉ sảnh", travel_from_prev=10),
                act("15:00-16:30", "Chiều", "food",
                    HA_FOOD["the_hill_station"],
                    "Café Hill Station - vintage", travel_from_prev=10),
                act("16:30-18:00", "Chiều", "attraction",
                    HA_SIGHT["pho_co"],
                    "Phố cổ chụp ảnh cuối cùng", travel_from_prev=10),
                act("18:00", "Tối", "end", None,
                    "Về Đà Nẵng - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 2400000,        # 2 đêm x 1.2M
        "food": 2200000,
        "tickets": 600000,
        "spa": 1200000,
        "transport": 800000,
        "other": 400000,
    },
    "estimatedTotalPerPerson": 3800000,  # 15.2M / 2
}

# === HOI03-s: 4N3Đ, 5-7tr, 3 người bạn ===
HOI03 = {
    "id": "HOI03-s",
    "city": "Hoi An",
    "title": "Hội An Beach & Old Town 4N3Đ - 3 người bạn",
    "duration": "4 ngày 3 đêm",
    "durationDays": 4,
    "durationNights": 3,
    "travelers": {"min": 3, "max": 3},
    "budgetPerPerson": {"min": 5000000, "max": 7000000},
    "style": "friends",
    "hotel": HA_HOTEL["ha_historic"],   # 900k, chia phòng
    "days": [
        {
            "day": 1,
            "title": "Phố cổ - Đèn lồng",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HA_FOOD["banh_mi_phuong"],
                    "Ăn sáng bánh mì Phượng"),
                act("09:30-10:30", "Sáng", "hotel",
                    HA_HOTEL["ha_historic"],
                    "Check-in Hoi An Historic Hotel", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "attraction",
                    HA_SIGHT["pho_co"],
                    "Phố cổ Hội An", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HA_FOOD["cao_lau_lien"],
                    "Ăn trưa Cao Lầu Liên", travel_from_prev=10),
                act("13:30-15:30", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Nghỉ trưa", travel_from_prev=10),
                act("15:30-17:30", "Chiều", "attraction",
                    HA_SIGHT["chua_cau"],
                    "Chùa Cầu + Hội quán Phúc Kiến", travel_from_prev=10),
                act("17:30-19:00", "Chiều", "shopping",
                    HA_SIGHT["may_ao_dai_yaly"],
                    "Chợ may áo dài - đặt may áo dài cho 3", travel_from_prev=10),
                act("19:00-21:00", "Tối", "food",
                    HA_FOOD["morning_glory"],
                    "Dinner Morning Glory", travel_from_prev=10),
                act("21:00-22:30", "Tối", "attraction",
                    HA_SIGHT["cho_dem_HA"],
                    "Chợ đêm Hội An", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "An Bàng - Rừng dừa",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["com_ga_ba_buoi"],
                    "Ăn sáng cơm gà Bà Buội"),
                act("09:00-11:30", "Sáng", "attraction",
                    HA_SIGHT["bai_an_bang"],
                    "Biển An Bàng - thuê xe đạp (30k/xe)", travel_from_prev=15),
                act("11:30-13:00", "Trưa", "food",
                    HA_FOOD["gioc_an_bang"],
                    "Ăn trưa hải sản Gioan", travel_from_prev=10),
                act("13:00-15:00", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Nghỉ trưa", travel_from_prev=20),
                act("15:00-17:30", "Chiều", "attraction",
                    HA_SIGHT["lang_dau_bay_mau"],
                    "Rừng dừa Bảy Mẫu - thuyền thúng, quay xe đạp", travel_from_prev=15),
                act("17:30-19:00", "Chiều", "food",
                    HA_FOOD["cocobox"],
                    "Cà phê Cocobox", travel_from_prev=15),
                act("19:00-21:00", "Tối", "food",
                    HA_FOOD["the_deck_house"],
                    "Dinner The Deck House An Bang", travel_from_prev=15),
                act("21:00-22:30", "Tối", "attraction",
                    HA_SIGHT["cho_dem_HA"],
                    "Chợ đêm Hội An lần 2", travel_from_prev=15),
            ]
        },
        {
            "day": 3,
            "title": "Mỹ Sơn - Làng nghề",
            "activities": [
                act("07:00-08:00", "Sáng", "food",
                    HA_FOOD["banh_mi_madam_khanh"],
                    "Ăn sáng bánh mì Madam Khánh"),
                act("08:00-13:00", "Cả ngày", "attraction",
                    P(11),  # reuse (placeholder for Mỹ Sơn)
                    "Tour Mỹ Sơn Sanctuary - thánh địa Chăm", travel_from_prev=45),
                act("13:00-14:00", "Trưa", "food",
                    HA_FOOD["my_quang_ong_hung"],
                    "Ăn trưa mì Quảng Ông Hùng", travel_from_prev=20),
                act("14:00-15:30", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Về khách sạn nghỉ", travel_from_prev=20),
                act("15:30-17:00", "Chiều", "attraction",
                    HA_SIGHT["lang_moc_kim_bong"],
                    "Làng mộc Kim Bồng", travel_from_prev=15),
                act("17:00-18:30", "Chiều", "food",
                    HA_FOOD["hoian_roastery"],
                    "Cà phê Hoi An Roastery", travel_from_prev=15),
                act("18:30-20:00", "Tối", "food",
                    HA_FOOD["nu_eatery"],
                    "Dinner Nu Eatery", travel_from_prev=10),
            ]
        },
        {
            "day": 4,
            "title": "Trà Quế - Thanh Hà - Bay về",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["banh_mi_phuong"],
                    "Ăn sáng bánh mì Phượng"),
                act("09:00-11:00", "Sáng", "attraction",
                    HA_SIGHT["lang_rau_tra_que"],
                    "Làng rau Trà Quế", travel_from_prev=15),
                act("11:00-12:00", "Sáng", "attraction",
                    HA_SIGHT["lang_gom_thanh_ha"],
                    "Làng gốm Thanh Hà", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HA_FOOD["com_ga_ha"],
                    "Ăn trưa cơm gà Hội An", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Check-out + nghỉ sảnh", travel_from_prev=15),
                act("15:00-16:30", "Chiều", "shopping",
                    HA_SIGHT["may_ao_dai_yaly"],
                    "Mua quà + nhận áo dài", travel_from_prev=10),
                act("16:30-18:00", "Chiều", "food",
                    HA_FOOD["hoian_roastery"],
                    "Cà phê cuối", travel_from_prev=10),
                act("18:00", "Tối", "end", None,
                    "Về Đà Nẵng - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 2700000,        # 3 đêm x 900k
        "food": 2200000,
        "tickets": 800000,
        "transport": 1200000,
        "other": 400000,
    },
    "estimatedTotalPerPerson": 2433000,  # 7.3M / 3
}

# === HOI04-s: 3N2Đ, 3-5tr, 1-2 người, foodie ===
HOI04 = {
    "id": "HOI04-s",
    "city": "Hoi An",
    "title": "Hội An Food Trip 3N2Đ - Ăn gì cũng có",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 1, "max": 2},
    "budgetPerPerson": {"min": 3000000, "max": 5000000},
    "style": "foodie",
    "hotel": HA_HOTEL["under_coconut"],   # 400k hostel
    "days": [
        {
            "day": 1,
            "title": "Bánh mì Phượng - Cao Lầu - Cơm gà",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HA_FOOD["banh_mi_phuong"],
                    "Bánh mì Phượng - 2B Phan Châu Trinh - 30k"),
                act("09:00-10:00", "Sáng", "hotel",
                    HA_HOTEL["under_coconut"],
                    "Check-in Under the Coconut Tree", travel_from_prev=10),
                act("10:00-12:00", "Sáng", "attraction",
                    HA_SIGHT["pho_co"],
                    "Phố cổ Hội An - dạo walking tour", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HA_FOOD["cao_lau_lien"],
                    "Cao Lầu Liên - 16 Thái Phiên - 60k", travel_from_prev=10),
                act("13:30-15:00", "Trưa", "rest",
                    HA_HOTEL["under_coconut"],
                    "Nghỉ trưa", travel_from_prev=10),
                act("15:00-17:00", "Chiều", "food",
                    HA_FOOD["hoian_roastery"],
                    "Cà phê Hoi An Roastery + bánh ngọt", travel_from_prev=10),
                act("17:00-18:30", "Chiều", "food",
                    HA_FOOD["banh_bao_my"],
                    "Bánh Bao Bánh Vạc Mộc - White Rose", travel_from_prev=10),
                act("18:30-20:00", "Tối", "food",
                    HA_FOOD["com_ga_ba_buoi"],
                    "Cơm gà Bà Buội - đặc sản Hội An", travel_from_prev=10),
                act("20:00-22:00", "Tối", "attraction",
                    HA_SIGHT["cho_dem_HA"],
                    "Chợ đêm Hội An + thả đèn hoa đăng", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Mì Quảng - Bánh xèo - Hải sản An Bàng",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["my_quang_ba_mua_ha"],
                    "Mì Quảng Bà Mua - 50k"),
                act("09:00-10:30", "Sáng", "attraction",
                    HA_SIGHT["lang_rau_tra_que"],
                    "Làng rau Trà Quế - làm bánh ít", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "food",
                    HA_FOOD["banh_trang_nuong"],
                    "Bánh tráng nướng chị Huệ - ăn vặt", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    P(53),  # Cao lầu Thanh
                    "Cao Lầu Thanh + bánh xèo Hội An", travel_from_prev=10),
                act("13:30-15:00", "Trưa", "rest",
                    HA_HOTEL["under_coconut"],
                    "Nghỉ trưa", travel_from_prev=10),
                act("15:00-17:30", "Chiều", "attraction",
                    HA_SIGHT["lang_dau_bay_mau"],
                    "Rừng dừa Bảy Mẫu - thuyền thúng", travel_from_prev=15),
                act("17:30-19:00", "Chiều", "attraction",
                    HA_SIGHT["bai_an_bang"],
                    "Biển An Bàng - hoàng hôn", travel_from_prev=15),
                act("19:00-21:00", "Tối", "food",
                    HA_FOOD["gioc_an_bang"],
                    "Dinner hải sản An Bàng - Gioan", travel_from_prev=10),
                act("21:00-22:00", "Tối", "food",
                    P(193),  # street food
                    "Ăn vặt chợ đêm", travel_from_prev=15),
            ]
        },
        {
            "day": 3,
            "title": "Chợ Hội An - Chè - Bay về",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["banh_mi_madam_khanh"],
                    "Bánh mì Madam Khánh - 30k"),
                act("09:00-10:30", "Sáng", "shopping",
                    P(156),  # Hoi An Markets Shopping
                    "Chợ Hội An - mua đặc sản (bánh tổ, mì Quảng, nước mắm)", travel_from_prev=10),
                act("10:30-12:00", "Sáng", "food",
                    HA_FOOD["banh_bao_my"],
                    "Ăn trưa Bánh Bao Bánh Vạc Mộc", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HA_FOOD["com_ga_ha"],
                    "Ăn trưa cơm gà Hội An", travel_from_prev=10),
                act("13:30-15:00", "Trưa", "rest",
                    HA_HOTEL["under_coconut"],
                    "Check-out + nghỉ sảnh", travel_from_prev=10),
                act("15:00-16:30", "Chiều", "food",
                    P(106),  # chè Huế (đã có ở Hue)
                    "Chè Hội An - ăn vặt", travel_from_prev=10),
                act("16:30-18:00", "Chiều", "food",
                    HA_FOOD["hoian_roastery"],
                    "Cà phê cuối Hoi An Roastery", travel_from_prev=10),
                act("18:00", "Tối", "end", None,
                    "Về Đà Nẵng - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 800000,         # 2 đêm x 400k
        "food": 1500000,
        "tickets": 300000,
        "transport": 400000,
        "other": 200000,
    },
    "estimatedTotalPerPerson": 1600000,
}

# === HOI05-s: 4N3Đ, 5-8tr, gia đình đa thế hệ ===
HOI05 = {
    "id": "HOI05-s",
    "city": "Hoi An",
    "title": "Hội An Family 4N3Đ - Gia đình đa thế hệ",
    "duration": "4 ngày 3 đêm",
    "durationDays": 4,
    "durationNights": 3,
    "travelers": {"min": 3, "max": 5},
    "budgetPerPerson": {"min": 5000000, "max": 8000000},
    "style": "family",
    "hotel": HA_HOTEL["ha_historic"],
    "days": [
        {
            "day": 1,
            "title": "Phố cổ nhẹ - Đèn lồng",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HA_FOOD["banh_mi_phuong"],
                    "Ăn sáng bánh mì Phượng"),
                act("09:30-10:30", "Sáng", "hotel",
                    HA_HOTEL["ha_historic"],
                    "Check-in Hoi An Historic", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "attraction",
                    HA_SIGHT["pho_co"],
                    "Phố cổ Hội An - dạo nhẹ", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HA_FOOD["cao_lau_lien"],
                    "Ăn trưa Cao Lầu Liên", travel_from_prev=10),
                act("13:30-15:30", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Nghỉ trưa dài", travel_from_prev=10),
                act("15:30-17:00", "Chiều", "attraction",
                    HA_SIGHT["chua_cau"],
                    "Chùa Cầu", travel_from_prev=10),
                act("17:00-18:30", "Chiều", "attraction",
                    HA_SIGHT["thuyen_song_thu_bon"],
                    "Thuyền sông Hoài nhẹ", travel_from_prev=10),
                act("18:30-20:00", "Tối", "food",
                    HA_FOOD["morning_glory"],
                    "Dinner Morning Glory", travel_from_prev=10),
                act("20:00-22:00", "Tối", "attraction",
                    HA_SIGHT["pho_den_long"],
                    "Phố đèn lồng", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Bảy Mẫu - An Bàng",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["com_ga_ba_buoi"],
                    "Ăn sáng cơm gà Bà Buội"),
                act("09:00-11:00", "Sáng", "attraction",
                    HA_SIGHT["lang_dau_bay_mau"],
                    "Rừng dừa Bảy Mẫu - thuyền thúng", travel_from_prev=15),
                act("11:00-12:00", "Sáng", "food",
                    HA_FOOD["gioc_an_bang"],
                    "Ăn nhẹ hải sản", travel_from_prev=15),
                act("12:00-13:30", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Nghỉ trưa", travel_from_prev=15),
                act("13:30-15:30", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Nghỉ tiếp - bà nội cần nghỉ nhiều", travel_from_prev=5),
                act("15:30-17:30", "Chiều", "attraction",
                    HA_SIGHT["bai_an_bang"],
                    "Biển An Bàng - ngồi cát cho bé và ông bà", travel_from_prev=15),
                act("18:00-20:00", "Tối", "food",
                    HA_FOOD["the_deck_house"],
                    "Dinner The Deck House An Bang", travel_from_prev=10),
                act("20:00-21:00", "Tối", "rest",
                    HA_HOTEL["ha_historic"],
                    "Về khách sạn nghỉ sớm", travel_from_prev=15),
            ]
        },
        {
            "day": 3,
            "title": "Trà Quế - Thanh Hà - Cafe",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["banh_mi_madam_khanh"],
                    "Ăn sáng bánh mì"),
                act("09:00-11:00", "Sáng", "attraction",
                    HA_SIGHT["lang_rau_tra_que"],
                    "Làng rau Trà Quế - đạp xe + làm bánh ít (bé thích)", travel_from_prev=15),
                act("11:00-12:00", "Sáng", "attraction",
                    HA_SIGHT["lang_gom_thanh_ha"],
                    "Làng gốm Thanh Hà", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HA_FOOD["com_ga_ha"],
                    "Ăn trưa cơm gà Hội An", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Nghỉ trưa", travel_from_prev=15),
                act("15:00-17:00", "Chiều", "attraction",
                    HA_SIGHT["lang_moc_kim_bong"],
                    "Làng mộc Kim Bồng", travel_from_prev=15),
                act("17:00-18:30", "Chiều", "food",
                    HA_FOOD["hoian_roastery"],
                    "Cà phê Hoi An Roastery", travel_from_prev=15),
                act("18:30-20:00", "Tối", "food",
                    HA_FOOD["nu_eatery"],
                    "Dinner Nu Eatery", travel_from_prev=10),
            ]
        },
        {
            "day": 4,
            "title": "Chợ - Mua quà - Bay về",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HA_FOOD["banh_mi_phuong"],
                    "Ăn sáng bánh mì Phượng"),
                act("09:00-11:00", "Sáng", "shopping",
                    P(156),  # markets
                    "Chợ Hội An - mua đặc sản", travel_from_prev=10),
                act("11:00-12:00", "Sáng", "food",
                    HA_FOOD["my_quang_ong_hung"],
                    "Ăn mì Quảng cuối", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Check-out + nghỉ sảnh", travel_from_prev=10),
                act("13:30-15:00", "Trưa", "food",
                    HA_FOOD["hoian_roastery"],
                    "Cà phê cuối", travel_from_prev=10),
                act("15:00-16:30", "Chiều", "shopping",
                    HA_SIGHT["may_ao_dai_yaly"],
                    "Mua quà lưu niệm", travel_from_prev=10),
                act("16:30-18:00", "Chiều", "attraction",
                    HA_SIGHT["pho_co"],
                    "Phố cổ lần cuối", travel_from_prev=10),
                act("18:00", "Tối", "end", None,
                    "Về Đà Nẵng - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 2700000,        # 3 đêm x 900k
        "food": 2200000,
        "tickets": 800000,
        "transport": 1200000,
        "other": 400000,
    },
    "estimatedTotalPerPerson": 1833000,  # 9.2M / 5
}

# === HOA01-s: 3N2Đ, 3-5tr, 1 người yên tĩnh ===
HOA01 = {
    "id": "HOA01-s",
    "city": "Hoi An",
    "title": "Hội An Yên Tĩnh 3N2Đ - Solo healing countryside",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 1, "max": 1},
    "budgetPerPerson": {"min": 3000000, "max": 5000000},
    "style": "quiet",
    "hotel": HA_HOTEL["cam_thanh_lotus"],  # 300k countryside
    "days": [
        {
            "day": 1,
            "title": "Đạp xe sáng sớm - Phố cổ vắng",
            "activities": [
                act("06:00-08:00", "Sáng", "attraction",
                    HA_SIGHT["lang_dau_bay_mau"],
                    "Đạp xe quanh làng + rừng dừa sáng sớm"),
                act("08:30-09:30", "Sáng", "food",
                    HA_FOOD["com_ga_ha"],
                    "Ăn sáng cơm gà Hội An tại Cơm gà Hội An trên đường Lý Thường Kiệt"),
                act("10:00-11:00", "Sáng", "hotel",
                    HA_HOTEL["cam_thanh_lotus"],
                    "Check-in Cam Thanh Lotus - yên tĩnh", travel_from_prev=10),
                act("11:00-12:30", "Sáng", "attraction",
                    HA_SIGHT["pho_co"],
                    "Phố cổ lúc vắng - sáng sớm", travel_from_prev=10),
                act("12:30-14:00", "Trưa", "food",
                    HA_FOOD["my_quang_ba_mua_ha"],
                    "Ăn trưa mì Quảng", travel_from_prev=10),
                act("14:00-15:30", "Trưa", "rest",
                    HA_HOTEL["cam_thanh_lotus"],
                    "Nghỉ trưa", travel_from_prev=10),
                act("15:30-17:30", "Chiều", "food",
                    HA_FOOD["cocobox"],
                    "Café bên sông Hoài - yên tĩnh", travel_from_prev=15),
                act("18:00-20:00", "Tối", "food",
                    HA_FOOD["com_ga_ba_buoi"],
                    "Ăn tối nhẹ cơm gà Bà Buội", travel_from_prev=10),
                act("20:00-21:30", "Tối", "rest",
                    HA_HOTEL["cam_thanh_lotus"],
                    "Về homestay nghỉ sớm", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Làng nghề sáng sớm - Spa",
            "activities": [
                act("06:00-07:30", "Sáng", "attraction",
                    HA_SIGHT["lang_gom_thanh_ha"],
                    "Làng gốm Thanh Hà - sáng sớm vắng"),
                act("08:00-09:00", "Sáng", "food",
                    HA_FOOD["banh_mi_phuong"],
                    "Ăn sáng bánh mì Phượng"),
                act("09:00-11:00", "Sáng", "attraction",
                    HA_SIGHT["lang_rau_tra_que"],
                    "Làng rau Trà Quế - thiền trong vườn", travel_from_prev=15),
                act("11:00-12:30", "Sáng", "food",
                    HA_FOOD["banh_bao_my"],
                    "Ăn trưa Bánh Bao Bánh Vạc Mộc", travel_from_prev=10),
                act("12:30-14:00", "Trưa", "rest",
                    HA_HOTEL["cam_thanh_lotus"],
                    "Nghỉ trưa", travel_from_prev=10),
                act("14:00-16:00", "Trưa", "attraction",
                    HA_HOTEL["la_siesta_resort"],
                    "Spa tại La Siesta Resort", travel_from_prev=15),
                act("16:00-18:00", "Chiều", "food",
                    HA_FOOD["cocobox"],
                    "Cà phê bên sông Hoài - hoàng hôn", travel_from_prev=15),
                act("18:30-20:00", "Tối", "food",
                    HA_FOOD["morning_glory"],
                    "Dinner Morning Glory - một mình", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Cafe - Bay về",
            "activities": [
                act("07:00-08:30", "Sáng", "food",
                    HA_FOOD["hi_bakery"],
                    "Ăn sáng Hi Bakery"),
                act("09:00-10:30", "Sáng", "attraction",
                    HA_SIGHT["lang_moc_kim_bong"],
                    "Làng mộc Kim Bồng", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "attraction",
                    HA_SIGHT["pho_co"],
                    "Phố cổ sáng sớm lần cuối", travel_from_prev=15),
                act("12:00-13:00", "Trưa", "food",
                    HA_FOOD["com_ga_ba_buoi"],
                    "Ăn trưa nhẹ cơm gà", travel_from_prev=10),
                act("13:00-14:00", "Trưa", "rest",
                    HA_HOTEL["cam_thanh_lotus"],
                    "Check-out + nghỉ sảnh", travel_from_prev=10),
                act("14:00-15:30", "Chiều", "food",
                    HA_FOOD["hoian_roastery"],
                    "Café cuối Hoi An Roastery", travel_from_prev=10),
                act("15:30", "Chiều", "end", None,
                    "Về Đà Nẵng - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 600000,         # 2 đêm x 300k
        "food": 800000,
        "tickets": 200000,
        "spa": 500000,
        "transport": 400000,
        "other": 200000,
    },
    "estimatedTotalPerPerson": 2700000,
}

# === HOA02-s: 3N2Đ, 4-6.5tr, 1-2 người chụp ảnh ===
HOA02 = {
    "id": "HOA02-s",
    "city": "Hoi An",
    "title": "Hội An Creative 3N2Đ - Photographer aesthetic",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 1, "max": 2},
    "budgetPerPerson": {"min": 4000000, "max": 6500000},
    "style": "photographer",
    "hotel": HA_HOTEL["ha_historic"],
    "days": [
        {
            "day": 1,
            "title": "Sunrise Phố cổ - Đèn lồng golden hour",
            "activities": [
                act("05:30-07:00", "Sáng", "attraction",
                    HA_SIGHT["pho_co"],
                    "Sunrise Phố cổ - chụp ảnh bình minh"),
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["banh_mi_phuong"],
                    "Ăn sáng bánh mì Phượng"),
                act("09:00-10:00", "Sáng", "hotel",
                    HA_HOTEL["ha_historic"],
                    "Check-in Hoi An Historic", travel_from_prev=10),
                act("10:00-12:00", "Sáng", "attraction",
                    HA_SIGHT["pho_co"],
                    "Phố cổ - chụp Chùa Cầu, Hội quán", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HA_FOOD["morning_glory"],
                    "Ăn trưa Morning Glory", travel_from_prev=10),
                act("13:30-15:30", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Nghỉ trưa + edit ảnh", travel_from_prev=10),
                act("15:30-17:30", "Chiều", "attraction",
                    HA_SIGHT["pho_co"],
                    "Phố cổ - chụp nhà cổ, kiến trúc", travel_from_prev=10),
                act("17:30-18:30", "Chiều", "attraction",
                    HA_SIGHT["thuyen_song_thu_bon"],
                    "Sunset thuyền sông Hoài (golden hour 17:30-18:30)", travel_from_prev=10),
                act("18:30-20:00", "Tối", "food",
                    HA_FOOD["mango_mango"],
                    "Dinner Mango Mango - view sông", travel_from_prev=10),
                act("20:00-22:00", "Tối", "attraction",
                    HA_SIGHT["pho_den_long"],
                    "Phố đèn lồng - chụp ảnh ban đêm", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Trà Quế - Bảy Mẫu - Sunset An Bàng",
            "activities": [
                act("05:30-07:00", "Sáng", "attraction",
                    HA_SIGHT["bai_an_bang"],
                    "Sunrise An Bàng"),
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["com_ga_ba_buoi"],
                    "Ăn sáng cơm gà"),
                act("09:00-11:30", "Sáng", "attraction",
                    HA_SIGHT["lang_rau_tra_que"],
                    "Làng rau Trà Quế - chụp ảnh nông thôn", travel_from_prev=15),
                act("11:30-13:00", "Trưa", "food",
                    HA_FOOD["my_quang_ong_hung"],
                    "Ăn trưa mì Quảng", travel_from_prev=10),
                act("13:00-15:00", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Nghỉ trưa", travel_from_prev=15),
                act("15:00-17:00", "Chiều", "attraction",
                    HA_SIGHT["lang_dau_bay_mau"],
                    "Rừng dừa Bảy Mẫu - thuyền thúng chụp ảnh", travel_from_prev=15),
                act("17:00-19:00", "Chiều", "attraction",
                    HA_SIGHT["bai_an_bang"],
                    "Sunset An Bàng - golden hour", travel_from_prev=15),
                act("19:00-21:00", "Tối", "food",
                    HA_FOOD["the_deck_house"],
                    "Dinner The Deck House An Bang", travel_from_prev=10),
                act("21:00-22:00", "Tối", "rest",
                    HA_HOTEL["ha_historic"],
                    "Về khách sạn", travel_from_prev=15),
            ]
        },
        {
            "day": 3,
            "title": "Thanh Hà - Cafe vintage - Bay về",
            "activities": [
                act("07:00-08:30", "Sáng", "food",
                    HA_FOOD["hi_bakery"],
                    "Ăn sáng Hi Bakery"),
                act("09:00-11:00", "Sáng", "attraction",
                    HA_SIGHT["lang_gom_thanh_ha"],
                    "Làng gốm Thanh Hà - chụp ảnh làng nghề", travel_from_prev=15),
                act("11:00-12:00", "Sáng", "attraction",
                    HA_SIGHT["lang_bich_hoa_tam_thanh"],
                    "Làng bích họa Tam Thanh - chụp ảnh", travel_from_prev=15),
                act("12:00-13:30", "Trưa", "food",
                    HA_FOOD["com_ga_ha"],
                    "Ăn trưa cơm gà", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "rest",
                    HA_HOTEL["ha_historic"],
                    "Check-out + nghỉ sảnh", travel_from_prev=10),
                act("15:00-16:30", "Chiều", "food",
                    HA_FOOD["the_hill_station"],
                    "Café Hill Station - vintage", travel_from_prev=10),
                act("16:30-18:00", "Chiều", "attraction",
                    HA_SIGHT["pho_co"],
                    "Phố cổ lần cuối", travel_from_prev=10),
                act("18:00", "Tối", "end", None,
                    "Về Đà Nẵng - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 1800000,
        "food": 1500000,
        "tickets": 500000,
        "transport": 600000,
        "other": 300000,
    },
    "estimatedTotalPerPerson": 2350000,  # 4.7M / 2
}

# === HOA03-s: 3N2Đ, 2.5-4tr, 1 backpacker ===
HOA03 = {
    "id": "HOA03-s",
    "city": "Hoi An",
    "title": "Hội An Backpacker 3N2Đ - Solo tiết kiệm",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 1, "max": 1},
    "budgetPerPerson": {"min": 2500000, "max": 4000000},
    "style": "backpacker",
    "hotel": HA_HOTEL["ha_backpacker"],  # 180k hostel
    "days": [
        {
            "day": 1,
            "title": "Phố cổ - Cao Lầu - Bánh mì Phượng",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HA_FOOD["banh_mi_phuong"],
                    "Bánh mì Phượng - 30k"),
                act("09:00-10:00", "Sáng", "hotel",
                    HA_HOTEL["ha_backpacker"],
                    "Check-in Hoi An Backpacker hostel", travel_from_prev=10),
                act("10:00-12:00", "Sáng", "attraction",
                    HA_SIGHT["pho_co"],
                    "Phố cổ Hội An - vé vào 120k", travel_from_prev=10),
                act("12:00-13:00", "Trưa", "food",
                    HA_FOOD["cao_lau_lien"],
                    "Cao Lầu Liên - 40k", travel_from_prev=10),
                act("13:00-15:00", "Trưa", "rest",
                    HA_HOTEL["ha_backpacker"],
                    "Nghỉ trưa", travel_from_prev=10),
                act("15:00-17:00", "Chiều", "shopping",
                    P(156),  # markets
                    "Chợ Hội An - mua sắm", travel_from_prev=10),
                act("17:00-18:30", "Chiều", "food",
                    HA_FOOD["banh_trang_nuong"],
                    "Ăn nhẹ bánh tráng nướng", travel_from_prev=10),
                act("18:30-20:00", "Tối", "food",
                    HA_FOOD["com_ga_ba_buoi"],
                    "Cơm gà Bà Buội - 40k", travel_from_prev=10),
                act("20:00-22:00", "Tối", "attraction",
                    HA_SIGHT["cho_dem_HA"],
                    "Chợ đêm Hội An", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Đạp xe An Bàng - Làng gốm",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["banh_mi_madam_khanh"],
                    "Bánh mì Madam Khánh - 30k"),
                act("09:00-11:00", "Sáng", "attraction",
                    HA_SIGHT["bai_an_bang"],
                    "Đạp xe An Bàng - FREE", travel_from_prev=15),
                act("11:00-12:00", "Sáng", "food",
                    HA_FOOD["my_quang_ba_mua_ha"],
                    "Ăn mì Quảng - 40k", travel_from_prev=10),
                act("12:00-15:00", "Trưa", "rest",
                    HA_HOTEL["ha_backpacker"],
                    "Nghỉ trưa + tắm", travel_from_prev=10),
                act("15:00-17:00", "Chiều", "attraction",
                    HA_SIGHT["lang_gom_thanh_ha"],
                    "Làng gốm Thanh Hà - 50k", travel_from_prev=15),
                act("17:00-18:30", "Chiều", "food",
                    HA_FOOD["cocobox"],
                    "Café bên sông", travel_from_prev=15),
                act("18:30-20:00", "Tối", "food",
                    HA_FOOD["com_ga_ha"],
                    "Cơm gà Hội An - 40k", travel_from_prev=10),
                act("20:00-22:00", "Tối", "attraction",
                    HA_SIGHT["cho_dem_HA"],
                    "Chợ đêm lần 2", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Trà Quế - Bay về",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HA_FOOD["banh_mi_phuong"],
                    "Bánh mì Phượng - 30k"),
                act("09:00-11:00", "Sáng", "attraction",
                    HA_SIGHT["lang_rau_tra_que"],
                    "Làng rau Trà Quế - đạp xe", travel_from_prev=15),
                act("11:00-12:00", "Sáng", "attraction",
                    HA_SIGHT["lang_moc_kim_bong"],
                    "Làng mộc Kim Bồng", travel_from_prev=10),
                act("12:00-13:00", "Trưa", "food",
                    HA_FOOD["my_quang_ong_hung"],
                    "Ăn trưa mì Quảng - 40k", travel_from_prev=10),
                act("13:00-14:00", "Trưa", "rest",
                    HA_HOTEL["ha_backpacker"],
                    "Check-out + nghỉ sảnh", travel_from_prev=10),
                act("14:00-15:30", "Chiều", "shopping",
                    P(156),
                    "Mua quà chợ", travel_from_prev=10),
                act("15:30", "Chiều", "end", None,
                    "Về Đà Nẵng - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 360000,         # 2 đêm x 180k
        "food": 500000,
        "tickets": 250000,
        "transport": 200000,
        "other": 100000,
    },
    "estimatedTotalPerPerson": 1410000,
}

# ============================================================
# HUẾ - 8 PLANS
# ============================================================

HUE_FOOD = {
    "bun_bo_ophuong": P(44),         # Bún bò O Phượng
    "bun_bo_dong_ba": P(99),         # Bún bò Đông Ba
    "bun_bo_my_re": P(45),           # Use 45 for my_re
    "banh_khoai_hanh": P(65),        # Bánh khoái Hạnh
    "banh_beo_nam_loc": P(92),       # Bánh bèo nậm lọc
    "com_hen_nang_buoi": P(78),      # Cơm hến Nàng Buối
    "com_hen_ba_hong": P(158),       # Cơm hến bà Hồng
    "bun_hen_nang_suong": P(157),    # Bún hến Nàng Sương
    "che_hue": P(106),               # Chè Huế (chè hẻm)
    "che_ba_lien": P(196),           # Chè Huế bà Liên
    "ancient_hue": P(127),           # Ancient Hue Restaurant
    "tui_an": P(148),                # Tứi An buffet 49 món
    "madam_thu": P(104),             # Madam Thủy
    "banh_canh_nam_pho": P(183),     # Bánh canh Nam Phổ
    "banh_nam_ba_doi": P(194),       # Bánh nậm bà Đợi
    "nem_lui_ba_ty": P(195),         # Nem lụi bà Tý
    "banh_bot_loc_ba_hanh": P(231),  # Bánh bột lọc bà Hạnh
    "banh_hat_sen": P(263),          # Bánh hạt sen Huế
    "con_hen": P(94),                # Cồn Hến
    "com_tam_suon": P(147),          # Cơm tấm Sườn Cây Bàng
    "cafe_mat_biec": P(159),         # Cafe Mắt Biếc
    "bun_rieu_cua_hue": P(222),      # Bún riêu cua Huế
    "bun_hen_thuong": P(222),        # alias
    "com_am_phu": P(127),            # use Ancient Hue for royal cuisine
}
HUE_SIGHT = {
    "dai_noi": P(6),                # Đại Nội
    "ngo_mon": P(10),               # Ngọ Môn
    "chua_thien_mu": P(11),         # Chùa Thiên Mụ
    "lang_tu_duc": P(14),           # Lăng Tự Đức
    "lang_khai_dinh": P(21),        # Lăng Khải Định
    "lang_minh_mang": P(28),        # Lăng Minh Mạng
    "dien_thai_hoa": P(32),         # Điện Thái Hòa
    "tu_cam_thanh": P(43),          # Tử Cấm Thành
    "huong_mieu": P(64),            # Hưng Miếu
    "cau_truong_tien": P(29),       # Cầu Trường Tiền
    "song_huong": P(22),            # Sông Hương
    "cho_dong_ba": P(23),           # Chợ Đông Ba
    "cho_an_cuu": P(168),           # Chợ An Cựu
    "lang_huong_thuy_xuan": P(177), # reuse for hương
    "lang_lua": P(177),             # Làng lụa
    "cung_an_dinh": P(303),         # Cung An Định
    "dinh_lap_an": P(67),           # Đầm Lập An
    "nui_ngu_binh": P(54),          # Núi Ngự Bình
    "lang_gia_long": P(77),         # Lăng Gia Long
    "doi_vong_canh": P(66),         # Đồi Vọng Cảnh
    "lang_bach_ma": P(46),          # Bạch Mã
    "pho_di_bo": P(68),             # Phố đi bộ Nguyễn Đình Chiểu
    "trinh_duong": P(225),          # Trường Quốc Học
    "lang_bich_hoa_tam_thanh": P(431),  # reuse
    "cho_ben_ngu": P(167),          # Chợ Bến Ngự
}
HUE_HOTEL = {
    "jade": P(637),                # 450k budget city
    "alan": P(638),                # 350k budget
    "hue_backpackers": P(639),     # 250k hostel
    "hong_thien": P(640),          # 400k budget
    "hue_nino": P(641),            # 450k budget
    "tam_homestay": P(642),        # 350k homestay
    "canary": P(643),              # 900k mid
    "moonlight": P(644),           # 1.3M mid
    "villa_louise": P(645),        # 1.5M mid
    "eldora": P(646),              # 1.6M mid
    "rosaleen": P(647),            # 1.1M mid
    "heritage_hue": P(648),        # 1.05M mid
    "hue_serene": P(649),          # 1.2M mid
    "indochine": P(650),           # 2.8M luxury
    "azerai": P(651),              # 3.5M luxury
    "silk_path": P(653),           # 3M luxury
    "thanh_lich": P(654),          # 2.3M luxury
    "angsana": P(655),             # 4.5M resort
    "banyan": P(656),              # 8.5M resort
    "pilgrimage": P(652),          # 3.2M resort
    "saigon_morin": P(105),        # 1.8M 4-star
    "imperial": P(133),            # 2.2M 5-star
    "century": P(162),             # 1.6M 4-star
    "orchid": P(174),              # 1.7M 4-star
    "hue_serene_shining": P(184),  # 1.5M 4-star
}

# === HUE01-s: 3N2Đ, 3.5-5.5tr, gia đình 3-4 người ===
HUE01 = {
    "id": "HUE01-s",
    "city": "Hue",
    "title": "Huế Imperial Heritage 3N2Đ - Gia đình cố đô",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 3, "max": 4},
    "budgetPerPerson": {"min": 3500000, "max": 5500000},
    "style": "family",
    "hotel": HUE_HOTEL["moonlight"],   # 1.3M mid river
    "days": [
        {
            "day": 1,
            "title": "Đại Nội - Sông Hương - Ca Huế",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HUE_FOOD["banh_canh_nam_pho"],
                    "Ăn sáng Bánh canh Nam Phổ - 25k"),
                act("09:00-10:00", "Sáng", "hotel",
                    HUE_HOTEL["moonlight"],
                    "Check-in Moonlight Hotel Huế", travel_from_prev=15),
                act("10:00-12:00", "Sáng", "attraction",
                    HUE_SIGHT["dai_noi"],
                    "Đại Nội Huế - 200k vé", travel_from_prev=15),
                act("12:00-13:30", "Trưa", "food",
                    HUE_FOOD["bun_bo_ophuong"],
                    "Ăn trưa Bún bò Huế O Phượng - 17 Lý Thường Kiệt - 40k", travel_from_prev=15),
                act("13:30-15:30", "Trưa", "rest",
                    HUE_HOTEL["moonlight"],
                    "Nghỉ trưa", travel_from_prev=15),
                act("15:30-17:00", "Chiều", "attraction",
                    HUE_SIGHT["dien_thai_hoa"],
                    "Điện Thái Hòa - Tử Cấm Thành", travel_from_prev=10),
                act("17:00-18:30", "Chiều", "attraction",
                    HUE_SIGHT["cau_truong_tien"],
                    "Cầu Trường Tiền - Sông Hương", travel_from_prev=10),
                act("18:30-20:00", "Tối", "food",
                    HUE_FOOD["com_hen_ba_hong"],
                    "Ăn tối Cơm hến bà Hồng - 30k", travel_from_prev=10),
                act("20:00-22:00", "Tối", "attraction",
                    HUE_SIGHT["song_huong"],
                    "Ca Huế sông Hương - 150k", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Lăng Tự Đức - Lăng Khải Định - Chùa Thiên Mụ",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["bun_bo_dong_ba"],
                    "Ăn sáng Bún bò Đông Ba - 35k"),
                act("08:30-10:30", "Sáng", "attraction",
                    HUE_SIGHT["lang_tu_duc"],
                    "Lăng Tự Đức - 150k vé", travel_from_prev=20),
                act("10:30-12:00", "Sáng", "attraction",
                    HUE_SIGHT["lang_khai_dinh"],
                    "Lăng Khải Định - 150k vé - kiến trúc Đông Tây", travel_from_prev=15),
                act("12:00-13:30", "Trưa", "food",
                    HUE_FOOD["banh_beo_nam_loc"],
                    "Ăn trưa Bánh bèo nậm lọc - 50k", travel_from_prev=20),
                act("13:30-15:30", "Trưa", "rest",
                    HUE_HOTEL["moonlight"],
                    "Nghỉ trưa", travel_from_prev=20),
                act("15:30-17:00", "Chiều", "attraction",
                    HUE_SIGHT["chua_thien_mu"],
                    "Chùa Thiên Mụ - FREE", travel_from_prev=20),
                act("17:00-18:30", "Chiều", "attraction",
                    HUE_SIGHT["song_huong"],
                    "Dạo Sông Hương", travel_from_prev=10),
                act("18:30-20:00", "Tối", "food",
                    HUE_FOOD["com_hen_nang_buoi"],
                    "Ăn tối Cơm hến Nàng Buối - 15k", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Chợ Đông Ba - Mua quà - Bay về",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["che_hue"],
                    "Ăn sáng Chè Huế - 15k"),
                act("09:00-10:30", "Sáng", "shopping",
                    HUE_SIGHT["cho_dong_ba"],
                    "Chợ Đông Ba - mua mè xửng, hạt sen, nón bài thơ", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "food",
                    HUE_FOOD["bun_hen_nang_suong"],
                    "Ăn Bún hến Nàng Sương", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "rest",
                    HUE_HOTEL["moonlight"],
                    "Check-out + nghỉ sảnh", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "food",
                    HUE_FOOD["banh_khoai_hanh"],
                    "Ăn Bánh khoái Hạnh", travel_from_prev=10),
                act("15:00-16:30", "Chiều", "attraction",
                    HUE_SIGHT["cho_dong_ba"],
                    "Mua quà thêm", travel_from_prev=10),
                act("16:30-18:00", "Chiều", "food",
                    HUE_FOOD["che_ba_lien"],
                    "Chè cuối - bà Liên", travel_from_prev=10),
                act("18:00", "Tối", "end", None,
                    "Ra sân bay - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 2600000,        # 2 đêm x 1.3M
        "food": 1200000,         # 3 ngày / 4 người
        "tickets": 800000,       # Đại Nội + 2 lăng
        "transport": 800000,
        "other": 200000,
    },
    "estimatedTotalPerPerson": 1400000,  # 5.6M / 4
}

# === HUE02-s: 3N2Đ, 3-4.5tr, 1-2 người foodie ===
HUE02 = {
    "id": "HUE02-s",
    "city": "Hue",
    "title": "Huế Food Trip 3N2Đ - Ăn vặt cố đô",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 1, "max": 2},
    "budgetPerPerson": {"min": 3000000, "max": 4500000},
    "style": "foodie",
    "hotel": HUE_HOTEL["jade"],   # 450k budget
    "days": [
        {
            "day": 1,
            "title": "Bún bò - Bánh bèo nậm lọc - Cơm hến",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HUE_FOOD["bun_bo_ophuong"],
                    "Bún bò Huế O Phượng - 40k"),
                act("09:00-10:00", "Sáng", "hotel",
                    HUE_HOTEL["jade"],
                    "Check-in Jade Hotel", travel_from_prev=15),
                act("10:00-12:00", "Sáng", "attraction",
                    HUE_SIGHT["dai_noi"],
                    "Đại Nội Huế - 200k", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HUE_FOOD["com_hen_ba_hong"],
                    "Cơm hến bà Hồng - 20k", travel_from_prev=10),
                act("13:30-15:00", "Trưa", "rest",
                    HUE_HOTEL["jade"],
                    "Nghỉ trưa", travel_from_prev=10),
                act("15:00-17:00", "Chiều", "food",
                    HUE_FOOD["che_hue"],
                    "Chè Huế - hẻm 15k", travel_from_prev=10),
                act("17:00-18:30", "Chiều", "food",
                    HUE_FOOD["cafe_mat_biec"],
                    "Cà phê Mắt Biếc - 60k", travel_from_prev=10),
                act("18:30-20:00", "Tối", "food",
                    HUE_FOOD["banh_khoai_hanh"],
                    "Bánh khoái Hạnh - 60k", travel_from_prev=10),
                act("20:00-21:30", "Tối", "attraction",
                    HUE_SIGHT["cau_truong_tien"],
                    "Cầu Trường Tiền đêm", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Chợ Đông Ba - Bánh bèo - Nem lụi",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["bun_bo_dong_ba"],
                    "Bún bò Đông Ba - 35k"),
                act("09:00-11:00", "Sáng", "shopping",
                    HUE_SIGHT["cho_dong_ba"],
                    "Chợ Đông Ba - ăn sáng tại chợ", travel_from_prev=15),
                act("11:00-12:30", "Sáng", "food",
                    HUE_FOOD["com_am_phu"],
                    "Cơm âm phủ Huế tại Ancient Hue Restaurant - món cung đình trong chợ Đông Ba", travel_from_prev=10),
                act("12:30-14:00", "Trưa", "rest",
                    HUE_HOTEL["jade"],
                    "Nghỉ trưa", travel_from_prev=15),
                act("14:00-16:00", "Trưa", "food",
                    HUE_FOOD["banh_beo_nam_loc"],
                    "Bánh bèo - bánh nậm - bánh lọc Hạnh", travel_from_prev=10),
                act("16:00-18:00", "Chiều", "attraction",
                    HUE_SIGHT["chua_thien_mu"],
                    "Chùa Thiên Mụ", travel_from_prev=15),
                act("18:00-20:00", "Tối", "food",
                    HUE_FOOD["nem_lui_ba_ty"],
                    "Nem lụi bà Tý - 50k", travel_from_prev=15),
                act("20:00-22:00", "Tối", "food",
                    HUE_FOOD["che_ba_lien"],
                    "Chè bà Liên + ăn vặt", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Chè - Bay về",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["banh_canh_nam_pho"],
                    "Bánh canh Nam Phổ - 35k"),
                act("09:00-10:30", "Sáng", "attraction",
                    HUE_SIGHT["lang_minh_mang"],
                    "Lăng Minh Mạng - 150k", travel_from_prev=20),
                act("10:30-12:00", "Sáng", "food",
                    HUE_FOOD["bun_hen_nang_suong"],
                    "Ăn nhẹ Bún hến Nàng Sương", travel_from_prev=15),
                act("12:00-13:30", "Trưa", "rest",
                    HUE_HOTEL["jade"],
                    "Check-out + nghỉ sảnh", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "food",
                    HUE_FOOD["che_hue"],
                    "Chè Huế cuối cùng", travel_from_prev=10),
                act("15:00-16:30", "Chiều", "shopping",
                    HUE_SIGHT["cho_dong_ba"],
                    "Mua mè xửng, hạt sen", travel_from_prev=10),
                act("16:30", "Chiều", "end", None,
                    "Ra sân bay - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 900000,         # 2 đêm x 450k
        "food": 1200000,
        "tickets": 500000,
        "transport": 500000,
        "other": 200000,
    },
    "estimatedTotalPerPerson": 1650000,
}

# === HUE03-s: 3N2Đ, 3.5-5tr, đi cùng người lớn tuổi ===
HUE03 = {
    "id": "HUE03-s",
    "city": "Hue",
    "title": "Huế Slow Travel 3N2Đ - Cùng người lớn tuổi",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 2, "max": 3},
    "budgetPerPerson": {"min": 3500000, "max": 5000000},
    "style": "elderly",
    "hotel": HUE_HOTEL["hue_serene"],  # 1.2M
    "days": [
        {
            "day": 1,
            "title": "Sông Hương - Cầu Trường Tiền - Cafe",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HUE_FOOD["banh_canh_nam_pho"],
                    "Ăn sáng Bánh canh Nam Phổ"),
                act("09:00-10:00", "Sáng", "hotel",
                    HUE_HOTEL["hue_serene"],
                    "Check-in Hue Serene Palace", travel_from_prev=15),
                act("10:00-12:00", "Sáng", "attraction",
                    HUE_SIGHT["song_huong"],
                    "Dạo Sông Hương - ngồi xe điện", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HUE_FOOD["bun_bo_ophuong"],
                    "Ăn trưa Bún bò O Phượng", travel_from_prev=10),
                act("13:30-15:30", "Trưa", "rest",
                    HUE_HOTEL["hue_serene"],
                    "Nghỉ trưa dài", travel_from_prev=10),
                act("15:30-17:00", "Chiều", "food",
                    HUE_FOOD["cafe_mat_biec"],
                    "Cafe Mắt Biếc - view sông Hương", travel_from_prev=10),
                act("17:00-18:30", "Chiều", "attraction",
                    HUE_SIGHT["cau_truong_tien"],
                    "Cầu Trường Tiền - ngắm hoàng hôn", travel_from_prev=10),
                act("18:30-20:00", "Tối", "food",
                    HUE_FOOD["com_hen_ba_hong"],
                    "Ăn tối Cơm hến bà Hồng", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Đại Nội - Chùa Thiên Mụ",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["bun_bo_dong_ba"],
                    "Ăn sáng Bún bò Đông Ba"),
                act("09:00-11:00", "Sáng", "attraction",
                    HUE_SIGHT["dai_noi"],
                    "Đại Nội - xe điện cho mẹ", travel_from_prev=15),
                act("11:00-12:30", "Sáng", "attraction",
                    HUE_SIGHT["chua_thien_mu"],
                    "Chùa Thiên Mụ - chụp ảnh, không leo", travel_from_prev=20),
                act("12:30-14:00", "Trưa", "food",
                    HUE_FOOD["com_hen_nang_buoi"],
                    "Ăn trưa Cơm hến Nàng Buối", travel_from_prev=20),
                act("14:00-15:30", "Trưa", "rest",
                    HUE_HOTEL["hue_serene"],
                    "Nghỉ trưa dài", travel_from_prev=20),
                act("15:30-17:00", "Chiều", "attraction",
                    HUE_SIGHT["song_huong"],
                    "Sông Hương - hoàng hôn", travel_from_prev=10),
                act("17:00-19:00", "Chiều", "attraction",
                    HUE_SIGHT["pho_di_bo"],
                    "Phố đi bộ Nguyễn Đình Chiểu", travel_from_prev=10),
                act("19:00-21:00", "Tối", "food",
                    HUE_FOOD["ancient_hue"],
                    "Dinner Ancient Hue Restaurant - royal cuisine", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Chợ Đông Ba - Bay về",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["che_hue"],
                    "Ăn sáng Chè Huế"),
                act("09:00-10:30", "Sáng", "shopping",
                    HUE_SIGHT["cho_dong_ba"],
                    "Chợ Đông Ba - mua mè xửng, hạt sen, nón bài thơ", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "food",
                    HUE_FOOD["banh_beo_nam_loc"],
                    "Ăn nhẹ bánh bèo nậm lọc", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "rest",
                    HUE_HOTEL["hue_serene"],
                    "Check-out + nghỉ sảnh", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "food",
                    HUE_FOOD["bun_bo_ophuong"],
                    "Ăn Bún bò O Phượng cuối", travel_from_prev=10),
                act("15:00-16:30", "Chiều", "food",
                    HUE_FOOD["che_ba_lien"],
                    "Chè cuối cùng", travel_from_prev=10),
                act("16:30", "Chiều", "end", None,
                    "Ra sân bay - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 2400000,        # 2 đêm x 1.2M
        "food": 800000,
        "tickets": 500000,
        "transport": 600000,
        "other": 200000,
    },
    "estimatedTotalPerPerson": 1500000,  # 4.5M / 3
}

# === HUE04-s: 4N3Đ, 5-7tr, 1 người thích lịch sử ===
HUE04 = {
    "id": "HUE04-s",
    "city": "Hue",
    "title": "Huế History Explorer 4N3Đ - Solo đi sâu lịch sử",
    "duration": "4 ngày 3 đêm",
    "durationDays": 4,
    "durationNights": 3,
    "travelers": {"min": 1, "max": 1},
    "budgetPerPerson": {"min": 5000000, "max": 7000000},
    "style": "history",
    "hotel": HUE_HOTEL["hue_serene"],  # 1.2M
    "days": [
        {
            "day": 1,
            "title": "Đại Nội - Bảo tàng Cổ vật",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HUE_FOOD["bun_bo_ophuong"],
                    "Ăn sáng Bún bò O Phượng"),
                act("09:00-10:00", "Sáng", "hotel",
                    HUE_HOTEL["hue_serene"],
                    "Check-in Hue Serene Palace", travel_from_prev=15),
                act("10:00-13:00", "Cả ngày", "attraction",
                    HUE_SIGHT["dai_noi"],
                    "Đại Nội: Ngọ Môn, Điện Thái Hòa, Thế Miếu, Hiển Lâm Các, Cửu Đỉnh - 4h", travel_from_prev=10),
                act("13:00-14:00", "Trưa", "food",
                    HUE_FOOD["com_hen_ba_hong"],
                    "Ăn trưa Cơm hến bà Hồng", travel_from_prev=10),
                act("14:00-15:30", "Trưa", "rest",
                    HUE_HOTEL["hue_serene"],
                    "Nghỉ trưa", travel_from_prev=10),
                act("15:30-17:30", "Chiều", "attraction",
                    P(122),  # Bảo tàng Mỹ thuật Cung đình
                    "Bảo tàng Cổ vật Cung đình Huế - 100k", travel_from_prev=10),
                act("17:30-19:00", "Chiều", "attraction",
                    HUE_SIGHT["cau_truong_tien"],
                    "Cầu Trường Tiền - hoàng hôn", travel_from_prev=10),
                act("19:00-21:00", "Tối", "food",
                    HUE_FOOD["ancient_hue"],
                    "Dinner Ancient Hue Restaurant - cung đình Huế", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Lăng phía Nam: Tự Đức + Khải Định",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["banh_canh_nam_pho"],
                    "Ăn sáng Bánh canh Nam Phổ"),
                act("08:30-11:00", "Sáng", "attraction",
                    HUE_SIGHT["lang_tu_duc"],
                    "Lăng Tự Đức - 150k", travel_from_prev=20),
                act("11:00-12:30", "Sáng", "attraction",
                    HUE_SIGHT["lang_khai_dinh"],
                    "Lăng Khải Định - 150k - Gothic Đông Tây", travel_from_prev=15),
                act("12:30-14:00", "Trưa", "food",
                    HUE_FOOD["bun_bo_dong_ba"],
                    "Ăn trưa Bún bò Đông Ba", travel_from_prev=20),
                act("14:00-15:30", "Trưa", "rest",
                    HUE_HOTEL["hue_serene"],
                    "Nghỉ trưa", travel_from_prev=20),
                act("15:30-17:00", "Chiều", "attraction",
                    HUE_SIGHT["chua_thien_mu"],
                    "Chùa Thiên Mụ", travel_from_prev=20),
                act("17:00-19:00", "Chiều", "food",
                    HUE_FOOD["cafe_mat_biec"],
                    "Cafe Mắt Biếc + sông Hương", travel_from_prev=10),
                act("19:00-21:00", "Tối", "food",
                    HUE_FOOD["com_hen_nang_buoi"],
                    "Dinner Cơm hến Nàng Buối", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Lăng phía Tây: Minh Mạng + Gia Long",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["bun_bo_ophuong"],
                    "Ăn sáng Bún bò O Phượng"),
                act("08:30-11:00", "Sáng", "attraction",
                    HUE_SIGHT["lang_minh_mang"],
                    "Lăng Minh Mạng - 150k - kiến trúc sơn thủy", travel_from_prev=20),
                act("11:00-12:30", "Sáng", "attraction",
                    HUE_SIGHT["lang_gia_long"],
                    "Lăng Gia Long - 150k", travel_from_prev=20),
                act("12:30-14:00", "Trưa", "food",
                    HUE_FOOD["banh_beo_nam_loc"],
                    "Ăn trưa Bánh bèo nậm lọc", travel_from_prev=20),
                act("14:00-15:30", "Trưa", "rest",
                    HUE_HOTEL["hue_serene"],
                    "Nghỉ trưa", travel_from_prev=20),
                act("15:30-17:30", "Chiều", "attraction",
                    HUE_SIGHT["doi_vong_canh"],
                    "Đồi Vọng Cảnh - panorama toàn cảnh Huế", travel_from_prev=20),
                act("17:30-19:00", "Chiều", "attraction",
                    HUE_SIGHT["song_huong"],
                    "Dạo Sông Hương", travel_from_prev=10),
                act("19:00-21:00", "Tối", "food",
                    HUE_FOOD["nem_lui_ba_ty"],
                    "Nem lụi bà Tý", travel_from_prev=10),
            ]
        },
        {
            "day": 4,
            "title": "Cung An Định - Bảo tàng - Bay về",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["che_hue"],
                    "Ăn sáng Chè Huế"),
                act("09:00-10:30", "Sáng", "attraction",
                    HUE_SIGHT["cung_an_dinh"],
                    "Cung An Định - 30k", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "attraction",
                    P(122),  # Bảo tàng Cung đình
                    "Bảo tàng Mỹ thuật Cung đình", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HUE_FOOD["com_hen_ba_hong"],
                    "Ăn trưa Cơm hến", travel_from_prev=10),
                act("13:30-15:00", "Trưa", "rest",
                    HUE_HOTEL["hue_serene"],
                    "Check-out + nghỉ sảnh", travel_from_prev=10),
                act("15:00-16:30", "Chiều", "shopping",
                    HUE_SIGHT["cho_dong_ba"],
                    "Chợ Đông Ba mua quà", travel_from_prev=15),
                act("16:30-18:00", "Chiều", "food",
                    HUE_FOOD["che_ba_lien"],
                    "Chè cuối + café", travel_from_prev=10),
                act("18:00", "Tối", "end", None,
                    "Ra sân bay - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 3600000,        # 3 đêm x 1.2M
        "food": 1200000,
        "tickets": 1200000,      # Đại Nội + 4 lăng + 2 bảo tàng
        "transport": 700000,
        "other": 200000,
    },
    "estimatedTotalPerPerson": 6900000,
}

# === HUE05-s: 4N3Đ, 5-8tr, gia đình đa thế hệ ===
HUE05 = {
    "id": "HUE05-s",
    "city": "Hue",
    "title": "Huế Family 4N3Đ - Gia đình đa thế hệ",
    "duration": "4 ngày 3 đêm",
    "durationDays": 4,
    "durationNights": 3,
    "travelers": {"min": 3, "max": 5},
    "budgetPerPerson": {"min": 5000000, "max": 8000000},
    "style": "family",
    "hotel": HUE_HOTEL["moonlight"],
    "days": [
        {
            "day": 1,
            "title": "Đại Nội - Sông Hương - Cafe",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HUE_FOOD["banh_canh_nam_pho"],
                    "Ăn sáng Bánh canh Nam Phổ"),
                act("09:00-10:00", "Sáng", "hotel",
                    HUE_HOTEL["moonlight"],
                    "Check-in Moonlight Hotel", travel_from_prev=15),
                act("10:00-12:00", "Sáng", "attraction",
                    HUE_SIGHT["dai_noi"],
                    "Đại Nội - 200k", travel_from_prev=15),
                act("12:00-13:30", "Trưa", "food",
                    HUE_FOOD["bun_bo_ophuong"],
                    "Ăn trưa Bún bò O Phượng", travel_from_prev=15),
                act("13:30-15:30", "Trưa", "rest",
                    HUE_HOTEL["moonlight"],
                    "Nghỉ trưa dài", travel_from_prev=10),
                act("15:30-17:00", "Chiều", "food",
                    HUE_FOOD["cafe_mat_biec"],
                    "Cafe Mắt Biếc - sông Hương", travel_from_prev=10),
                act("17:00-18:30", "Chiều", "attraction",
                    HUE_SIGHT["cau_truong_tien"],
                    "Cầu Trường Tiền - hoàng hôn", travel_from_prev=10),
                act("18:30-20:00", "Tối", "food",
                    HUE_FOOD["com_hen_ba_hong"],
                    "Ăn tối Cơm hến bà Hồng", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Chùa Thiên Mụ - Lăng Minh Mạng",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["bun_bo_dong_ba"],
                    "Ăn sáng Bún bò Đông Ba"),
                act("09:00-11:00", "Sáng", "attraction",
                    HUE_SIGHT["chua_thien_mu"],
                    "Chùa Thiên Mụ - không leo cho người lớn tuổi", travel_from_prev=20),
                act("11:00-12:30", "Sáng", "attraction",
                    HUE_SIGHT["lang_minh_mang"],
                    "Lăng Minh Mạng - 150k - chụp ảnh bên ngoài", travel_from_prev=20),
                act("12:30-14:00", "Trưa", "food",
                    HUE_FOOD["com_hen_nang_buoi"],
                    "Ăn trưa Cơm hến Nàng Buối", travel_from_prev=20),
                act("14:00-15:30", "Trưa", "rest",
                    HUE_HOTEL["moonlight"],
                    "Nghỉ trưa dài", travel_from_prev=20),
                act("15:30-17:00", "Chiều", "attraction",
                    HUE_SIGHT["song_huong"],
                    "Thuyền sông Hương nhẹ - thuyền rồng", travel_from_prev=10),
                act("17:00-19:00", "Chiều", "food",
                    HUE_FOOD["ancient_hue"],
                    "Cà phê + bánh", travel_from_prev=10),
                act("19:00-21:00", "Tối", "food",
                    HUE_FOOD["ancient_hue"],
                    "Dinner Ancient Hue Restaurant - gia đình", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Lăng Khải Định - Làng hương Thủy Xuân",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["banh_canh_nam_pho"],
                    "Ăn sáng"),
                act("08:30-10:30", "Sáng", "attraction",
                    HUE_SIGHT["lang_khai_dinh"],
                    "Lăng Khải Định - 150k - xe điện cho người lớn", travel_from_prev=20),
                act("10:30-12:00", "Sáng", "attraction",
                    HUE_SIGHT["lang_huong_thuy_xuan"],
                    "Làng hương Thủy Xuân - bé thích chụp ảnh", travel_from_prev=15),
                act("12:00-13:30", "Trưa", "food",
                    HUE_FOOD["banh_beo_nam_loc"],
                    "Ăn trưa Bánh bèo nậm lọc", travel_from_prev=15),
                act("13:30-15:00", "Trưa", "rest",
                    HUE_HOTEL["moonlight"],
                    "Nghỉ trưa dài", travel_from_prev=15),
                act("15:00-17:00", "Chiều", "attraction",
                    HUE_SIGHT["lang_lua"],
                    "Làng lụa Duy Trinh - mua sắm", travel_from_prev=15),
                act("17:00-18:30", "Chiều", "food",
                    HUE_FOOD["cafe_mat_biec"],
                    "Cafe Mắt Biếc", travel_from_prev=15),
                act("18:30-20:00", "Tối", "food",
                    HUE_FOOD["nem_lui_ba_ty"],
                    "Dinner Nem lụi bà Tý", travel_from_prev=10),
            ]
        },
        {
            "day": 4,
            "title": "Chợ Đông Ba - Bay về",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["che_hue"],
                    "Ăn sáng Chè Huế"),
                act("09:00-11:00", "Sáng", "shopping",
                    HUE_SIGHT["cho_dong_ba"],
                    "Chợ Đông Ba - mua mè xửng, nón bài thơ, hạt sen", travel_from_prev=15),
                act("11:00-12:00", "Sáng", "food",
                    HUE_FOOD["bun_hen_nang_suong"],
                    "Ăn Bún hến Nàng Sương", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "rest",
                    HUE_HOTEL["moonlight"],
                    "Check-out + nghỉ sảnh", travel_from_prev=10),
                act("13:30-15:00", "Trưa", "food",
                    HUE_FOOD["banh_khoai_hanh"],
                    "Bánh khoái Hạnh cuối", travel_from_prev=10),
                act("15:00-16:30", "Chiều", "food",
                    HUE_FOOD["che_ba_lien"],
                    "Chè cuối - bà Liên", travel_from_prev=10),
                act("16:30", "Chiều", "end", None,
                    "Ra sân bay - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 3900000,        # 3 đêm x 1.3M
        "food": 1500000,
        "tickets": 1000000,
        "transport": 1200000,
        "other": 300000,
    },
    "estimatedTotalPerPerson": 1580000,  # 7.9M / 5
}

# === HUEA01-s: 3N2Đ, 3-5tr, 1 người yên tĩnh ===
HUEA01 = {
    "id": "HUEA01-s",
    "city": "Hue",
    "title": "Huế Yên Tĩnh 3N2Đ - Solo healing sông Hương",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 1, "max": 1},
    "budgetPerPerson": {"min": 3000000, "max": 5000000},
    "style": "quiet",
    "hotel": HUE_HOTEL["hue_serene"],
    "days": [
        {
            "day": 1,
            "title": "Sông Hương sáng sớm - Đại Nội vắng",
            "activities": [
                act("06:00-07:30", "Sáng", "attraction",
                    HUE_SIGHT["song_huong"],
                    "Cafe sông Hương bình minh - Cafe Mắt Biếc"),
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["banh_canh_nam_pho"],
                    "Ăn sáng Bánh canh Nam Phổ"),
                act("09:00-10:00", "Sáng", "hotel",
                    HUE_HOTEL["hue_serene"],
                    "Check-in Hue Serene", travel_from_prev=15),
                act("10:00-12:00", "Sáng", "attraction",
                    HUE_SIGHT["chua_thien_mu"],
                    "Chùa Thiên Mụ - sáng yên tĩnh", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HUE_FOOD["com_hen_ba_hong"],
                    "Ăn trưa Cơm hến", travel_from_prev=15),
                act("13:30-15:30", "Trưa", "rest",
                    HUE_HOTEL["hue_serene"],
                    "Nghỉ trưa dài", travel_from_prev=15),
                act("15:30-17:30", "Chiều", "attraction",
                    HUE_SIGHT["dai_noi"],
                    "Đại Nội - lúc vắng", travel_from_prev=15),
                act("17:30-19:00", "Chiều", "attraction",
                    HUE_SIGHT["song_huong"],
                    "Sông Hương - hoàng hôn", travel_from_prev=10),
                act("19:00-20:30", "Tối", "food",
                    HUE_FOOD["bun_bo_ophuong"],
                    "Dinner Bún bò O Phượng", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Chùa - Làng hương - Spa",
            "activities": [
                act("07:00-08:00", "Sáng", "food",
                    HUE_FOOD["bun_bo_dong_ba"],
                    "Ăn sáng Bún bò Đông Ba"),
                act("08:30-10:30", "Sáng", "attraction",
                    HUE_SIGHT["lang_huong_thuy_xuan"],
                    "Làng hương Thủy Xuân - thiền", travel_from_prev=20),
                act("10:30-12:00", "Sáng", "attraction",
                    HUE_SIGHT["chua_thien_mu"],
                    "Chùa Thiên Mụ lần 2", travel_from_prev=15),
                act("12:00-13:30", "Trưa", "food",
                    HUE_FOOD["com_hen_nang_buoi"],
                    "Ăn trưa Cơm hến Nàng Buối", travel_from_prev=15),
                act("13:30-15:30", "Trưa", "rest",
                    HUE_HOTEL["hue_serene"],
                    "Nghỉ trưa + spa", travel_from_prev=15),
                act("15:30-17:30", "Chiều", "attraction",
                    HUE_HOTEL["indochine"],
                    "Spa tại Indochine Palace", travel_from_prev=15),
                act("17:30-19:00", "Chiều", "attraction",
                    HUE_SIGHT["song_huong"],
                    "Sông Hương - hoàng hôn yên tĩnh", travel_from_prev=10),
                act("19:00-21:00", "Tối", "food",
                    HUE_FOOD["ancient_hue"],
                    "Dinner Ancient Hue Restaurant - một mình", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Đại Nội - Chợ Đông Ba - Bay về",
            "activities": [
                act("07:00-08:00", "Sáng", "food",
                    HUE_FOOD["che_hue"],
                    "Ăn sáng Chè Huế"),
                act("08:30-10:30", "Sáng", "attraction",
                    HUE_SIGHT["dai_noi"],
                    "Đại Nội - sáng sớm vắng", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "attraction",
                    P(122),
                    "Bảo tàng Mỹ thuật Cung đình", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HUE_FOOD["com_hen_ba_hong"],
                    "Ăn trưa Cơm hến", travel_from_prev=10),
                act("13:30-15:00", "Trưa", "rest",
                    HUE_HOTEL["hue_serene"],
                    "Check-out + nghỉ sảnh", travel_from_prev=10),
                act("15:00-16:30", "Chiều", "food",
                    HUE_FOOD["che_ba_lien"],
                    "Café + chè cuối", travel_from_prev=10),
                act("16:30-18:00", "Chiều", "shopping",
                    HUE_SIGHT["cho_dong_ba"],
                    "Chợ Đông Ba - mua quà", travel_from_prev=10),
                act("18:00", "Tối", "end", None,
                    "Ra sân bay - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 2400000,
        "food": 700000,
        "tickets": 600000,
        "spa": 500000,
        "transport": 400000,
        "other": 200000,
    },
    "estimatedTotalPerPerson": 4800000,
}

# === HUEA02-s: 4N3Đ, 5-7.5tr, 1 người đam mê lịch sử ===
HUEA02 = {
    "id": "HUEA02-s",
    "city": "Hue",
    "title": "Huế History Lover 4N3Đ - Solo lịch sử chuyên sâu",
    "duration": "4 ngày 3 đêm",
    "durationDays": 4,
    "durationNights": 3,
    "travelers": {"min": 1, "max": 1},
    "budgetPerPerson": {"min": 5000000, "max": 7500000},
    "style": "history_deep",
    "hotel": HUE_HOTEL["hue_serene"],
    "days": [
        {
            "day": 1,
            "title": "Đại Nội chi tiết - Bảo tàng Cung đình",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HUE_FOOD["bun_bo_ophuong"],
                    "Ăn sáng Bún bò O Phượng"),
                act("09:00-13:00", "Cả ngày", "attraction",
                    HUE_SIGHT["dai_noi"],
                    "Đại Nội chi tiết 4h: Ngọ Môn, Điện Thái Hòa, Thế Miếu, Hiển Lâm Các, Cửu Đỉnh, Tử Cấm Thành", travel_from_prev=15),
                act("13:00-14:00", "Trưa", "food",
                    HUE_FOOD["com_hen_ba_hong"],
                    "Ăn trưa Cơm hến bà Hồng", travel_from_prev=15),
                act("14:00-15:30", "Trưa", "rest",
                    HUE_HOTEL["hue_serene"],
                    "Nghỉ trưa", travel_from_prev=15),
                act("15:30-17:30", "Chiều", "attraction",
                    P(122),  # Bảo tàng Cung đình
                    "Bảo tàng Cổ vật Cung đình Huế", travel_from_prev=15),
                act("18:30-20:00", "Tối", "food",
                    HUE_FOOD["ancient_hue"],
                    "Dinner Ancient Hue - cung đình Huế", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Lăng phía Nam: Tự Đức - Khải Định - Đồng Khánh",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HUE_FOOD["banh_canh_nam_pho"],
                    "Ăn sáng Bánh canh Nam Phổ"),
                act("09:00-11:30", "Sáng", "attraction",
                    HUE_SIGHT["lang_khai_dinh"],
                    "Lăng Khải Định - Gothic Đông Tây - 150k", travel_from_prev=20),
                act("11:30-13:00", "Trưa", "food",
                    HUE_FOOD["bun_bo_dong_ba"],
                    "Ăn trưa Bún bò Đông Ba", travel_from_prev=15),
                act("13:00-15:00", "Trưa", "attraction",
                    HUE_SIGHT["lang_tu_duc"],
                    "Lăng Tự Đức - 150k - thơ và kiến trúc", travel_from_prev=15),
                act("15:00-16:00", "Chiều", "rest",
                    HUE_HOTEL["hue_serene"],
                    "Nghỉ", travel_from_prev=20),
                act("16:00-18:00", "Chiều", "attraction",
                    HUE_SIGHT["doi_vong_canh"],
                    "Đồi Vọng Cảnh - view toàn cảnh lăng tẩm", travel_from_prev=20),
                act("18:30-20:00", "Tối", "food",
                    HUE_FOOD["nem_lui_ba_ty"],
                    "Dinner Nem lụi bà Tý", travel_from_prev=15),
            ]
        },
        {
            "day": 3,
            "title": "Minh Mạng - Nam Giao - Văn Miếu - Thiên Mụ",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HUE_FOOD["bun_bo_ophuong"],
                    "Ăn sáng Bún bò O Phượng"),
                act("09:00-12:00", "Sáng", "attraction",
                    HUE_SIGHT["lang_minh_mang"],
                    "Lăng Minh Mạng - 150k - sơn thủy hữu tình", travel_from_prev=20),
                act("12:00-13:30", "Trưa", "food",
                    HUE_FOOD["banh_beo_nam_loc"],
                    "Ăn trưa Bánh bèo nậm lọc", travel_from_prev=15),
                act("14:00-15:30", "Trưa", "attraction",
                    HUE_SIGHT["lang_lua"],
                    "Đàn Nam Giao - di tích lịch sử", travel_from_prev=15),
                act("15:30-16:30", "Chiều", "attraction",
                    HUE_SIGHT["trinh_duong"],
                    "Văn Miếu Huế", travel_from_prev=10),
                act("17:00-19:00", "Chiều", "attraction",
                    HUE_SIGHT["chua_thien_mu"],
                    "Chùa Thiên Mụ - hoàng hôn", travel_from_prev=10),
                act("19:00-21:00", "Tối", "food",
                    HUE_FOOD["ancient_hue"],
                    "Dinner Ancient Hue - royal cuisine", travel_from_prev=15),
            ]
        },
        {
            "day": 4,
            "title": "Cung An Định - Bảo tàng - Chợ Đông Ba - Bay về",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HUE_FOOD["che_hue"],
                    "Ăn sáng Chè Huế"),
                act("09:00-10:30", "Sáng", "attraction",
                    HUE_SIGHT["cung_an_dinh"],
                    "Cung An Định - 30k", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "attraction",
                    P(122),
                    "Bảo tàng Mỹ thuật Cung đình", travel_from_prev=10),
                act("12:00-13:30", "Trưa", "food",
                    HUE_FOOD["com_hen_ba_hong"],
                    "Ăn trưa Cơm hến", travel_from_prev=10),
                act("13:30-15:00", "Trưa", "rest",
                    HUE_HOTEL["hue_serene"],
                    "Check-out + nghỉ sảnh", travel_from_prev=10),
                act("15:00-16:30", "Chiều", "shopping",
                    HUE_SIGHT["cho_dong_ba"],
                    "Chợ Đông Ba - mua quà", travel_from_prev=15),
                act("16:30-18:00", "Chiều", "food",
                    HUE_FOOD["cafe_mat_biec"],
                    "Cafe lịch sử - Cafe Mắt Biếc", travel_from_prev=10),
                act("18:00", "Tối", "end", None,
                    "Ra sân bay - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 3600000,        # 3 đêm x 1.2M
        "food": 1100000,
        "tickets": 1500000,      # Đại Nội + 4 lăng + 2 bảo tàng
        "transport": 700000,
        "other": 200000,
    },
    "estimatedTotalPerPerson": 7100000,
}

# === HUEA03-s: 3N2Đ, 2.5-4tr, 1 sinh viên ===
HUEA03 = {
    "id": "HUEA03-s",
    "city": "Hue",
    "title": "Huế Budget 3N2Đ - Sinh viên tiết kiệm",
    "duration": "3 ngày 2 đêm",
    "durationDays": 3,
    "durationNights": 2,
    "travelers": {"min": 1, "max": 1},
    "budgetPerPerson": {"min": 2500000, "max": 4000000},
    "style": "student",
    "hotel": HUE_HOTEL["hue_backpackers"],  # 250k hostel
    "days": [
        {
            "day": 1,
            "title": "Đại Nội - Bún bò - Cơm hến",
            "activities": [
                act("08:00-09:00", "Sáng", "food",
                    HUE_FOOD["bun_bo_ophuong"],
                    "Bún bò O Phượng - 40k"),
                act("09:00-10:00", "Sáng", "hotel",
                    HUE_HOTEL["hue_backpackers"],
                    "Check-in Hue Backpackers Hostel", travel_from_prev=15),
                act("10:00-12:00", "Sáng", "attraction",
                    HUE_SIGHT["dai_noi"],
                    "Đại Nội - 200k", travel_from_prev=10),
                act("12:00-13:00", "Trưa", "food",
                    HUE_FOOD["com_hen_ba_hong"],
                    "Cơm hến - 20k", travel_from_prev=10),
                act("13:00-15:00", "Trưa", "rest",
                    HUE_HOTEL["hue_backpackers"],
                    "Nghỉ trưa", travel_from_prev=10),
                act("15:00-17:00", "Chiều", "attraction",
                    HUE_SIGHT["cau_truong_tien"],
                    "Cầu Trường Tiền - chụp ảnh FREE", travel_from_prev=10),
                act("17:00-18:30", "Chiều", "attraction",
                    HUE_SIGHT["song_huong"],
                    "Sông Hương dạo", travel_from_prev=10),
                act("18:30-20:00", "Tối", "food",
                    HUE_FOOD["che_hue"],
                    "Chè Huế + bánh - 30k", travel_from_prev=10),
                act("20:00-21:30", "Tối", "food",
                    HUE_FOOD["cafe_mat_biec"],
                    "Cafe sinh viên", travel_from_prev=10),
            ]
        },
        {
            "day": 2,
            "title": "Chùa Thiên Mụ - Lăng Tự Đức - Làng hương",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["bun_bo_dong_ba"],
                    "Ăn sáng Bún bò Đông Ba - 35k"),
                act("09:00-10:30", "Sáng", "attraction",
                    HUE_SIGHT["chua_thien_mu"],
                    "Chùa Thiên Mụ - FREE", travel_from_prev=15),
                act("10:30-12:00", "Sáng", "attraction",
                    HUE_SIGHT["lang_tu_duc"],
                    "Lăng Tự Đức - 150k (chụp ảnh bên ngoài FREE)", travel_from_prev=15),
                act("12:00-13:00", "Trưa", "food",
                    HUE_FOOD["com_hen_nang_buoi"],
                    "Cơm hến Nàng Buối - 15k", travel_from_prev=15),
                act("13:00-15:00", "Trưa", "rest",
                    HUE_HOTEL["hue_backpackers"],
                    "Nghỉ trưa", travel_from_prev=15),
                act("15:00-17:00", "Chiều", "attraction",
                    HUE_SIGHT["lang_huong_thuy_xuan"],
                    "Làng hương Thủy Xuân - FREE", travel_from_prev=15),
                act("17:00-18:30", "Chiều", "food",
                    HUE_FOOD["banh_khoai_hanh"],
                    "Ăn Bánh khoái Hạnh", travel_from_prev=15),
                act("18:30-20:00", "Tối", "food",
                    HUE_FOOD["che_ba_lien"],
                    "Chè bà Liên + cafe", travel_from_prev=10),
            ]
        },
        {
            "day": 3,
            "title": "Chợ Đông Ba - Bay về",
            "activities": [
                act("07:30-08:30", "Sáng", "food",
                    HUE_FOOD["banh_canh_nam_pho"],
                    "Bánh canh Nam Phổ - 35k"),
                act("09:00-11:00", "Sáng", "shopping",
                    HUE_SIGHT["cho_dong_ba"],
                    "Chợ Đông Ba - mua đặc sản", travel_from_prev=15),
                act("11:00-12:00", "Sáng", "food",
                    HUE_FOOD["bun_hen_nang_suong"],
                    "Ăn Bún hến Nàng Sương", travel_from_prev=10),
                act("12:00-13:00", "Trưa", "rest",
                    HUE_HOTEL["hue_backpackers"],
                    "Check-out + nghỉ sảnh", travel_from_prev=15),
                act("13:00-14:00", "Trưa", "food",
                    HUE_FOOD["com_tam_suon"],
                    "Cơm tấm sườn", travel_from_prev=10),
                act("14:00-15:30", "Chiều", "food",
                    HUE_FOOD["che_hue"],
                    "Chè cuối - 15k", travel_from_prev=10),
                act("15:30", "Chiều", "end", None,
                    "Ra sân bay - kết thúc"),
            ]
        }
    ],
    "costBreakdown": {
        "hotel": 500000,         # 2 đêm x 250k
        "food": 500000,
        "tickets": 350000,
        "transport": 300000,
        "other": 100000,
    },
    "estimatedTotalPerPerson": 1750000,
}

# ============================================================
# EXPORT
# ============================================================

ALL_PLANS = [
    DN01, DN02, DN03, DN04, DN05, DNA01, DNA02, DNA03,
    HOI01, HOI02, HOI03, HOI04, HOI05, HOA01, HOA02, HOA03,
    HUE01, HUE02, HUE03, HUE04, HUE05, HUEA01, HUEA02, HUEA03,
]

PLAN_OUT.parent.mkdir(parents=True, exist_ok=True)
PLAN_OUT.write_text(
    json.dumps({"version": "1.0", "plans": ALL_PLANS}, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
print(f"Wrote {len(ALL_PLANS)} plans to {PLAN_OUT}")
print(f"Total file size: {PLAN_OUT.stat().st_size:,} bytes")