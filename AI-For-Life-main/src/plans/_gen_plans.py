"""Generate 24 plans JSON file."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from _gen_core import L, ALL_HOTELS, get_loc, get_hotel


# ============================================================
# Helpers
# ============================================================
def act(time, period, type_, name, description, duration_min=None, cost=None, travel=None):
    if name in ALL_HOTELS:
        l = ALL_HOTELS[name]
    else:
        l = get_loc(name)
    cost_per_person = cost if cost is not None else l["avgCost"]
    duration = duration_min if duration_min is not None else l["durationMinutes"]
    out = {
        "time": time,
        "period": period,
        "type": type_,
        "location": l,
        "description": description,
        "costPerPerson": cost_per_person,
        "durationMinutes": duration,
    }
    if travel is not None:
        out["travelFromPreviousMinutes"] = travel
    return out


def day(n, title, items):
    """items = list of (time, period, type, name, desc, [duration], [cost], [travel])"""
    return {
        "day": n,
        "title": title,
        "activities": [act(*it) for it in items],
    }


def calc_breakdown(days, hotel_cost_per_night, nights, rooms_factor=1):
    """Calculate cost breakdown."""
    hotel_total = hotel_cost_per_night * nights * rooms_factor
    food = 0
    tickets = 0
    other = 0
    for d in days:
        for a in d["activities"]:
            if a["type"] == "hotel":
                continue
            cost = a.get("costPerPerson", 0)
            cat = (a.get("location") or {}).get("category", "")
            if cat in ["food"] or a.get("type") == "food":
                food += cost
            elif cat in ["museum", "sightseeing", "cultural", "wellness"] or a.get("type") == "wellness":
                tickets += cost
            else:
                other += cost
    transport = int((food + tickets + other) * 0.15)
    return {
        "hotel": int(hotel_total),
        "food": int(food),
        "tickets": int(tickets),
        "transport": int(transport),
        "other": int(other),
    }


def build_plan(pid, city, title, dur, dur_days, dur_nights, trav_min, trav_max,
               budget_min, budget_max, style, hotel_name, days, hotel_rooms=1):
    h = get_hotel(hotel_name)
    hotel_cost = h["avgCost"]
    breakdown = calc_breakdown(days, hotel_cost, dur_nights, hotel_rooms)
    total_per_person = (breakdown["hotel"] + breakdown["food"] + breakdown["tickets"] + breakdown["transport"] + breakdown["other"]) // max(1, trav_max)
    # Cap at budget_max
    estimated = min(budget_max, max(budget_min, total_per_person))
    return {
        "id": pid,
        "city": city,
        "title": title,
        "duration": dur,
        "durationDays": dur_days,
        "durationNights": dur_nights,
        "travelers": {"min": trav_min, "max": trav_max},
        "budgetPerPerson": {"min": budget_min, "max": budget_max},
        "style": style,
        "hotel": h,
        "days": days,
        "costBreakdown": breakdown,
        "estimatedTotalPerPerson": int(estimated),
    }


# ============================================================
# 24 PLANS
# ============================================================
PLANS = []

# --- ĐÀ NẴNG ---

# DN01-s: 3N2Đ, 4.5-6tr, 2-3 người, balanced
PLANS.append(build_plan(
    "DN01-s", "Da Nang", "Đà Nẵng First Trip 3N2Đ - Biển và thiên nhiên",
    "3 ngày 2 đêm", 3, 2, 2, 3, 4500000, 6000000, "balanced", "M Village Hotel Da Nang Centre",
    [
        day(1, "Trung tâm Đà Nẵng", [
            ("10:00-11:00", "Sáng", "beach", "Bãi biển Mỹ Khê", "Tắm biển sáng tại Mỹ Khê"),
            ("11:00-11:30", "Sáng", "food", "Mỳ Quảng 24/7", "Ăn sáng mỳ Quảng 24/7"),
            ("13:00-15:00", "Trưa", "hotel", "M Village Hotel Da Nang Centre", "Check-in / nghỉ ngơi", 60, 480),
            ("15:00-17:00", "Chiều", "sightseeing", "Bảo tàng Điêu khắc Chăm", "Tham quan Bảo tàng Điêu khắc Chăm"),
            ("18:00-19:00", "Tối", "food", "Madame Lân", "Ăn tối tại Madame Lân"),
            ("19:30-20:30", "Tối", "sightseeing", "Cầu Rồng", "Ngắm Cầu Rồng phun lửa cuối tuần"),
        ]),
        day(2, "Sơn Trà - Linh Ứng", [
            ("07:00-08:00", "Sáng", "food", "Bánh tráng cuốn thịt heo Bà Hường", "Ăn sáng bánh tráng cuốn thịt heo"),
            ("09:00-12:00", "Sáng", "cultural", "Chùa Linh Ứng - Sơn Trà", "Tham quan Chùa Linh Ứng - Sơn Trà"),
            ("12:30-14:00", "Trưa", "food", "Hải sản Bé Mặn", "Ăn trưa hải sản Bé Mặn"),
            ("15:00-17:00", "Chiều", "beach", "Bãi biển Mỹ Khê", "Tắm biển chiều tại Mỹ Khê"),
            ("18:00-19:30", "Tối", "food", "Chè Liên", "Ăn tối nhẹ tại Chè Liên"),
            ("19:30-21:00", "Tối", "shopping", "Chợ đêm Sơn Trà", "Dạo chợ đêm Sơn Trà"),
        ]),
        day(3, "Ngũ Hành Sơn", [
            ("07:30-08:30", "Sáng", "food", "Mỳ Quảng Bà Mua", "Ăn sáng Mỳ Quảng Bà Mua"),
            ("09:00-12:00", "Sáng", "sightseeing", "Ngũ Hành Sơn", "Leo núi Ngũ Hành Sơn - Thủy Sơn"),
            ("12:30-14:00", "Trưa", "food", "Mỳ Quảng 24/7", "Ăn trưa"),
            ("14:30-17:00", "Chiều", "beach", "Bãi biển Non Nước", "Tắm biển Non Nước"),
            ("18:00-19:00", "Tối", "shopping", "Chợ Hàn", "Mua đặc sản tại Chợ Hàn"),
            ("19:30-20:30", "Tối", "sightseeing", "Sông Hàn", "Dạo sông Hàn buổi tối"),
        ]),
    ]
))

# DN02-s: 3N2Đ, 5-7tr, 2 người couple, romantic
PLANS.append(build_plan(
    "DN02-s", "Da Nang", "Đà Nẵng Romantic 3N2Đ - Honeymoon cặp đôi",
    "3 ngày 2 đêm", 3, 2, 2, 2, 5000000, 7000000, "romantic", "Sala Danang Beach Hotel",
    [
        day(1, "Beach & Romantic Dinner", [
            ("08:00-09:00", "Sáng", "food", "Mỳ Quảng 24/7", "Ăn sáng mỳ Quảng"),
            ("10:00-12:00", "Sáng", "beach", "Bãi biển Mỹ Khê", "Tắm biển Mỹ Khê"),
            ("14:00-15:00", "Trưa", "hotel", "Sala Danang Beach Hotel", "Check-in Sala Danang Beach Hotel"),
            ("15:30-17:30", "Chiều", "sightseeing", "Bãi Bụt", "Đi Sơn Trà - Bãi Bụt"),
            ("18:30-20:30", "Tối", "food", "Madame Lân", "Dinner tại Madame Lân"),
            ("20:30-22:00", "Tối", "sightseeing", "Cầu Rồng", "Ngắm Cầu Rồng"),
        ]),
        day(2, "Bà Nà Hills", [
            ("08:00-08:30", "Sáng", "food", "Bánh xèo Bà Dưỡng", "Ăn sáng nhanh"),
            ("09:00-15:00", "Cả ngày", "sightseeing", "Sun World Bà Nà Hills", "Tham quan Sun World Bà Nà Hills - bao gồm Cầu Vàng"),
            ("12:00-13:30", "Trưa", "food", "Buffet Bà Nà Hills", "Ăn trưa buffet Bà Nà"),
            ("15:30-17:00", "Chiều", "hotel", "Sala Danang Beach Hotel", "Nghỉ ngơi tại khách sạn"),
            ("19:00-21:00", "Tối", "food", "Bữa tối couple tại Đà Nẵng", "Bữa tối couple tại Đà Nẵng"),
            ("21:00-22:00", "Tối", "sightseeing", "Sông Hàn", "Dạo bờ sông Hàn"),
        ]),
        day(3, "Couple Relax", [
            ("08:30-09:30", "Sáng", "food", "Mỳ Quảng Bà Mua", "Ăn sáng tại Mỳ Quảng Bà Mua"),
            ("10:00-12:00", "Sáng", "beach", "Bãi biển Mỹ Khê", "Tắm biển My Khe"),
            ("12:30-14:00", "Trưa", "food", "Bếp Cuốn Đà Nẵng", "Ăn trưa Bếp Cuốn Đà Nẵng"),
            ("14:30-17:00", "Chiều", "sightseeing", "Ngũ Hành Sơn", "Tham quan Ngũ Hành Sơn"),
            ("18:30-20:00", "Tối", "sightseeing", "Cầu Tình Yêu", "Đi dạo Cầu Tình Yêu + sông Hàn"),
            ("20:00-21:30", "Tối", "end", "Kết thúc", "Kết thúc chuyến đi"),
        ]),
    ]
))

# DN03-s: 4N3Đ, 6-8tr, 3-4 người trẻ
PLANS.append(build_plan(
    "DN03-s", "Da Nang", "Đà Nẵng Adventure 4N3Đ - Nhóm bạn trẻ năng động",
    "4 ngày 3 đêm", 4, 3, 3, 4, 6000000, 8000000, "adventure", "M Village Hotel Da Nang Centre",
    [
        day(1, "Mỹ Khê + Sơn Trà + Chợ đêm", [
            ("09:00-11:00", "Sáng", "beach", "Mỹ Khê", "Tắm biển Mỹ Khê"),
            ("11:30-12:30", "Trưa", "food", "Mỳ Quảng Bà Mua", "Ăn trưa Mỳ Quảng Bà Mua"),
            ("14:00-16:00", "Chiều", "hotel", "M Village Hotel Da Nang Centre", "Check-in khách sạn"),
            ("16:30-18:00", "Chiều", "sightseeing", "Bảo tàng Điêu khắc Chăm", "Bảo tàng Chăm"),
            ("19:00-20:30", "Tối", "food", "Helio Night Market", "Ăn tối + dạo chợ đêm"),
            ("20:30-22:00", "Tối", "sightseeing", "Cầu Rồng", "Ngắm Cầu Rồng"),
        ]),
        day(2, "Bà Nà Hills", [
            ("08:00-08:30", "Sáng", "food", "Bún chả cá Hờn", "Ăn sáng"),
            ("09:00-15:00", "Cả ngày", "sightseeing", "Sun World Bà Nà Hills", "Bà Nà Hills - Cầu Vàng + Fantasy Park"),
            ("12:00-13:30", "Trưa", "food", "Buffet Bà Nà Hills", "Buffet Bà Nà"),
            ("16:00-17:30", "Chiều", "hotel", "M Village Hotel Da Nang Centre", "Nghỉ ngơi"),
            ("18:00-20:00", "Tối", "food", "An Thượng", "Ăn tối food court An Thượng"),
            ("20:00-22:00", "Tối", "shopping", "Helio Night Market", "Đi chơi Helio"),
        ]),
        day(3, "Linh Ứng + Ngũ Hành Sơn", [
            ("07:00-08:00", "Sáng", "food", "Bánh tráng cuốn thịt heo Bà Hường", "Ăn sáng"),
            ("08:30-11:00", "Sáng", "cultural", "Chùa Linh Ứng - Sơn Trà", "Chùa Linh Ứng"),
            ("11:30-13:00", "Trưa", "food", "Hải sản Bé Mặn", "Ăn trưa hải sản"),
            ("14:00-16:30", "Chiều", "sightseeing", "Ngũ Hành Sơn", "Ngũ Hành Sơn"),
            ("17:00-18:30", "Chiều", "hotel", "M Village Hotel Da Nang Centre", "Nghỉ ngơi"),
            ("19:00-21:00", "Tối", "shopping", "Chợ Cồn", "Ăn tối + mua đồ tại Chợ Cồn"),
            ("21:00-22:00", "Tối", "food", "Chè Liên", "Ăn vặt"),
        ]),
        day(4, "Mỹ Khê + Bánh xèo", [
            ("08:00-09:00", "Sáng", "food", "Bánh xèo Bà Dưỡng", "Ăn sáng bánh xèo"),
            ("09:30-11:30", "Sáng", "beach", "Mỹ Khê", "Tắm biển sáng"),
            ("12:00-13:30", "Trưa", "food", "Bánh tráng cuốn thịt heo Bà Hường", "Ăn trưa"),
            ("14:00-16:00", "Chiều", "hotel", "M Village Hotel Da Nang Centre", "Trả phòng / nghỉ ngơi"),
            ("16:30-18:00", "Chiều", "sightseeing", "Sông Hàn", "Dạo sông Hàn + Cầu Rồng"),
            ("18:00-19:30", "Tối", "end", "Kết thúc", "Kết thúc chuyến đi"),
        ]),
    ]
))

# DN04-s: 3N2Đ, 3.5-5tr, thích ăn
PLANS.append(build_plan(
    "DN04-s", "Da Nang", "Đà Nẵng Food Trip 3N2Đ - Ăn gì cũng có",
    "3 ngày 2 đêm", 3, 2, 1, 2, 3500000, 5000000, "food", "Danang Beach Hotel",
    [
        day(1, "Food tour trung tâm", [
            ("07:00-08:00", "Sáng", "food", "Mỳ Quảng 24/7", "Ăn sáng mỳ Quảng"),
            ("10:00-11:30", "Sáng", "food", "Bánh tráng cuốn thịt heo Bà Hường", "Ăn bánh tráng cuốn"),
            ("13:00-15:00", "Trưa", "hotel", "Danang Beach Hotel", "Check-in khách sạn"),
            ("15:30-17:30", "Chiều", "shopping", "Chợ Cồn", "Khám phá Chợ Cồn"),
            ("18:00-20:00", "Tối", "food", "Hải sản Bé Mặn", "Ăn tối hải sản"),
        ]),
        day(2, "Ngũ Hành Sơn + Ẩm thực", [
            ("07:00-08:00", "Sáng", "food", "Bún chả cá Hờn", "Ăn sáng"),
            ("09:00-11:30", "Sáng", "sightseeing", "Ngũ Hành Sơn", "Leo núi Ngũ Hành Sơn"),
            ("12:00-13:30", "Trưa", "food", "Mỳ Quảng Bà Mua", "Ăn trưa"),
            ("14:00-15:30", "Chiều", "hotel", "Danang Beach Hotel", "Nghỉ ngơi"),
            ("16:00-18:00", "Chiều", "food", "Bánh xèo Bà Dưỡng", "Ăn chiều tại Bà Dưỡng"),
            ("19:00-21:00", "Tối", "food", "Hải sản Bé Mặn", "Ăn tối hải sản"),
        ]),
        day(3, "Bánh mì + beach", [
            ("07:00-08:00", "Sáng", "food", "Bánh mì Bà Lan", "Ăn sáng bánh mì"),
            ("09:00-11:00", "Sáng", "shopping", "Chợ Hàn", "Mua đặc sản Chợ Hàn"),
            ("11:30-13:00", "Trưa", "food", "Bánh bèo Bà Đỏ", "Ăn trưa"),
            ("14:00-17:00", "Chiều", "beach", "Mỹ Khê", "Tắm biển Mỹ Khê"),
            ("18:00-19:30", "Tối", "food", "Chè Liên", "Ăn tối + chè"),
        ]),
    ],
    hotel_rooms=1
))

# DN05-s: 4N3Đ, 6-9tr, gia đình
PLANS.append(build_plan(
    "DN05-s", "Da Nang", "Đà Nẵng Family 4N3Đ - Gia đình đa thế hệ",
    "4 ngày 3 đêm", 4, 3, 3, 5, 6000000, 9000000, "family", "Hyatt Regency Danang Resort & Spa",
    [
        day(1, "Mỹ Khê + City", [
            ("09:00-11:00", "Sáng", "beach", "Mỹ Khê", "Tắm biển Mỹ Khê"),
            ("12:00-13:30", "Trưa", "food", "Nhà hàng gia đình", "Ăn trưa"),
            ("14:00-15:00", "Trưa", "hotel", "Hyatt Regency Danang Resort & Spa", "Check-in Hyatt Regency"),
            ("15:30-17:30", "Chiều", "rest", "khách sạn nghỉ ngơi", "Nghỉ ngơi tại khách sạn"),
            ("18:00-20:00", "Tối", "food", "Nhà hàng gia đình", "Ăn tối"),
            ("20:00-22:00", "Tối", "sightseeing", "Sông Hàn", "Ngắm Cầu Rồng + sông Hàn"),
        ]),
        day(2, "Bà Nà Hills", [
            ("08:00-08:30", "Sáng", "food", "Bún chả cá Hờn", "Ăn sáng"),
            ("09:00-15:00", "Cả ngày", "sightseeing", "Sun World Bà Nà Hills", "Bà Nà Hills - Cầu Vàng"),
            ("12:00-13:30", "Trưa", "food", "Buffet Bà Nà Hills", "Buffet Bà Nà"),
            ("15:30-17:00", "Chiều", "hotel", "Hyatt Regency Danang Resort & Spa", "Nghỉ tại resort"),
            ("19:00-21:00", "Tối", "food", "Nhà hàng đặc sản", "Ăn tối"),
        ]),
        day(3, "Linh Ứng + Beach", [
            ("07:30-08:30", "Sáng", "food", "Bánh tráng cuốn thịt heo Bà Hường", "Ăn sáng"),
            ("09:00-11:30", "Sáng", "cultural", "Chùa Linh Ứng - Sơn Trà", "Chùa Linh Ứng"),
            ("12:00-13:30", "Trưa", "food", "Hải sản Bé Mặn", "Ăn trưa"),
            ("14:30-16:30", "Chiều", "shopping", "Vincom Plaza Đà Nẵng", "Đi Vincom Plaza"),
            ("17:00-18:00", "Chiều", "hotel", "Hyatt Regency Danang Resort & Spa", "Nghỉ ngơi"),
            ("18:30-20:00", "Tối", "sightseeing", "Sông Hàn", "Dạo sông Hàn"),
        ]),
        day(4, "Ngũ Hành Sơn", [
            ("07:00-08:00", "Sáng", "food", "Mỳ Quảng Bà Mua", "Ăn sáng"),
            ("08:30-11:00", "Sáng", "sightseeing", "Ngũ Hành Sơn", "Ngũ Hành Sơn"),
            ("11:30-13:00", "Trưa", "food", "Nhà hàng đặc sản", "Ăn trưa"),
            ("13:30-14:30", "Trưa", "hotel", "Hyatt Regency Danang Resort & Spa", "Trả phòng"),
            ("15:00-17:00", "Chiều", "beach", "Non Nước", "Tắm biển Non Nước"),
            ("17:30-19:00", "Tối", "end", "Kết thúc", "Kết thúc chuyến đi"),
        ]),
    ]
))

# DNA01-s: 3N2Đ, 3.5-5.5tr, 1 người yên tĩnh
PLANS.append(build_plan(
    "DNA01-s", "Da Nang", "Đà Nẵng Yên Tĩnh 3N2Đ - Solo healing",
    "3 ngày 2 đêm", 3, 2, 1, 1, 3500000, 5500000, "solo-quiet", "Sea Vista Hotel & Apartment",
    [
        day(1, "Beach + Cafe yên tĩnh", [
            ("06:00-08:00", "Sáng", "beach", "Mỹ Khê sáng sớm", "Đi bộ bãi biển Mỹ Khê buổi sớm"),
            ("08:30-09:30", "Sáng", "food", "Mỳ Quảng 24/7", "Ăn sáng"),
            ("11:00-13:00", "Trưa", "hotel", "Sea Vista Hotel & Apartment", "Check-in Sea Vista"),
            ("14:00-17:00", "Chiều", "sightseeing", "Bán đảo Sơn Trà", "Khám phá Sơn Trà"),
            ("18:00-19:30", "Tối", "food", "Café ven biển", "Café ven biển"),
        ]),
        day(2, "Linh Ứng + Spa", [
            ("07:00-08:00", "Sáng", "food", "Nhà hàng chay", "Ăn sáng chay"),
            ("08:30-11:30", "Sáng", "cultural", "Chùa Linh Ứng - Sơn Trà", "Linh Ứng"),
            ("12:00-13:30", "Trưa", "food", "Nhà hàng chay", "Ăn trưa chay"),
            ("14:30-17:00", "Chiều", "wellness", "Spa Đà Nẵng", "Spa thư giãn"),
            ("18:00-20:00", "Tối", "beach", "Mỹ Khê", "Ngồi biển Mỹ Khê buổi tối"),
        ]),
        day(3, "Ngũ Hành Sơn + Cafe", [
            ("07:00-08:00", "Sáng", "food", "Bánh xèo Bà Dưỡng", "Ăn sáng"),
            ("08:30-11:00", "Sáng", "sightseeing", "Ngũ Hành Sơn", "Ngũ Hành Sơn"),
            ("11:30-13:00", "Trưa", "food", "Bánh xèo Bà Dưỡng", "Ăn trưa"),
            ("14:00-17:00", "Chiều", "food", "Café yên tĩnh ven sông Hàn", "Café yên tĩnh ven sông Hàn"),
            ("17:30-19:00", "Tối", "sightseeing", "Sông Hàn", "Dạo sông Hàn"),
        ]),
    ]
))

# DNA02-s: 3N2Đ, 6-10tr, honeymoon
PLANS.append(build_plan(
    "DNA02-s", "Da Nang", "Đà Nẵng Honeymoon 3N2Đ - Resort view biển",
    "3 ngày 2 đêm", 3, 2, 2, 2, 6000000, 10000000, "honeymoon", "TIA Wellness Resort",
    [
        day(1, "Resort + Romantic dinner", [
            ("08:00-10:00", "Sáng", "beach", "Resort + biển", "Nghỉ dưỡng resort"),
            ("11:00-12:30", "Trưa", "food", "Lunch tại resort", "Lunch tại resort"),
            ("13:00-15:00", "Trưa", "hotel", "TIA Wellness Resort", "Check-in TIA Wellness"),
            ("16:00-18:00", "Chiều", "beach", "Mỹ Khê sunset", "Ngắm Mỹ Khê sunset"),
            ("19:00-21:30", "Tối", "food", "Romantic dinner ven biển", "Romantic dinner ven biển"),
        ]),
        day(2, "Bà Nà Hills + Spa", [
            ("08:00-08:30", "Sáng", "food", "Lunch tại resort", "Ăn sáng tại resort"),
            ("09:00-15:00", "Cả ngày", "sightseeing", "Sun World Bà Nà Hills", "Bà Nà Hills + Cầu Vàng"),
            ("12:00-13:30", "Trưa", "food", "Buffet Bà Nà Hills", "Buffet Bà Nà"),
            ("16:00-17:30", "Chiều", "hotel", "TIA Wellness Resort", "Nghỉ ngơi"),
            ("18:30-20:00", "Tối", "wellness", "Spa couple", "Spa couple"),
        ]),
        day(3, "Sơn Trà + Beach + Dinner", [
            ("08:00-09:00", "Sáng", "food", "Lunch tại resort", "Ăn sáng"),
            ("09:30-12:00", "Sáng", "sightseeing", "Bán đảo Sơn Trà", "Khám phá Sơn Trà"),
            ("12:30-14:00", "Trưa", "food", "Nhà hàng ven biển", "Ăn trưa ven biển"),
            ("14:30-17:00", "Chiều", "beach", "Bãi Bụt", "Tắm biển Bãi Bụt"),
            ("18:30-21:00", "Tối", "food", "Dinner cuối chuyến", "Dinner cuối chuyến"),
        ]),
    ]
))

# DNA03-s: 3N2Đ, 2.5-4tr, sinh viên
PLANS.append(build_plan(
    "DNA03-s", "Da Nang", "Đà Nẵng Budget 3N2Đ - Sinh viên tiết kiệm",
    "3 ngày 2 đêm", 3, 2, 1, 1, 2500000, 4000000, "budget-student", "Danang Backpackers Hostel",
    [
        day(1, "Mỳ Quảng + Beach", [
            ("07:00-08:00", "Sáng", "food", "Mỳ Quảng 24/7", "Ăn sáng"),
            ("09:00-11:00", "Sáng", "shopping", "Chợ Cồn", "Khám phá Chợ Cồn"),
            ("11:30-13:00", "Trưa", "food", "Quán cơm bình dân", "Ăn trưa bình dân"),
            ("14:00-15:00", "Trưa", "hotel", "Danang Backpackers Hostel", "Check-in hostel"),
            ("15:30-17:30", "Chiều", "beach", "Mỹ Khê", "Tắm biển Mỹ Khê"),
            ("18:00-20:00", "Tối", "sightseeing", "Cầu Rồng", "Ngắm Cầu Rồng + sông Hàn"),
        ]),
        day(2, "Ngũ Hành Sơn + Beach", [
            ("07:00-08:00", "Sáng", "food", "Bánh mì Bà Lan", "Ăn sáng bánh mì"),
            ("09:00-11:30", "Sáng", "sightseeing", "Ngũ Hành Sơn", "Ngũ Hành Sơn (vé SV)"),
            ("12:00-13:30", "Trưa", "food", "Quán cơm bình dân", "Ăn trưa bình dân"),
            ("14:30-17:00", "Chiều", "beach", "Non Nước", "Tắm biển Non Nước"),
            ("18:00-20:00", "Tối", "shopping", "Chợ đêm Sơn Trà", "Ăn tối chợ đêm"),
        ]),
        day(3, "Museum + Beach", [
            ("07:00-08:00", "Sáng", "food", "Bánh mì + café", "Ăn sáng"),
            ("09:00-11:30", "Sáng", "museum", "Bảo tàng Mỹ thuật Đà Nẵng", "Bảo tàng Mỹ thuật"),
            ("12:00-13:30", "Trưa", "food", "Mỳ Quảng Bà Mua", "Ăn trưa"),
            ("14:00-15:30", "Chiều", "hotel", "Danang Backpackers Hostel", "Trả phòng"),
            ("16:00-18:00", "Chiều", "sightseeing", "Sông Hàn", "Dạo sông Hàn"),
            ("18:00-19:30", "Tối", "end", "Kết thúc", "Kết thúc"),
        ]),
    ]
))

# ============================================================
# HỘI AN - 8 PLANS
# ============================================================

# HOI01-s: 3N2Đ, 3.5-5.5tr, gia đình 3-4 người
PLANS.append(build_plan(
    "HOI01-s", "Hoi An", "Hội An Heritage 3N2Đ - Gia đình phố cổ",
    "3 ngày 2 đêm", 3, 2, 3, 4, 3500000, 5500000, "family-heritage", "Hoang Trinh Hotel",
    [
        day(1, "Phố cổ + Chợ đêm", [
            ("08:00-09:30", "Sáng", "sightseeing", "Phố cổ Hội An", "Phố cổ Hội An"),
            ("11:00-13:30", "Trưa", "food", "Cơm gà Bà Buội", "Ăn trưa Cơm gà Bà Buội"),
            ("14:00-15:00", "Trưa", "hotel", "Hoang Trinh Hotel", "Check-in khách sạn"),
            ("15:30-17:30", "Chiều", "cultural", "Nhà cổ Tấn Ký", "Tham quan Nhà cổ Tấn Ký"),
            ("18:30-21:00", "Tối", "shopping", "Chợ đêm Hội An", "Dạo chợ đêm Hội An"),
        ]),
        day(2, "Rừng dừa + Trà Quế", [
            ("08:00-09:30", "Sáng", "sightseeing", "Rừng dừa Bảy Mẫu", "Tham quan Rừng dừa Bảy Mẫu"),
            ("11:00-13:30", "Trưa", "food", "Nhà hàng Cẩm Thanh", "Ăn trưa"),
            ("14:30-17:00", "Chiều", "sightseeing", "Trà Quế", "Tham quan Trà Quế"),
            ("18:00-19:30", "Tối", "food", "Phố cổ Hội An", "Ăn tối tại Phố cổ"),
            ("20:00-21:30", "Tối", "sightseeing", "Phố đèn lồng", "Ngắm Phố đèn lồng"),
        ]),
        day(3, "An Bàng + Café", [
            ("08:00-09:30", "Sáng", "beach", "An Bàng Beach", "An Bàng Beach"),
            ("10:30-12:00", "Trưa", "food", "Bánh mì Phượng", "Ăn trưa Bánh mì Phượng"),
            ("14:00-16:00", "Chiều", "food", "Café ven sông Hoài", "Café ven sông Hoài"),
            ("16:30-18:00", "Chiều", "hotel", "Hoang Trinh Hotel", "Trả phòng"),
            ("18:00-19:00", "Tối", "end", "Trả phòng", "Trả phòng + kết thúc"),
        ]),
    ]
))

# HOI02-s: 3N2Đ, 4.5-7tr, cặp đôi
PLANS.append(build_plan(
    "HOI02-s", "Hoi An", "Hội An Romantic 3N2Đ - Cặp đôi đèn lồng",
    "3 ngày 2 đêm", 3, 2, 2, 2, 4500000, 7000000, "romantic", "Allegro Hoi An",
    [
        day(1, "Phố cổ + Du thuyền", [
            ("08:00-09:30", "Sáng", "sightseeing", "Phố cổ Hội An", "Phố cổ Hội An"),
            ("11:30-13:30", "Trưa", "food", "Morning Glory", "Ăn trưa tại Morning Glory"),
            ("14:00-15:00", "Trưa", "hotel", "Allegro Hoi An", "Check-in Allegro Hoi An"),
            ("15:30-17:30", "Chiều", "cultural", "Nhà cổ Tấn Ký", "Nhà cổ Tấn Ký + Chùa Cầu"),
            ("18:00-19:30", "Tối", "sightseeing", "Du thuyền sông Hoài", "Du thuyền sông Hoài"),
            ("20:00-21:30", "Tối", "food", "Romantic dinner phố cổ", "Dinner phố cổ"),
        ]),
        day(2, "An Bàng + Trà Quế", [
            ("08:00-11:30", "Sáng", "beach", "An Bàng Beach", "Tắm biển An Bàng"),
            ("12:00-13:30", "Trưa", "food", "Nhà hàng An Bàng", "Ăn trưa"),
            ("14:30-17:00", "Chiều", "sightseeing", "Trà Quế", "Tham quan Trà Quế"),
            ("18:00-20:00", "Tối", "food", "Romantic dinner phố cổ", "Dinner phố cổ"),
        ]),
        day(3, "Thanh Hà + Bánh mì", [
            ("08:00-10:00", "Sáng", "sightseeing", "Làng gốm Thanh Hà", "Làng gốm Thanh Hà"),
            ("10:30-12:00", "Trưa", "food", "Bánh mì Phượng", "Ăn trưa"),
            ("14:00-16:30", "Chiều", "food", "Café Reaching Out", "Café yên tĩnh phố cổ"),
            ("17:00-18:00", "Chiều", "hotel", "Allegro Hoi An", "Trả phòng"),
            ("18:30-21:00", "Tối", "sightseeing", "Phố đèn lồng", "Phố đèn lồng"),
        ]),
    ]
))

# HOI03-s: 4N3Đ, 5-7tr, 3 người bạn
PLANS.append(build_plan(
    "HOI03-s", "Hoi An", "Hội An Beach & Old Town 4N3Đ - 3 người bạn",
    "4 ngày 3 đêm", 4, 3, 3, 3, 5000000, 7000000, "group-friends", "Hoi An Historic Hotel",
    [
        day(1, "Phố cổ + Cao lầu", [
            ("08:00-09:30", "Sáng", "sightseeing", "Phố cổ Hội An", "Phố cổ"),
            ("11:30-13:30", "Trưa", "food", "Cao lầu Bà Bé", "Ăn trưa Cao lầu Bà Bé"),
            ("14:00-15:00", "Trưa", "hotel", "Hoi An Historic Hotel", "Check-in"),
            ("15:30-17:30", "Chiều", "cultural", "Chùa Cầu", "Chùa Cầu + nhà cổ"),
            ("18:30-21:00", "Tối", "shopping", "Chợ đêm Hội An", "Chợ đêm Hội An"),
        ]),
        day(2, "Rừng dừa + Beach", [
            ("08:00-11:00", "Sáng", "sightseeing", "Rừng dừa Bảy Mẫu", "Rừng dừa Bảy Mẫu"),
            ("11:30-13:30", "Trưa", "food", "Nhà hàng Cẩm Thanh", "Ăn trưa"),
            ("14:30-17:00", "Chiều", "beach", "An Bàng Beach", "Tắm biển An Bàng"),
            ("18:00-21:00", "Tối", "food", "Pub/café phố cổ", "Pub/café phố cổ"),
        ]),
        day(3, "Thanh Hà + Kim Bồng", [
            ("08:00-09:30", "Sáng", "sightseeing", "Làng gốm Thanh Hà", "Làng gốm Thanh Hà"),
            ("10:00-11:30", "Sáng", "food", "Bánh mì Phượng", "Ăn sáng"),
            ("13:30-16:00", "Chiều", "sightseeing", "Làng mộc Kim Bồng", "Làng mộc Kim Bồng"),
            ("16:30-18:00", "Chiều", "hotel", "Hoi An Historic Hotel", "Nghỉ ngơi"),
            ("18:30-21:00", "Tối", "sightseeing", "Phố đèn lồng", "Phố đèn lồng"),
        ]),
        day(4, "Trà Quế + Café", [
            ("08:00-10:00", "Sáng", "sightseeing", "Trà Quế", "Trà Quế"),
            ("11:00-13:00", "Trưa", "food", "Cơm gà Bà Buội", "Ăn trưa"),
            ("14:00-16:00", "Chiều", "food", "Café ven sông Hoài", "Café sông Hoài"),
            ("16:30-18:00", "Chiều", "hotel", "Hoi An Historic Hotel", "Trả phòng"),
            ("18:30-19:30", "Tối", "end", "Trả phòng", "Kết thúc"),
        ]),
    ]
))

# HOI04-s: 3N2Đ, 3-5tr, thích ăn
PLANS.append(build_plan(
    "HOI04-s", "Hoi An", "Hội An Food Trip 3N2Đ - Ăn gì cũng có",
    "3 ngày 2 đêm", 3, 2, 1, 2, 3000000, 5000000, "food", "Hoi An Backpacker Hostel",
    [
        day(1, "Phố cổ + Bánh mì", [
            ("07:00-08:00", "Sáng", "food", "Bánh mì Phượng", "Ăn sáng"),
            ("11:00-13:30", "Trưa", "food", "Cơm gà Bà Buội", "Ăn trưa Cơm gà Bà Buội"),
            ("14:00-15:00", "Trưa", "hotel", "Hoi An Backpacker Hostel", "Check-in hostel"),
            ("15:30-17:30", "Chiều", "shopping", "Chợ Hội An", "Khám phá Chợ Hội An"),
            ("18:30-20:00", "Tối", "food", "Cao lầu Bà Bé", "Ăn tối Cao lầu Bà Bé"),
        ]),
        day(2, "Bánh bao + Trà Quế", [
            ("08:00-09:30", "Sáng", "food", "Bánh bao bánh vạc Hoa Hồng Trắng", "Ăn sáng"),
            ("11:30-13:30", "Trưa", "food", "Morning Glory", "Ăn trưa Morning Glory"),
            ("14:30-17:00", "Chiều", "sightseeing", "Trà Quế", "Trà Quế"),
            ("18:00-20:00", "Tối", "food", "Bánh xèo Hội An", "Ăn tối bánh xèo"),
        ]),
        day(3, "Cao lầu + Café", [
            ("07:00-08:30", "Sáng", "food", "Cao lầu Bà Bé", "Ăn sáng Cao lầu"),
            ("10:00-11:30", "Sáng", "food", "Bánh mì Madam Khánh", "Ăn Bánh mì Madam Khánh"),
            ("13:30-15:30", "Chiều", "shopping", "Chợ Hội An", "Mua sắm Chợ Hội An"),
            ("16:00-18:00", "Chiều", "food", "Chè Hội An", "Ăn Chè Hội An"),
            ("18:30-19:00", "Tối", "end", "Trả phòng", "Trả phòng + kết thúc"),
        ]),
    ]
))

# HOI05-s: 4N3Đ, 5-8tr, gia đình đa thế hệ
PLANS.append(build_plan(
    "HOI05-s", "Hoi An", "Hội An Family 4N3Đ - Gia đình đa thế hệ",
    "4 ngày 3 đêm", 4, 3, 4, 6, 5000000, 8000000, "family", "La Siesta Hoi An Resort & Spa",
    [
        day(1, "Phố cổ + Phố đèn lồng", [
            ("08:00-09:30", "Sáng", "sightseeing", "Phố cổ Hội An", "Phố cổ"),
            ("11:00-13:00", "Trưa", "food", "Nhà hàng gia đình", "Ăn trưa"),
            ("14:00-15:00", "Trưa", "hotel", "La Siesta Hoi An Resort & Spa", "Check-in La Siesta"),
            ("15:30-17:00", "Chiều", "cultural", "Nhà cổ Tấn Ký", "Nhà cổ Tấn Ký"),
            ("18:00-21:00", "Tối", "sightseeing", "Phố đèn lồng", "Phố đèn lồng"),
        ]),
        day(2, "Trà Quế + Phố cổ", [
            ("08:00-09:30", "Sáng", "sightseeing", "Trà Quế", "Trà Quế"),
            ("11:00-13:00", "Trưa", "food", "Nhà hàng Trà Quế", "Ăn trưa"),
            ("14:00-16:00", "Chiều", "rest", "khách sạn nghỉ ngơi", "Nghỉ ngơi khách sạn"),
            ("17:00-21:00", "Tối", "sightseeing", "Phố cổ Hội An", "Ăn tối + Phố cổ"),
        ]),
        day(3, "Rừng dừa + Beach + Dinner", [
            ("08:00-11:00", "Sáng", "sightseeing", "Rừng dừa Bảy Mẫu", "Rừng dừa Bảy Mẫu"),
            ("11:30-13:30", "Trưa", "food", "Nhà hàng Cẩm Thanh", "Ăn trưa"),
            ("14:30-17:00", "Chiều", "beach", "An Bàng Beach", "An Bàng Beach"),
            ("18:00-20:00", "Tối", "food", "Dinner gia đình", "Dinner gia đình"),
        ]),
        day(4, "Café + Mua sắm", [
            ("08:00-09:30", "Sáng", "food", "Café ven sông Hoài", "Café ven sông"),
            ("11:00-13:00", "Trưa", "food", "Cơm gà Bà Buội", "Ăn trưa"),
            ("14:00-16:00", "Chiều", "shopping", "Mua đặc sản", "Mua đặc sản"),
            ("16:30-18:00", "Chiều", "hotel", "La Siesta Hoi An Resort & Spa", "Trả phòng"),
            ("18:30-19:00", "Tối", "end", "Trả phòng", "Kết thúc"),
        ]),
    ]
))

# HOA01-s: 3N2Đ, 3-5tr, yên tĩnh
PLANS.append(build_plan(
    "HOA01-s", "Hoi An", "Hội An Yên Tĩnh 3N2Đ - Solo healing countryside",
    "3 ngày 2 đêm", 3, 2, 1, 1, 3000000, 5000000, "solo-quiet", "Hoi An Lodge",
    [
        day(1, "Café + Phố cổ", [
            ("07:00-08:30", "Sáng", "food", "Café ven sông Hoài", "Café ven sông Hoài"),
            ("10:00-12:00", "Sáng", "food", "Nhà hàng chay", "Ăn trưa chay"),
            ("13:00-14:00", "Trưa", "hotel", "Hoi An Lodge", "Check-in Hoi An Lodge"),
            ("14:30-17:00", "Chiều", "sightseeing", "Phố cổ Hội An", "Phố cổ yên tĩnh"),
            ("18:00-21:00", "Tối", "sightseeing", "Phố đèn lồng", "Đi bộ phố cổ"),
        ]),
        day(2, "An Bàng + Spa", [
            ("08:00-11:00", "Sáng", "beach", "An Bàng Beach", "Tắm biển An Bàng"),
            ("12:00-13:30", "Trưa", "food", "Nhà hàng An Bàng", "Ăn trưa"),
            ("14:30-17:00", "Chiều", "sightseeing", "Trà Quế", "Trà Quế"),
            ("18:00-20:00", "Tối", "wellness", "Spa Hội An", "Spa thư giãn"),
        ]),
        day(3, "Café + Làng gốm", [
            ("07:00-09:00", "Sáng", "food", "Café yên tĩnh", "Café yên tĩnh"),
            ("10:00-11:30", "Sáng", "food", "Bánh mì Phượng", "Ăn Bánh mì Phượng"),
            ("13:00-16:00", "Chiều", "sightseeing", "Làng gốm Thanh Hà", "Làng gốm Thanh Hà"),
            ("16:30-18:00", "Chiều", "hotel", "Hoi An Lodge", "Trả phòng"),
            ("18:30-19:00", "Tối", "end", "Trả phòng", "Kết thúc"),
        ]),
    ]
))

# HOA02-s: 3N2Đ, 4-6.5tr, photography
PLANS.append(build_plan(
    "HOA02-s", "Hoi An", "Hội An Creative 3N2Đ - Photographer aesthetic",
    "3 ngày 2 đêm", 3, 2, 1, 2, 4000000, 6500000, "photography", "Allegro Hoi An",
    [
        day(1, "Chùa Cầu + Phố đèn lồng", [
            ("06:00-08:00", "Sáng", "cultural", "Chùa Cầu", "Chụp Chùa Cầu lúc bình minh"),
            ("10:00-11:30", "Sáng", "food", "Morning Glory", "Ăn trưa"),
            ("13:30-16:30", "Chiều", "cultural", "Nhà cổ Tấn Ký", "Chụp nhà cổ Tấn Ký"),
            ("17:30-21:00", "Tối", "sightseeing", "Phố đèn lồng", "Phố đèn lồng - golden hour"),
        ]),
        day(2, "Trà Quế + Cẩm Thanh", [
            ("07:00-09:30", "Sáng", "sightseeing", "Trà Quế", "Chụp Trà Quế lúc sáng sớm"),
            ("11:00-13:00", "Trưa", "food", "Nhà hàng Cẩm Thanh", "Ăn trưa"),
            ("14:00-17:30", "Chiều", "sightseeing", "Rừng dừa Bảy Mẫu", "Chụp Rừng dừa"),
            ("18:30-20:00", "Tối", "sightseeing", "Sông Hoài", "Sông Hoài sunset"),
        ]),
        day(3, "Thanh Hà + An Bàng sunset", [
            ("08:00-10:00", "Sáng", "sightseeing", "Làng gốm Thanh Hà", "Chụp Thanh Hà"),
            ("10:30-12:00", "Trưa", "food", "Bánh mì Phượng", "Ăn Bánh mì Phượng"),
            ("14:00-17:30", "Chiều", "beach", "An Bàng Beach", "An Bàng sunset"),
            ("18:30-20:00", "Tối", "sightseeing", "Phố đèn lồng", "Phố cổ"),
        ]),
    ]
))

# HOA03-s: 3N2Đ, 2.5-4tr, backpacker
PLANS.append(build_plan(
    "HOA03-s", "Hoi An", "Hội An Backpacker 3N2Đ - Solo tiết kiệm",
    "3 ngày 2 đêm", 3, 2, 1, 1, 2500000, 4000000, "budget-backpacker", "Hoi An Backpacker Hostel",
    [
        day(1, "Bánh mì + Phố cổ", [
            ("07:00-08:00", "Sáng", "food", "Bánh mì Phượng", "Ăn sáng"),
            ("10:00-11:30", "Sáng", "shopping", "Chợ Hội An", "Chợ Hội An"),
            ("12:00-13:30", "Trưa", "food", "Nhà hàng gia đình", "Ăn trưa bình dân"),
            ("14:00-15:00", "Trưa", "hotel", "Hoi An Backpacker Hostel", "Check-in hostel"),
            ("15:30-17:30", "Chiều", "sightseeing", "Phố cổ Hội An", "Phố cổ"),
            ("18:30-20:00", "Tối", "shopping", "Chợ đêm Hội An", "Chợ đêm"),
        ]),
        day(2, "Trà Quế + An Bàng + Cao lầu", [
            ("08:00-11:00", "Sáng", "sightseeing", "Trà Quế", "Đạp xe Trà Quế"),
            ("11:30-13:30", "Trưa", "food", "Nhà hàng Trà Quế", "Ăn trưa"),
            ("14:30-17:00", "Chiều", "beach", "An Bàng Beach", "Tắm biển An Bàng"),
            ("18:00-20:00", "Tối", "food", "Cao lầu Bà Bé", "Ăn tối Cao lầu"),
        ]),
        day(3, "Thanh Hà + Café", [
            ("08:00-10:00", "Sáng", "sightseeing", "Làng gốm Thanh Hà", "Làng gốm Thanh Hà"),
            ("10:30-11:30", "Sáng", "food", "Bánh mì Madam Khánh", "Ăn sáng"),
            ("13:30-15:30", "Chiều", "food", "Café phố cổ", "Café phố cổ"),
            ("16:00-17:00", "Chiều", "hotel", "Hoi An Backpacker Hostel", "Trả phòng"),
            ("17:30-18:30", "Tối", "end", "Trả phòng", "Kết thúc"),
        ]),
    ]
))

# ============================================================
# HUẾ - 8 PLANS
# ============================================================

# HUE01-s: 3N2Đ, 3.5-5.5tr, gia đình
PLANS.append(build_plan(
    "HUE01-s", "Hue", "Huế Imperial Heritage 3N2Đ - Gia đình cố đô",
    "3 ngày 2 đêm", 3, 2, 3, 4, 3500000, 5500000, "family-heritage", "Hue Serene Palace Hotel",
    [
        day(1, "Đại Nội + Phố đi bộ", [
            ("08:00-09:30", "Sáng", "cultural", "Đại Nội Huế", "Đại Nội Huế"),
            ("10:30-12:00", "Sáng", "food", "Bún bò Huế Hạnh", "Ăn trưa"),
            ("13:00-14:00", "Trưa", "hotel", "Hue Serene Palace Hotel", "Check-in Hue Serene Palace"),
            ("14:30-16:30", "Chiều", "rest", "Nghỉ khách sạn", "Nghỉ ngơi"),
            ("17:00-19:30", "Tối", "sightseeing", "Phố đi bộ Nguyễn Đình Chiểu", "Phố đi bộ Nguyễn Đình Chiểu"),
        ]),
        day(2, "Lăng Minh Mạng + Chùa Thiên Mụ", [
            ("07:30-09:30", "Sáng", "cultural", "Lăng Minh Mạng", "Lăng Minh Mạng"),
            ("11:00-13:00", "Trưa", "food", "Cơm niêu", "Ăn trưa"),
            ("14:00-16:30", "Chiều", "cultural", "Chùa Thiên Mụ", "Chùa Thiên Mụ"),
            ("17:00-19:00", "Tối", "sightseeing", "Sông Hương", "Dạo sông Hương"),
        ]),
        day(3, "Chợ Đông Ba + Cung An Định", [
            ("08:00-10:00", "Sáng", "shopping", "Chợ Đông Ba", "Chợ Đông Ba"),
            ("11:00-13:00", "Trưa", "food", "Bánh bèo Bà Đỏ", "Ăn trưa"),
            ("14:00-16:00", "Chiều", "cultural", "Cung An Định", "Cung An Định"),
            ("16:30-18:00", "Chiều", "hotel", "Hue Serene Palace Hotel", "Trả phòng"),
            ("18:30-19:30", "Tối", "end", "Kết thúc", "Kết thúc chuyến đi"),
        ]),
    ]
))

# HUE02-s: 3N2Đ, 3-4.5tr, thích ăn
PLANS.append(build_plan(
    "HUE02-s", "Hue", "Huế Food Trip 3N2Đ - Ăn vặt cố đô",
    "3 ngày 2 đêm", 3, 2, 1, 2, 3000000, 4500000, "food", "Hue Serene Palace Hotel",
    [
        day(1, "Food tour", [
            ("07:00-08:00", "Sáng", "food", "Bún bò Huế Hạnh", "Ăn sáng Bún bò"),
            ("10:00-11:30", "Sáng", "food", "Bánh bèo Bà Đỏ", "Ăn Bánh bèo"),
            ("13:00-14:30", "Trưa", "shopping", "Chợ Đông Ba", "Chợ Đông Ba"),
            ("15:00-16:30", "Chiều", "hotel", "Hue Serene Palace Hotel", "Check-in"),
            ("17:00-19:00", "Tối", "food", "Chè Huế", "Ăn tối + Chè"),
        ]),
        day(2, "Đại Nội + Nem lụi", [
            ("07:00-08:00", "Sáng", "food", "Cơm hến Hoa Đông", "Ăn sáng Cơm hến"),
            ("10:00-11:30", "Sáng", "food", "Bún thịt nướng", "Ăn trưa"),
            ("13:30-17:00", "Chiều", "cultural", "Đại Nội Huế", "Đại Nội"),
            ("18:00-20:00", "Tối", "food", "Nem lụi Huế", "Ăn tối Nem lụi"),
        ]),
        day(3, "Thiên Mụ + Bánh khoái", [
            ("07:00-08:30", "Sáng", "food", "Bánh khoái Hồng Mai", "Ăn sáng Bánh khoái"),
            ("10:00-11:30", "Sáng", "food", "Bánh lọc Huế", "Ăn trưa"),
            ("13:30-16:30", "Chiều", "cultural", "Chùa Thiên Mụ", "Chùa Thiên Mụ"),
            ("17:30-19:00", "Tối", "shopping", "Chợ Đông Ba", "Ăn tối + Chợ Đông Ba"),
        ]),
    ]
))

# HUE03-s: 3N2Đ, 3.5-5tr, người lớn tuổi
PLANS.append(build_plan(
    "HUE03-s", "Hue", "Huế Slow Travel 3N2Đ - Cùng người lớn tuổi",
    "3 ngày 2 đêm", 3, 2, 2, 4, 3500000, 5000000, "family-elderly", "Hue Serene Palace Hotel",
    [
        day(1, "Đại Nội + Sông Hương", [
            ("08:00-09:30", "Sáng", "cultural", "Đại Nội Huế", "Đại Nội"),
            ("11:00-12:30", "Sáng", "food", "Nhà hàng cơm Huế", "Ăn trưa nhà hàng Huế"),
            ("13:30-14:30", "Trưa", "hotel", "Hue Serene Palace Hotel", "Check-in"),
            ("15:00-16:30", "Chiều", "rest", "Nghỉ khách sạn", "Nghỉ ngơi"),
            ("17:00-19:00", "Tối", "sightseeing", "Sông Hương", "Dạo sông Hương"),
        ]),
        day(2, "Chùa Thiên Mụ + Lăng Minh Mạng", [
            ("07:30-09:00", "Sáng", "cultural", "Chùa Thiên Mụ", "Chùa Thiên Mụ"),
            ("10:30-12:00", "Sáng", "food", "Cơm niêu", "Ăn trưa"),
            ("13:30-16:30", "Chiều", "cultural", "Lăng Minh Mạng", "Lăng Minh Mạng"),
            ("17:00-18:30", "Chiều", "hotel", "Hue Serene Palace Hotel", "Nghỉ ngơi"),
            ("19:00-19:30", "Tối", "end", "Nghỉ", "Nghỉ"),
        ]),
        day(3, "Chợ Đông Ba + Café", [
            ("08:00-10:00", "Sáng", "shopping", "Chợ Đông Ba", "Chợ Đông Ba"),
            ("11:00-12:30", "Trưa", "food", "Bánh bèo Bà Đỏ", "Ăn trưa"),
            ("14:00-16:00", "Chiều", "food", "Café ven sông Hương", "Café sông Hương"),
            ("16:30-18:00", "Chiều", "hotel", "Hue Serene Palace Hotel", "Trả phòng"),
            ("18:30-19:00", "Tối", "end", "Kết thúc", "Kết thúc"),
        ]),
    ]
))

# HUE04-s: 4N3Đ, 5-7tr, 1 người thích lịch sử
PLANS.append(build_plan(
    "HUE04-s", "Hue", "Huế History Explorer 4N3Đ - Solo đi sâu lịch sử",
    "4 ngày 3 đêm", 4, 3, 1, 1, 5000000, 7000000, "solo-history", "Eldora Hotel",
    [
        day(1, "Đại Nội + Sông Hương", [
            ("07:00-08:30", "Sáng", "cultural", "Đại Nội Huế", "Đại Nội – Ngọ Môn"),
            ("09:30-11:00", "Sáng", "food", "Bún bò Huế Hạnh", "Ăn trưa"),
            ("12:00-15:30", "Chiều", "cultural", "Điện Thái Hòa", "Điện Thái Hòa + Tử Cấm Thành"),
            ("16:30-18:00", "Chiều", "sightseeing", "Sông Hương", "Sông Hương"),
            ("18:30-19:30", "Tối", "hotel", "Eldora Hotel", "Check-in Eldora Hotel"),
        ]),
        day(2, "Lăng Minh Mạng + Khải Định", [
            ("07:00-09:30", "Sáng", "cultural", "Lăng Minh Mạng", "Lăng Minh Mạng"),
            ("11:00-12:30", "Sáng", "food", "Nhà hàng Huế", "Ăn trưa"),
            ("13:30-16:30", "Chiều", "cultural", "Lăng Khải Định", "Lăng Khải Định"),
            ("17:00-19:00", "Tối", "food", "Café lịch sử/phố cổ", "Café lịch sử"),
        ]),
        day(3, "Tự Đức + Cung An Định", [
            ("07:00-09:30", "Sáng", "cultural", "Lăng Tự Đức", "Lăng Tự Đức"),
            ("11:00-12:30", "Sáng", "food", "Bánh bèo Bà Đỏ", "Ăn trưa"),
            ("13:30-16:00", "Chiều", "cultural", "Cung An Định", "Cung An Định"),
            ("17:00-19:00", "Tối", "sightseeing", "Phố đi bộ", "Phố đi bộ"),
        ]),
        day(4, "Bảo tàng + Đàn Nam Giao", [
            ("07:00-08:30", "Sáng", "museum", "Bảo tàng Cổ vật Cung đình Huế", "Bảo tàng Cổ vật"),
            ("10:00-11:30", "Sáng", "food", "Cơm hến Hoa Đông", "Ăn trưa"),
            ("13:30-16:00", "Chiều", "cultural", "Đàn Nam Giao", "Đàn Nam Giao"),
            ("16:30-18:00", "Chiều", "hotel", "Eldora Hotel", "Trả phòng"),
            ("18:30-19:00", "Tối", "end", "Kết thúc", "Kết thúc"),
        ]),
    ]
))

# HUE05-s: 4N3Đ, 5-8tr, gia đình đa thế hệ
PLANS.append(build_plan(
    "HUE05-s", "Hue", "Huế Family 4N3Đ - Gia đình đa thế hệ",
    "4 ngày 3 đêm", 4, 3, 4, 6, 5000000, 8000000, "family", "Moonlight Hotel Hue",
    [
        day(1, "Đại Nội + Sông Hương", [
            ("08:00-09:30", "Sáng", "cultural", "Đại Nội Huế", "Đại Nội"),
            ("11:00-12:30", "Sáng", "food", "Nhà hàng Huế", "Ăn trưa"),
            ("13:30-14:30", "Trưa", "hotel", "Moonlight Hotel Hue", "Check-in"),
            ("15:00-16:30", "Chiều", "rest", "Nghỉ khách sạn", "Nghỉ ngơi"),
            ("17:00-19:00", "Tối", "sightseeing", "Sông Hương", "Dạo sông Hương"),
        ]),
        day(2, "Chùa + Lăng Minh Mạng", [
            ("07:30-09:30", "Sáng", "cultural", "Chùa Thiên Mụ", "Chùa Thiên Mụ"),
            ("11:00-13:00", "Trưa", "food", "Cơm niêu", "Ăn trưa"),
            ("14:00-16:30", "Chiều", "cultural", "Lăng Minh Mạng", "Lăng Minh Mạng"),
            ("17:00-18:30", "Chiều", "hotel", "Moonlight Hotel Hue", "Nghỉ ngơi"),
        ]),
        day(3, "Lăng Khải Định + Làng hương", [
            ("07:30-09:30", "Sáng", "cultural", "Lăng Khải Định", "Lăng Khải Định"),
            ("10:30-12:00", "Sáng", "food", "Bún bò Huế Hạnh", "Ăn trưa"),
            ("14:00-16:30", "Chiều", "sightseeing", "Làng hương Thủy Xuân", "Làng hương"),
            ("17:00-19:00", "Tối", "food", "Café", "Café"),
        ]),
        day(4, "Chợ + Cung An Định", [
            ("08:00-10:00", "Sáng", "shopping", "Chợ Đông Ba", "Chợ Đông Ba"),
            ("11:00-12:30", "Sáng", "food", "Bánh bèo Bà Đỏ", "Ăn trưa"),
            ("14:00-16:00", "Chiều", "cultural", "Cung An Định", "Cung An Định"),
            ("16:30-18:00", "Chiều", "hotel", "Moonlight Hotel Hue", "Trả phòng"),
            ("18:30-19:00", "Tối", "end", "Kết thúc", "Kết thúc"),
        ]),
    ]
))

# HUEA01-s: 3N2Đ, 3-5tr, yên tĩnh
PLANS.append(build_plan(
    "HUEA01-s", "Hue", "Huế Yên Tĩnh 3N2Đ - Solo healing sông Hương",
    "3 ngày 2 đêm", 3, 2, 1, 1, 3000000, 5000000, "solo-quiet", "Hue Serene Palace Hotel",
    [
        day(1, "Café + Đại Nội", [
            ("07:00-08:30", "Sáng", "food", "Café ven sông Hương", "Café ven sông Hương"),
            ("10:00-11:30", "Sáng", "food", "Nhà hàng chay", "Ăn trưa chay"),
            ("13:00-14:00", "Trưa", "hotel", "Hue Serene Palace Hotel", "Check-in"),
            ("14:30-17:00", "Chiều", "cultural", "Đại Nội Huế", "Đại Nội"),
            ("17:30-19:00", "Tối", "sightseeing", "Sông Hương", "Sông Hương"),
        ]),
        day(2, "Chùa + Làng hương", [
            ("07:30-09:00", "Sáng", "cultural", "Chùa Thiên Mụ", "Chùa Thiên Mụ"),
            ("10:30-12:00", "Sáng", "food", "Cơm hến Hoa Đông", "Ăn trưa"),
            ("14:00-16:30", "Chiều", "sightseeing", "Làng hương Thủy Xuân", "Làng hương"),
            ("17:00-19:00", "Tối", "food", "Café yên tĩnh", "Café yên tĩnh"),
        ]),
        day(3, "Công viên + Café", [
            ("07:00-08:30", "Sáng", "sightseeing", "Công viên ven sông", "Công viên ven sông"),
            ("09:30-11:00", "Sáng", "food", "Bún bò Huế Hạnh", "Ăn trưa"),
            ("13:00-15:30", "Chiều", "food", "Café phố cổ", "Café phố cổ"),
            ("16:00-17:30", "Chiều", "hotel", "Hue Serene Palace Hotel", "Trả phòng"),
            ("18:00-19:00", "Tối", "end", "Kết thúc", "Kết thúc"),
        ]),
    ]
))

# HUEA02-s: 4N3Đ, 5-7.5tr, đam mê lịch sử
PLANS.append(build_plan(
    "HUEA02-s", "Hue", "Huế History Lover 4N3Đ - Solo lịch sử chuyên sâu",
    "4 ngày 3 đêm", 4, 3, 1, 1, 5000000, 7500000, "solo-history-deep", "Eldora Hotel",
    [
        day(1, "Hoàng thành", [
            ("07:00-08:30", "Sáng", "cultural", "Đại Nội Huế", "Ngọ Môn – Đại Nội"),
            ("09:30-11:00", "Sáng", "food", "Bún bò Huế Hạnh", "Ăn trưa"),
            ("12:00-15:30", "Chiều", "cultural", "Điện Thái Hòa", "Điện Thái Hòa – Tử Cấm Thành"),
            ("16:30-18:00", "Chiều", "sightseeing", "Sông Hương", "Sông Hương"),
            ("18:30-19:30", "Tối", "hotel", "Eldora Hotel", "Check-in Eldora Hotel"),
        ]),
        day(2, "Minh Mạng + Khải Định", [
            ("07:00-09:30", "Sáng", "cultural", "Lăng Minh Mạng", "Lăng Minh Mạng"),
            ("11:00-12:30", "Sáng", "food", "Nhà hàng Huế", "Ăn trưa"),
            ("13:30-16:30", "Chiều", "cultural", "Lăng Khải Định", "Lăng Khải Định"),
            ("17:00-19:00", "Tối", "food", "Café", "Café lịch sử"),
        ]),
        day(3, "Tự Đức + Đồng Khánh", [
            ("07:00-09:30", "Sáng", "cultural", "Lăng Tự Đức", "Lăng Tự Đức"),
            ("10:30-12:00", "Sáng", "food", "Cơm hến Hoa Đông", "Ăn trưa"),
            ("13:30-16:00", "Chiều", "cultural", "Lăng Đồng Khánh", "Lăng Đồng Khánh"),
            ("17:00-19:00", "Tối", "sightseeing", "Phố đi bộ", "Phố đi bộ"),
        ]),
        day(4, "Di tích bổ sung", [
            ("07:30-09:00", "Sáng", "cultural", "Cung An Định", "Cung An Định"),
            ("10:00-11:30", "Sáng", "food", "Bánh bèo Bà Đỏ", "Ăn trưa"),
            ("13:30-16:00", "Chiều", "cultural", "Đàn Nam Giao", "Đàn Nam Giao"),
            ("16:30-18:00", "Chiều", "hotel", "Eldora Hotel", "Trả phòng"),
            ("18:30-19:00", "Tối", "end", "Kết thúc", "Kết thúc"),
        ]),
    ]
))

# HUEA03-s: 3N2Đ, 2.5-4tr, sinh viên
PLANS.append(build_plan(
    "HUEA03-s", "Hue", "Huế Budget 3N2Đ - Sinh viên tiết kiệm",
    "3 ngày 2 đêm", 3, 2, 1, 1, 2500000, 4000000, "budget-student", "Hue Backpackers Hostel",
    [
        day(1, "Bún bò + Đại Nội", [
            ("07:00-08:00", "Sáng", "food", "Bún bò Huế Hạnh", "Ăn sáng"),
            ("10:00-11:30", "Sáng", "food", "Cơm bình dân", "Ăn trưa"),
            ("13:00-14:00", "Trưa", "hotel", "Hue Backpackers Hostel", "Check-in hostel"),
            ("14:30-17:00", "Chiều", "cultural", "Đại Nội Huế", "Đại Nội (vé SV)"),
            ("17:30-19:00", "Tối", "sightseeing", "Sông Hương", "Sông Hương"),
        ]),
        day(2, "Chùa + Chợ + Chè", [
            ("07:30-09:00", "Sáng", "cultural", "Chùa Thiên Mụ", "Chùa Thiên Mụ"),
            ("10:30-12:00", "Sáng", "food", "Cơm hến Hoa Đông", "Ăn trưa"),
            ("13:30-16:00", "Chiều", "shopping", "Chợ Đông Ba", "Chợ Đông Ba"),
            ("17:00-19:00", "Tối", "food", "Chè Huế", "Ăn tối Chè"),
        ]),
        day(3, "Bánh bèo + Làng hương", [
            ("07:00-08:30", "Sáng", "food", "Bánh bèo Bà Đỏ", "Ăn sáng"),
            ("10:00-11:30", "Sáng", "food", "Bún thịt nướng", "Ăn trưa"),
            ("13:30-16:00", "Chiều", "sightseeing", "Làng hương Thủy Xuân", "Làng hương"),
            ("16:30-17:30", "Chiều", "hotel", "Hue Backpackers Hostel", "Trả phòng"),
            ("18:00-19:00", "Tối", "end", "Kết thúc", "Kết thúc"),
        ]),
    ]
))

# Save all 24 plans
if __name__ == "__main__":
    output = {"version": "1.0", "plans": PLANS}
    out_path = os.path.join(os.path.dirname(__file__), "plans_simple_new.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("Wrote", len(PLANS), "plans to", out_path)