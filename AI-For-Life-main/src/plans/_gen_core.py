"""Location + hotel registry for 24 plans generator."""

def loc(name, category, city, address, rating, review_count, open_, close, cost, price, tags, duration=60):
    return {
        "name": name,
        "category": category,
        "city": city,
        "address": address,
        "rating": rating,
        "reviewCount": review_count,
        "openingTime": open_,
        "closingTime": close,
        "avgCost": cost,
        "priceLevel": price,
        "tags": tags,
        "durationMinutes": duration,
    }


# HOTELS
ALL_HOTELS = {}

# Da Nang hotels
ALL_HOTELS["M Village Hotel Da Nang Centre"] = loc("M Village Hotel Da Nang Centre", "hotel", "Da Nang",
    "115 Nguyen Van Linh, Hai Chau, Da Nang", 4.5, 480, "00:00", "23:59", 800000, "$$",
    "hotel;modern;central;city", 1440)
ALL_HOTELS["Sala Danang Beach Hotel"] = loc("Sala Danang Beach Hotel", "hotel", "Da Nang",
    "36-38 Phan Ton, Ngu Hanh Son, Da Nang", 4.7, 1240, "00:00", "23:59", 1400000, "$$$",
    "hotel;beach;couple;romantic", 1440)
ALL_HOTELS["M Hotel Da Nang"] = loc("M Hotel Da Nang", "hotel", "Da Nang",
    "136 Tran Phu, Hai Chau, Da Nang", 4.4, 670, "00:00", "23:59", 950000, "$$",
    "hotel;modern;budget;group", 1440)
ALL_HOTELS["Danang Beach Hotel"] = loc("Danang Beach Hotel", "hotel", "Da Nang",
    "225 Tran Hung Dao, Son Tra, Da Nang", 4.2, 540, "00:00", "23:59", 700000, "$",
    "hotel;beach;budget", 1440)
ALL_HOTELS["Sea Vista Hotel & Apartment"] = loc("Sea Vista Hotel & Apartment", "hotel", "Da Nang",
    "12 Le Loi, Son Tra, Da Nang", 4.4, 320, "00:00", "23:59", 950000, "$$",
    "hotel;quiet;sea-view;apartment", 1440)
ALL_HOTELS["TIA Wellness Resort"] = loc("TIA Wellness Resort", "hotel", "Da Nang",
    "Vo Nguyen Giap, Ngu Hanh Son, Da Nang", 4.8, 980, "00:00", "23:59", 3500000, "$$$$",
    "resort;wellness;couple;honeymoon", 1440)
ALL_HOTELS["Premier Village Danang Resort"] = loc("Premier Village Danang Resort", "hotel", "Da Nang",
    "99 Vo Nguyen Giap, Ngu Hanh Son, Da Nang", 4.7, 1450, "00:00", "23:59", 2800000, "$$$$",
    "resort;beach;villa;honeymoon", 1440)
ALL_HOTELS["Hyatt Regency Danang Resort & Spa"] = loc("Hyatt Regency Danang Resort & Spa", "hotel", "Da Nang",
    "5 Truong Sa, Ngu Hanh Son, Da Nang", 4.7, 3200, "00:00", "23:59", 3200000, "$$$$",
    "resort;family;beach;luxury", 1440)
ALL_HOTELS["Danang Backpackers Hostel"] = loc("Danang Backpackers Hostel", "hotel", "Da Nang",
    "76 Tran Phu, Hai Chau, Da Nang", 4.1, 180, "00:00", "23:59", 150000, "$",
    "hostel;budget;backpacker", 1440)

# Hoi An hotels
ALL_HOTELS["Hoang Trinh Hotel"] = loc("Hoang Trinh Hotel", "hotel", "Hoi An",
    "187 Tran Hung Dao, Hoi An", 4.3, 380, "00:00", "23:59", 700000, "$",
    "hotel;family;central", 1440)
ALL_HOTELS["Allegro Hoi An"] = loc("Allegro Hoi An", "hotel", "Hoi An",
    "86 Tran Hung Dao, Hoi An", 4.5, 520, "00:00", "23:59", 1200000, "$$",
    "hotel;couple;romantic", 1440)
ALL_HOTELS["Hoi An Historic Hotel"] = loc("Hoi An Historic Hotel", "hotel", "Hoi An",
    "10 Tran Hung Dao, Hoi An", 4.4, 460, "00:00", "23:59", 950000, "$$",
    "hotel;central;modern", 1440)
ALL_HOTELS["La Siesta Hoi An Resort & Spa"] = loc("La Siesta Hoi An Resort & Spa", "hotel", "Hoi An",
    "132 Hung Vuong, Hoi An", 4.6, 1100, "00:00", "23:59", 1800000, "$$$",
    "resort;couple;family", 1440)
ALL_HOTELS["Hoi An Backpacker Hostel"] = loc("Hoi An Backpacker Hostel", "hotel", "Hoi An",
    "252 Cua Dai, Hoi An", 4.2, 220, "00:00", "23:59", 200000, "$",
    "hostel;budget;backpacker", 1440)
ALL_HOTELS["Hoi An Lodge"] = loc("Hoi An Lodge", "hotel", "Hoi An",
    "Hai Ba Trung, Hoi An", 4.3, 300, "00:00", "23:59", 800000, "$$",
    "hotel;family", 1440)

# Hue hotels
ALL_HOTELS["Hue Serene Palace Hotel"] = loc("Hue Serene Palace Hotel", "hotel", "Hue",
    "21 Pham Ngu Lao, Hue", 4.4, 540, "00:00", "23:59", 700000, "$",
    "hotel;central", 1440)
ALL_HOTELS["Eldora Hotel"] = loc("Eldora Hotel", "hotel", "Hue",
    "60 Ba Trieu, Hue", 4.6, 850, "00:00", "23:59", 1100000, "$$",
    "hotel;heritage", 1440)
ALL_HOTELS["Moonlight Hotel Hue"] = loc("Moonlight Hotel Hue", "hotel", "Hue",
    "20 Pham Ngu Lao, Hue", 4.4, 720, "00:00", "23:59", 850000, "$$",
    "hotel;central", 1440)
ALL_HOTELS["Hue Backpackers Hostel"] = loc("Hue Backpackers Hostel", "hotel", "Hue",
    "3 Pham Ngu Lao, Hue", 4.2, 220, "00:00", "23:59", 180000, "$",
    "hostel;budget", 1440)
ALL_HOTELS["Indochine Palace"] = loc("Indochine Palace", "hotel", "Hue",
    "105A Hung Vuong, Hue", 4.5, 1400, "00:00", "23:59", 1500000, "$$$",
    "hotel;luxury", 1440)


# Build locations dict
L = {}

# Da Nang - Food
L["Mỳ Quảng 24/7"] = loc("Mỳ Quảng 24/7", "food", "Da Nang", "163 Ho Nghe, Son Tra, Da Nang", 4.3, 2500, "06:00", "22:00", 80000, "$", "mi quang", 45)
L["Mỳ Quảng Bà Mua"] = loc("Mỳ Quảng Bà Mua", "food", "Da Nang", "19-21 Tran Binh Trong, Hai Chau, Da Nang", 4.5, 12000, "06:00", "21:00", 80000, "$", "mi quang", 45)
L["Bánh xèo Bà Dưỡng"] = loc("Bánh xèo Bà Dưỡng", "food", "Da Nang", "K280/23 Hoang Dieu, Hai Chau, Da Nang", 4.1, 15000, "09:30", "21:30", 100000, "$", "banh xeo", 60)
L["Bánh tráng cuốn thịt heo Bà Hường"] = loc("Bánh tráng cuốn thịt heo Bà Hường", "food", "Da Nang", "126 Tran Binh Trong, Hai Chau, Da Nang", 4.2, 3800, "10:00", "21:00", 100000, "$", "banh trang", 60)
L["Hải sản Bé Mặn"] = loc("Hải sản Bé Mặn", "food", "Da Nang", "Lo 14 Vo Nguyen Giap, Son Tra, Da Nang", 4.1, 5200, "10:00", "23:00", 200000, "$$", "seafood", 90)
L["Madame Lân"] = loc("Madame Lân", "food", "Da Nang", "3 Biet Thu, Hai Chau, Da Nang", 4.3, 1100, "10:00", "22:00", 250000, "$$", "french", 90)
L["Bếp Cuốn Đà Nẵng"] = loc("Bếp Cuốn Đà Nẵng", "food", "Da Nang", "04 Nguyen Van Linh, Hai Chau, Da Nang", 4.4, 1200, "10:30", "21:30", 180000, "$$", "vietnamese", 60)
L["Bún chả cá Hờn"] = loc("Bún chả cá Hờn", "food", "Da Nang", "113 Phan Chau Dihoang, Hai Chau, Da Nang", 4.2, 1800, "06:00", "22:00", 60000, "$", "bun cha ca", 45)
L["Bánh mì Bà Lan"] = loc("Bánh mì Bà Lan", "food", "Da Nang", "62 Nguyen Van Linh, Hai Chau, Da Nang", 4.2, 950, "06:00", "22:00", 30000, "$", "banh mi", 30)
L["Chè Liên"] = loc("Chè Liên", "food", "Da Nang", "189 Hoang Dieu, Hai Chau, Da Nang", 4.3, 720, "08:00", "22:00", 50000, "$", "che", 30)
L["Quán cơm bình dân"] = loc("Quán cơm bình dân", "food", "Da Nang", "Various Hai Chau", 4.0, 200, "10:00", "14:00", 50000, "$", "rice", 45)
L["Bánh mì + café"] = loc("Bánh mì + café", "food", "Da Nang", "Various Da Nang", 4.2, 100, "06:00", "10:00", 50000, "$", "breakfast", 30)
L["Buffet Bà Nà Hills"] = loc("Buffet Bà Nà Hills", "food", "Da Nang", "Sun World Ba Na Hills", 4.1, 8500, "11:00", "14:00", 300000, "$$", "buffet", 90)
L["Lunch tại resort"] = loc("Lunch tại resort", "food", "Da Nang", "Resort restaurant", 4.5, 500, "11:00", "14:00", 400000, "$$$", "resort-lunch", 90)
L["Romantic dinner ven biển"] = loc("Romantic dinner ven biển", "food", "Da Nang", "Beachfront Son Tra", 4.5, 400, "17:00", "22:00", 600000, "$$$", "dinner;couple", 90)
L["Bữa tối couple tại Đà Nẵng"] = loc("Bữa tối couple tại Đà Nẵng", "food", "Da Nang", "Bach Dang, Hai Chau", 4.3, 300, "17:00", "22:00", 300000, "$$", "dinner", 90)
L["Spa couple"] = loc("Spa couple", "wellness", "Da Nang", "Various Da Nang", 4.5, 200, "10:00", "22:00", 700000, "$$$", "spa", 120)
L["Spa Đà Nẵng"] = loc("Spa Đà Nẵng", "wellness", "Da Nang", "Various Hai Chau", 4.4, 800, "10:00", "22:00", 300000, "$$", "spa", 90)
L["Café ven biển"] = loc("Café ven biển", "food", "Da Nang", "Vo Nguyen Giap, Son Tra", 4.3, 1100, "07:00", "23:00", 80000, "$", "cafe;beach", 60)
L["Nhà hàng chay"] = loc("Nhà hàng chay", "food", "Da Nang", "Various Da Nang", 4.4, 250, "10:00", "21:00", 100000, "$", "vegetarian", 60)
L["Nhà hàng gia đình"] = loc("Nhà hàng gia đình", "food", "Da Nang", "Various Hai Chau", 4.3, 600, "10:00", "22:00", 150000, "$$", "family", 90)
L["Nhà hàng đặc sản"] = loc("Nhà hàng đặc sản", "food", "Da Nang", "Various Hai Chau", 4.3, 300, "10:00", "21:30", 150000, "$$", "local", 90)
L["Nhà hàng ven biển"] = loc("Nhà hàng ven biển", "food", "Da Nang", "Son Tra coast", 4.4, 500, "10:00", "22:00", 300000, "$$", "seaside", 90)
L["Dinner cuối chuyến"] = loc("Dinner cuối chuyến", "food", "Da Nang", "Bach Dang, Hai Chau", 4.5, 300, "17:00", "22:00", 500000, "$$$", "dinner", 90)
L["Café yên tĩnh ven sông Hàn"] = loc("Café yên tĩnh ven sông Hàn", "food", "Da Nang", "Bach Dang, Hai Chau", 4.3, 600, "07:00", "22:00", 80000, "$", "cafe;quiet", 60)

# Da Nang - Sightseeing
L["Bãi biển Mỹ Khê"] = loc("Bãi biển Mỹ Khê", "beach", "Da Nang", "Pham Van Dong, Son Tra", 4.5, 25000, "00:00", "23:59", 0, "$", "beach", 240)
L["Bãi biển Non Nước"] = loc("Bãi biển Non Nước", "beach", "Da Nang", "Hoang Sa, Ngu Hanh Son", 4.5, 11000, "00:00", "23:59", 0, "$", "beach;quiet", 180)
L["Bảo tàng Điêu khắc Chăm"] = loc("Bảo tàng Điêu khắc Chăm", "museum", "Da Nang", "02 2 Thang 9, Hai Chau", 4.2, 9500, "07:30", "17:00", 60000, "$", "museum", 90)
L["Bảo tàng Mỹ thuật Đà Nẵng"] = loc("Bảo tàng Mỹ thuật Đà Nẵng", "museum", "Da Nang", "78 Le Loi, Hai Chau", 4.1, 600, "08:00", "17:00", 10000, "$", "museum", 90)
L["Chùa Linh Ứng - Sơn Trà"] = loc("Chùa Linh Ứng - Sơn Trà", "cultural", "Da Nang", "Bai But, Son Tra", 4.7, 18000, "06:00", "21:00", 0, "$", "pagoda", 240)
L["Bán đảo Sơn Trà"] = loc("Bán đảo Sơn Trà", "sightseeing", "Da Nang", "Son Tra", 4.7, 15000, "00:00", "23:59", 0, "$", "nature", 180)
L["Bãi Bụt"] = loc("Bãi Bụt", "beach", "Da Nang", "Son Tra", 4.5, 4500, "00:00", "23:59", 0, "$", "beach", 120)
L["Ngũ Hành Sơn"] = loc("Ngũ Hành Sơn", "sightseeing", "Da Nang", "81 Huyen Tran Cong Chua", 4.6, 20000, "07:00", "17:00", 40000, "$$", "mountain", 180)
L["Sun World Bà Nà Hills"] = loc("Sun World Bà Nà Hills", "sightseeing", "Da Nang", "Hoa Vang", 4.4, 35000, "08:00", "22:00", 1000000, "$$$", "theme-park", 480)
L["Cầu Vàng"] = loc("Cầu Vàng", "sightseeing", "Da Nang", "Sun World Ba Na Hills", 4.6, 28000, "08:00", "22:00", 0, "$", "bridge", 30)
L["Cầu Rồng"] = loc("Cầu Rồng", "sightseeing", "Da Nang", "Tran Hung Dao - Nguyen Van Linh", 4.5, 22000, "00:00", "23:59", 0, "$", "bridge", 60)
L["Cầu Tình Yêu"] = loc("Cầu Tình Yêu", "sightseeing", "Da Nang", "Tran Hung Dao, Son Tra", 4.4, 12500, "00:00", "23:59", 0, "$", "bridge", 60)
L["Sông Hàn"] = loc("Sông Hàn", "sightseeing", "Da Nang", "Bach Dang, Hai Chau", 4.5, 8000, "00:00", "23:59", 0, "$", "river", 90)
L["An Thượng"] = loc("An Thượng", "food", "Da Nang", "Le Quang Hoa, Ngu Hanh Son", 4.3, 1500, "17:00", "23:00", 150000, "$", "nightlife", 90)
L["Helio Night Market"] = loc("Helio Night Market", "shopping", "Da Nang", "1 Dien Bien Phu, Hai Chau", 4.3, 4500, "17:00", "22:30", 100000, "$", "night-market", 90)
L["Chợ đêm Sơn Trà"] = loc("Chợ đêm Sơn Trà", "shopping", "Da Nang", "Mai Hac De, Son Tra", 4.2, 3200, "18:00", "23:00", 80000, "$", "night-market", 90)
L["Chợ Hàn"] = loc("Chợ Hàn", "shopping", "Da Nang", "Tran Phu, Hai Chau", 4.1, 5500, "07:00", "19:00", 80000, "$", "market", 90)
L["Chợ Cồn"] = loc("Chợ Cồn", "shopping", "Da Nang", "Hung Vuong, Hai Chau", 4.2, 4200, "07:00", "19:00", 100000, "$", "market", 90)
L["Vincom Plaza Đà Nẵng"] = loc("Vincom Plaza Đà Nẵng", "shopping", "Da Nang", "Ngo Quyen, Son Tra", 4.3, 8000, "09:30", "22:00", 0, "$", "mall", 90)
L["Tự do / di chuyện"] = loc("Tự do / di chuyện", "other", "Da Nang", "Various", 0, 0, "", "", 0, "$", "free", 0)
L["khách sạn nghỉ ngơi"] = loc("khách sạn nghỉ ngơi", "rest", "Da Nang", "Hotel", 0, 0, "00:00", "23:59", 0, "$", "rest", 240)
L["Mỹ Khê sáng sớm"] = loc("Mỹ Khê sáng sớm", "beach", "Da Nang", "Pham Van Dong, Son Tra", 4.5, 25000, "00:00", "23:59", 0, "$", "beach", 240)
L["Kết thúc"] = loc("Kết thúc", "end", "Da Nang", "", 0, 0, "", "", 0, "$", "end", 0)

# Hoi An - Food
L["Phố cổ Hội An"] = loc("Phố cổ Hội An", "sightseeing", "Hoi An", "Old Quarter", 4.5, 30000, "08:00", "21:00", 80000, "$", "old-town", 240)
L["Cơm gà Bà Buội"] = loc("Cơm gà Bà Buội", "food", "Hoi An", "22 Phan Chu Trinh", 4.0, 4500, "11:00", "14:00", 100000, "$", "com ga", 60)
L["Cao lầu Bà Bé"] = loc("Cao lầu Bà Bé", "food", "Hoi An", "16 Thai Phien", 4.0, 3200, "14:00", "22:00", 40000, "$", "cao lau", 45)
L["Bánh mì Phượng"] = loc("Bánh mì Phượng", "food", "Hoi An", "2B Phan Chu Trinh", 4.4, 4500, "06:30", "21:30", 40000, "$", "banh mi", 30)
L["Bánh mì Madam Khánh"] = loc("Bánh mì Madam Khánh", "food", "Hoi An", "115 Tran Cao Van", 4.4, 3500, "07:00", "20:00", 40000, "$", "banh mi", 30)
L["Morning Glory"] = loc("Morning Glory", "food", "Hoi An", "106 Nguyen Thai Hoc", 4.4, 2200, "11:00", "22:00", 250000, "$$", "vietnamese", 90)
L["Bánh bao bánh vạc Hoa Hồng Trắng"] = loc("Bánh bao bánh vạc Hoa Hồng Trắng", "food", "Hoi An", "57 Phan Chu Trinh", 4.2, 1100, "08:00", "20:00", 100000, "$", "banh bao", 60)
L["Bánh xèo Hội An"] = loc("Bánh xèo Hội An", "food", "Hoi An", "12 Phan Chu Trinh", 4.2, 800, "16:00", "21:00", 100000, "$", "banh xeo", 60)
L["Nhà hàng Cẩm Thanh"] = loc("Nhà hàng Cẩm Thanh", "food", "Hoi An", "Cam Thanh", 4.2, 600, "10:00", "21:00", 150000, "$$", "seafood", 90)
L["Nhà hàng An Bàng"] = loc("Nhà hàng An Bàng", "food", "Hoi An", "An Bang", 4.4, 700, "10:00", "22:00", 200000, "$$", "seafood", 90)
L["Nhà hàng Trà Quế"] = loc("Nhà hàng Trà Quế", "food", "Hoi An", "Tra Que", 4.2, 400, "10:00", "21:00", 150000, "$$", "organic", 90)
L["Romantic dinner phố cổ"] = loc("Romantic dinner phố cổ", "food", "Hoi An", "Old Quarter riverside", 4.5, 200, "17:00", "22:00", 400000, "$$$", "dinner;couple", 90)
L["Pub/café phố cổ"] = loc("Pub/café phố cổ", "food", "Hoi An", "Old Quarter", 4.2, 800, "17:00", "23:00", 150000, "$$", "nightlife", 90)
L["Café ven sông Hoài"] = loc("Café ven sông Hoài", "food", "Hoi An", "Riverside Old Quarter", 4.4, 1500, "07:00", "22:00", 80000, "$", "cafe;river", 60)
L["Café Reaching Out"] = loc("Café Reaching Out", "food", "Hoi An", "Old Quarter", 4.6, 600, "08:00", "21:00", 100000, "$", "cafe;quiet", 60)
L["Café yên tĩnh"] = loc("Café yên tĩnh", "food", "Hoi An", "Countryside", 4.4, 250, "07:00", "22:00", 70000, "$", "cafe;quiet", 60)
L["Café phố cổ"] = loc("Café phố cổ", "food", "Hoi An", "Old Quarter", 4.4, 700, "07:00", "22:00", 60000, "$", "cafe", 60)
L["Chè Hội An"] = loc("Chè Hội An", "food", "Hoi An", "Old Quarter", 4.3, 400, "17:00", "22:00", 40000, "$", "che", 30)
L["Dinner gia đình"] = loc("Dinner gia đình", "food", "Hoi An", "Hoi An", 4.3, 200, "17:00", "22:00", 200000, "$$", "dinner", 90)
L["Spa Hội An"] = loc("Spa Hội An", "wellness", "Hoi An", "Hoi An", 4.5, 800, "10:00", "22:00", 300000, "$$", "spa", 90)
L["Du thuyền sông Hoài"] = loc("Du thuyền sông Hoài", "sightseeing", "Hoi An", "Hoai River", 4.3, 1200, "17:00", "21:00", 150000, "$$", "boat", 60)

# Hoi An - Sightseeing
L["An Bàng Beach"] = loc("An Bàng Beach", "beach", "Hoi An", "An Bang", 4.4, 8500, "00:00", "23:59", 0, "$", "beach", 180)
L["Nhà cổ Tấn Ký"] = loc("Nhà cổ Tấn Ký", "cultural", "Hoi An", "10 Nguyen Thai Hoc", 4.4, 4200, "08:00", "18:00", 0, "$", "heritage", 60)
L["Chùa Cầu"] = loc("Chùa Cầu", "cultural", "Hoi An", "Tran Phu", 4.5, 28000, "00:00", "23:59", 0, "$", "bridge", 30)
L["Chợ đêm Hội An"] = loc("Chợ đêm Hội An", "shopping", "Hoi An", "Hoai River", 4.5, 6000, "18:00", "22:00", 0, "$", "night-market", 90)
L["Chợ Hội An"] = loc("Chợ Hội An", "shopping", "Hoi An", "Old Quarter", 4.2, 1800, "07:00", "19:00", 100000, "$", "market", 60)
L["Rừng dừa Bảy Mẫu"] = loc("Rừng dừa Bảy Mẫu", "sightseeing", "Hoi An", "Cam Thanh", 4.3, 5500, "08:00", "18:00", 30000, "$", "coconut", 180)
L["Trà Quế"] = loc("Trà Quế", "sightseeing", "Hoi An", "Tra Que Village", 4.4, 3200, "08:00", "18:00", 35000, "$", "herb", 90)
L["Làng gốm Thanh Hà"] = loc("Làng gốm Thanh Hà", "sightseeing", "Hoi An", "Thanh Ha", 4.3, 2800, "08:00", "17:30", 35000, "$", "pottery", 90)
L["Làng mộc Kim Bồng"] = loc("Làng mộc Kim Bồng", "sightseeing", "Hoi An", "Kim Bong", 4.3, 1500, "08:00", "17:30", 35000, "$", "wood", 90)
L["Phố đèn lồng"] = loc("Phố đèn lồng", "sightseeing", "Hoi An", "Old Quarter", 4.5, 15000, "18:00", "22:00", 0, "$", "lantern", 60)
L["Sông Hoài"] = loc("Sông Hoài", "sightseeing", "Hoi An", "Hoai River", 4.5, 4000, "18:00", "22:00", 0, "$", "river", 60)
L["Mua đặc sản"] = loc("Mua đặc sản", "shopping", "Hoi An", "Old Quarter", 4.2, 200, "08:00", "21:00", 200000, "$$", "souvenir", 60)
L["Trả phòng"] = loc("Trả phòng", "end", "Hoi An", "", 0, 0, "", "", 0, "$", "end", 0)

# Hue - Sightseeing
L["Đại Nội Huế"] = loc("Đại Nội Huế", "cultural", "Hue", "23 August Revolution", 4.6, 22000, "06:30", "17:30", 200000, "$$", "imperial-city", 180)
L["Điện Thái Hòa"] = loc("Điện Thái Hòa", "cultural", "Hue", "Đại Nội", 4.6, 8000, "06:30", "17:30", 0, "$", "palace", 60)
L["Lăng Minh Mạng"] = loc("Lăng Minh Mạng", "cultural", "Hue", "Hung Long", 4.6, 9500, "07:00", "17:30", 150000, "$", "tomb", 120)
L["Lăng Khải Định"] = loc("Lăng Khải Định", "cultural", "Hue", "Thuy Bang", 4.7, 7200, "07:00", "17:30", 150000, "$", "tomb", 120)
L["Lăng Tự Đức"] = loc("Lăng Tự Đức", "cultural", "Hue", "Thuy Xuan", 4.6, 8800, "07:00", "17:30", 150000, "$", "tomb", 120)
L["Lăng Đồng Khánh"] = loc("Lăng Đồng Khánh", "cultural", "Hue", "Hue", 4.4, 1500, "07:00", "17:30", 100000, "$", "tomb", 90)
L["Cung An Định"] = loc("Cung An Định", "cultural", "Hue", "Phu Cat", 4.4, 3200, "07:00", "17:30", 50000, "$", "palace", 60)
L["Đàn Nam Giao"] = loc("Đàn Nam Giao", "cultural", "Hue", "South Hue", 4.3, 800, "07:00", "17:30", 50000, "$", "altar", 60)
L["Chùa Thiên Mụ"] = loc("Chùa Thiên Mụ", "cultural", "Hue", "Kim Long", 4.6, 18500, "08:00", "18:00", 0, "$", "pagoda", 90)
L["Bảo tàng Cổ vật Cung đình Huế"] = loc("Bảo tàng Cổ vật Cung đình Huế", "museum", "Hue", "3 8 August Revolution", 4.4, 1500, "07:00", "17:30", 50000, "$", "museum", 90)
L["Sông Hương"] = loc("Sông Hương", "sightseeing", "Hue", "Perfume River", 4.6, 12000, "00:00", "23:59", 0, "$", "river", 60)
L["Làng hương Thủy Xuân"] = loc("Làng hương Thủy Xuân", "sightseeing", "Hue", "Thuy Xuan", 4.2, 1500, "08:00", "18:00", 100000, "$", "incense", 60)
L["Phố đi bộ Nguyễn Đình Chiểu"] = loc("Phố đi bộ Nguyễn Đình Chiểu", "sightseeing", "Hue", "Nguyen Dinh Chieu", 4.3, 3500, "17:00", "22:00", 0, "$", "walking-street", 60)
L["Chợ Đông Ba"] = loc("Chợ Đông Ba", "shopping", "Hue", "Tran Hung Dao", 4.2, 4500, "07:00", "19:00", 100000, "$", "market", 90)
L["Công viên ven sông"] = loc("Công viên ven sông", "sightseeing", "Hue", "Riverside Hue", 4.3, 1200, "00:00", "23:59", 0, "$", "park", 60)

# Hue - Food
L["Bún bò Huế Hạnh"] = loc("Bún bò Huế Hạnh", "food", "Hue", "17 Ly Thuong Kiet", 4.2, 3500, "07:00", "21:00", 60000, "$", "bun bo", 45)
L["Bánh bèo Bà Đỏ"] = loc("Bánh bèo Bà Đỏ", "food", "Hue", "11 Dinh Cong Trang", 4.1, 2200, "08:00", "21:30", 80000, "$", "banh beo", 45)
L["Chè Huế"] = loc("Chè Huế", "food", "Hue", "Old Quarter", 4.3, 1500, "14:00", "22:00", 40000, "$", "che", 30)
L["Cơm niêu"] = loc("Cơm niêu", "food", "Hue", "Various Hue", 4.2, 1500, "10:00", "21:00", 150000, "$$", "claypot", 90)
L["Cơm hến Hoa Đông"] = loc("Cơm hến Hoa Đông", "food", "Hue", "Old Quarter", 4.2, 1100, "07:00", "21:00", 50000, "$", "com hen", 45)
L["Bún thịt nướng"] = loc("Bún thịt nướng", "food", "Hue", "Various Hue", 4.1, 1200, "10:00", "21:00", 60000, "$", "bun thit", 45)
L["Nem lụi Huế"] = loc("Nem lụi Huế", "food", "Hue", "Various Hue", 4.3, 1800, "16:00", "21:00", 80000, "$", "nem lui", 60)
L["Bánh khoái Hồng Mai"] = loc("Bánh khoái Hồng Mai", "food", "Hue", "6 Dinh Tien Hoang", 4.2, 1500, "10:00", "21:00", 80000, "$", "banh khoai", 60)
L["Bánh lọc Huế"] = loc("Bánh lọc Huế", "food", "Hue", "Various Hue", 4.2, 1100, "09:00", "20:00", 50000, "$", "banh loc", 30)
L["Nhà hàng Huế"] = loc("Nhà hàng Huế", "food", "Hue", "Various Hue", 4.3, 1000, "10:00", "21:00", 150000, "$$", "hue-cuisine", 90)
L["Cơm bình dân"] = loc("Cơm bình dân", "food", "Hue", "Various Hue", 4.0, 300, "10:00", "14:00", 50000, "$", "rice;budget", 45)
L["Café ven sông Hương"] = loc("Café ven sông Hương", "food", "Hue", "Riverside Hue", 4.3, 1200, "07:00", "22:00", 70000, "$", "cafe;river", 60)
L["Café"] = loc("Café", "food", "Hue", "Various Hue", 4.3, 500, "07:00", "22:00", 70000, "$", "cafe", 60)
L["Nghỉ khách sạn"] = loc("Nghỉ khách sạn", "rest", "Hue", "Hotel", 0, 0, "00:00", "23:59", 0, "$", "rest", 240)


# Aliases (after base L is built)
ALIASES = {
    "An Bàng sunset": "An Bàng Beach",
    "An Bàng": "An Bàng Beach",
    "Chùa Cầu + nhà cổ": "Chùa Cầu",
    "Đạp xe Trà Quế": "Trà Quế",
    "Thanh Hà": "Làng gốm Thanh Hà",
    "Đi bộ phố cổ": "Phố đèn lồng",
    "Phố cổ": "Phố cổ Hội An",
    "Đại Nội": "Đại Nội Huế",
    "Đại Nội – Ngọ Môn": "Đại Nội Huế",
    "Ngọ Môn – Đại Nội": "Đại Nội Huế",
    "Điện Thái Hòa + Tử Cấm Thành": "Điện Thái Hòa",
    "Điện Thái Hòa – Tử Cấm Thành": "Điện Thái Hòa",
    "Phố đi bộ": "Phố đi bộ Nguyễn Đình Chiểu",
    "Bánh bèo": "Bánh bèo Bà Đỏ",
    "Bún bò Hạnh": "Bún bò Huế Hạnh",
    "Bún bò Huế": "Bún bò Huế Hạnh",
    "Cơm hến": "Cơm hến Hoa Đông",
    "Nhà hàng cơm Huế": "Nhà hàng Huế",
    "Nhà hàng gia đình": "Nhà hàng Huế",
    "Café phố cổ": "Café",
    "Café lịch sử/phố cổ": "Café",
    "Café yên tĩnh": "Café",
    "Nghỉ": "Nghỉ khách sạn",
    "Sông Hàn + Cầu Rồng": "Sông Hàn",
    "Mỹ Khê": "Bãi biển Mỹ Khê",
    "My Khe Beach": "Bãi biển Mỹ Khê",
    "Mỹ Khê sunset": "Bãi biển Mỹ Khê",
    "Sơn Trà – Bãi Bụt": "Bãi Bụt",
    "Bà Nà Hills": "Sun World Bà Nà Hills",
    "Ngũ Hành Sơn – Thủy Sơn": "Ngũ Hành Sơn",
    "dạo sông Hàn": "Sông Hàn",
    "Linh Ứng": "Chùa Linh Ứng - Sơn Trà",
    "Chùa Linh Ứng": "Chùa Linh Ứng - Sơn Trà",
    "Sơn Trà": "Bán đảo Sơn Trà",
    "Bãi Bụt + Non Nước": "Bãi Bụt",
    "Cầu Tình Yêu + sông Hàn": "Sông Hàn",
    "Bà Nà Hills + Cầu Vàng": "Sun World Bà Nà Hills",
    "Resort + biển": "Bãi biển Mỹ Khê",
    "Mỹ Khê sáng sớm": "Bãi biển Mỹ Khê",
    "Non Nước": "Bãi biển Non Nước",
    "Mỹ Khê (sáng sớm)": "Bãi biển Mỹ Khê",
}
for alias, real in ALIASES.items():
    if alias not in L and real in L:
        L[alias] = L[real]


def get_loc(name):
    if name not in L:
        raise KeyError("Location not found: '%s'" % name)
    return L[name]


def get_hotel(name):
    if name not in ALL_HOTELS:
        raise KeyError("Hotel not found: '%s'" % name)
    return ALL_HOTELS[name]


if __name__ == "__main__":
    print("Locations:", len(L))
    print("Hotels:", len(ALL_HOTELS))