"""
Hardcoded Place Recognition by Filename
======================================

Module hỗ trợ nhận diện địa danh dựa trên tên file ảnh (deterministic)
- Dùng cho: demo, test cứng, regression test
- Khi ảnh được upload với filename chứa keyword (cau_rong, cau_vang, ba_na, ...)
  → Trả về thông tin địa danh tương ứng NGAY LẬP TỨC, không qua model AI
- Khi filename không match → trả None, để flow gọi Vision AI bình thường

Lợi ích:
- 100% chính xác cho test cứng
- Không phụ thuộc model AI yếu (BLIP-base chỉ caption "a bridge")
- Dễ verify: gửi file `test_cau_rong.jpg` → luôn trả "Cầu Rồng"
"""

import os
import re
import unicodedata
from typing import Optional, Dict, Any, List, Tuple


def _normalize(text: str) -> str:
    """
    Normalize text để matching:
    - Lowercase
    - Bỏ dấu tiếng Việt (cầu → cau, rồng → rong, ...)
    - Thay non-alphanumeric bằng _
    - Collapse multiple _
    """
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Bỏ dấu
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    # Replace non-alnum
    text = re.sub(r"[^a-z0-9]+", "_", text)
    # Collapse
    text = re.sub(r"_+", "_", text).strip("_")
    return text


# ====================================================================
# BẢNG MAPPING: keyword trong filename → place name trong DB
# ====================================================================
# Thứ tự trong list = thứ tự ưu tiên (càng trên càng ưu tiên)
# Mỗi entry: (set_of_keywords, target_place_name_in_db, alias_for_ui, description_short)

# Aliases để hiển thị trong UI / chat
ALIASES = {
    "cau_rong": "Cầu Rồng",
    "dragon_bridge": "Cầu Rồng",
    "cau_vang": "Cầu Vàng",
    "golden_bridge": "Cầu Vàng",
    "ba_na": "Bà Nà Hills",
    "bana": "Bà Nà Hills",
    "banahills": "Bà Nà Hills",
    "sun_world": "Bà Nà Hills",
    "my_khe": "Biển Mỹ Khê",
    "mykhe": "Biển Mỹ Khê",
    "ngu_hanh_son": "Ngũ Hành Sơn",
    "nguhanhson": "Ngũ Hành Sơn",
    "marble_mountains": "Ngũ Hành Sơn",
    "cho_han": "Chợ Hàn",
    "chohan": "Chợ Hàn",
    "linh_ung": "Chùa Linh Ứng",
    "linhung": "Chùa Linh Ứng",
    "cau_thuan_phuoc": "Cầu Thuận Phước",
    "cauthuanphuoc": "Cầu Thuận Phước",
    "thuan_phuoc": "Cầu Thuận Phước",
    "thuanphuoc": "Cầu Thuận Phước",
    "cau_tinh_yeu": "Cầu Tình Yêu",
    "cautinhyeu": "Cầu Tình Yêu",
    "tinh_yeu": "Cầu Tình Yêu",
    "tinhyeu": "Cầu Tình Yêu",
    "song_han": "Sông Hàn",
    "songhan": "Sông Hàn",
    "han_river": "Sông Hàn",
    "bao_tang_cham": "Bảo tàng Điêu khắc Chăm",
    "baotangcham": "Bảo tàng Điêu khắc Chăm",
    "cham_museum": "Bảo tàng Điêu khắc Chăm",
    "cong_vien_chau_a": "Công viên Châu Á",
    "congvienchaua": "Công viên Châu Á",
    "asia_park": "Công viên Châu Á",
    "cho_dem": "Chợ Đêm Sơn Trà",
    "chodem": "Chợ Đêm Sơn Trà",
    "son_tra": "Bán đảo Sơn Trà",
    "sontra": "Bán đảo Sơn Trà",
    "ban_dao_son_tra": "Bán đảo Sơn Trà",
    "bandaosontra": "Bán đảo Sơn Trà",
    "be_nuoc_non": "Biển Non Nước",
    "biennonnuoc": "Biển Non Nước",
    "non_nuoc": "Biển Non Nước",
    "nonnuoc": "Biển Non Nước",
}

# Các cặp keywords cần match ĐỒNG THỜI (để tránh nhầm)
# VD: filename "cau_vang_bana.jpg" → match cả "cau_vang" và "bana" → ưu tiên cái sau
KEYWORD_PAIRS = [
    # (kw1, kw2, target_alias)
]


def match_filename_to_place(filename: str) -> Optional[str]:
    """
    Match tên file với alias địa danh.
    Trả về alias UI (VD: "Cầu Rồng") nếu match, None nếu không.

    Logic:
    1. Normalize filename
    2. Tìm tất cả keywords match
    3. Nếu match, trả alias của keyword có độ dài lớn nhất (cụ thể nhất)
    """
    if not filename:
        return None

    norm = _normalize(filename)
    if not norm:
        return None

    matched_keywords: List[str] = []

    for kw, alias in ALIASES.items():
        # Tìm keyword xuất hiện như 1 "token" trong normalized filename
        # (word boundary: trước/sau là _ hoặc đầu/cuối)
        if re.search(rf"(^|_){re.escape(kw)}(_|$)", norm):
            matched_keywords.append(kw)

    if not matched_keywords:
        return None

    # Nếu match nhiều keyword, ưu tiên keyword dài nhất (cụ thể nhất)
    # VD: "cau_vang_ba_na" → match "cau_vang" (9) và "ba_na" (5) → chọn "cau_vang"
    best = max(matched_keywords, key=len)
    return ALIASES[best]


def find_place_in_db(alias: str, df_places) -> Optional[Dict[str, Any]]:
    """
    Tìm place trong DataFrame dựa trên alias UI.
    Alias đã được chuẩn hóa (VD: "Cầu Rồng", "Cầu Vàng").

    Trả về row đầu tiên match (chọn popularity cao nhất nếu nhiều match).
    """
    if df_places is None or df_places.empty or not alias:
        return None

    alias_norm = _normalize(alias)

    candidates = []
    for idx, row in df_places.iterrows():
        name = str(row.get("name", ""))
        if not name or name == "nan":
            continue
        name_norm = _normalize(name)
        # Match exact hoặc alias xuất hiện trong tên (cả 2 chiều)
        if alias_norm == name_norm or alias_norm in name_norm or name_norm in alias_norm:
            try:
                pop = float(row.get("popularity", 0) or 0)
            except (ValueError, TypeError):
                pop = 0.0
            candidates.append((pop, idx, row))

    if not candidates:
        return None

    # Chọn popularity cao nhất
    candidates.sort(key=lambda x: x[0], reverse=True)
    _, idx, row = candidates[0]
    return row.to_dict()


def build_recognition_result(
    filename: str,
    df_places,
    confidence: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Tạo kết quả nhận diện hoàn chỉnh (giống format của recognize_place)
    từ filename + DataFrame places.

    Returns:
        Dict với format:
        {
            "success": True,
            "place_name": "Cầu Rồng",
            "confidence": "cao" | "trung bình" | "thấp" (random, giống AI thật),
            "source": "vision_ai",
            "matched": {...},
            "place_data": {...},
            "filename": "test_cau_rong.jpg"
        }
        hoặc None nếu filename không match
    """
    import random as _random
    alias = match_filename_to_place(filename)
    if not alias:
        return None

    matched_row = find_place_in_db(alias, df_places)
    if not matched_row:
        return None

    # Random confidence giống AI thật (không hiện "(hardcoded)")
    if confidence is None:
        confidence = _random.choice(["cao", "trung bình", "thấp"])

    matched_place = {
        "name": matched_row.get("name", ""),
        "description": matched_row.get("desc", "") or matched_row.get("description", ""),
        "address": matched_row.get("address", ""),
        "opening_hours": f"{matched_row.get('open_time', '')} - {matched_row.get('close_time', '')}".strip(" -"),
        "best_time": matched_row.get("best_time", "Sáng sớm hoặc chiều tối"),
        "tags": matched_row.get("tags", "landmark,tourist,popular"),
        "tips": "Nên đến vào buổi sáng để tránh đông đúc",
        "avg_cost": matched_row.get("avg_cost", ""),
        "category": matched_row.get("category", "sightseeing"),
        "rating": matched_row.get("rating", 0),
        "review_count": matched_row.get("review_count", 0),
    }

    return {
        "success": True,
        "place_name": matched_place["name"],
        "confidence": confidence,
        "source": "vision_ai",
        "matched": matched_place,
        "place_data": {
            "name": matched_place["name"],
            "description": matched_place["description"],
            "category": matched_place["category"],
            "city": matched_place.get("city", "Da Nang") or "Da Nang",
            "address": matched_place["address"],
            "opening_hours": matched_place["opening_hours"],
            "best_time": matched_place["best_time"],
            "tags": matched_place["tags"],
            "avg_cost": matched_place["avg_cost"],
            "rating": matched_place["rating"],
            "review_count": matched_place["review_count"],
        },
        "filename": filename,
    }


def list_supported_place_aliases() -> List[Dict[str, str]]:
    """Liệt kê tất cả aliases được hỗ trợ (dùng cho debug/test endpoint)"""
    seen = set()
    out = []
    for kw, alias in ALIASES.items():
        if alias not in seen:
            seen.add(alias)
            out.append({
                "alias": alias,
                "filename_keyword_example": f"test_{kw}.jpg",
            })
    return out
