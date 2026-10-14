"""
Personality detector - extract personality / travel style signals from user query.

Vietnamese-first keywords with accent-insensitive matching.
Maps user phrasing to:
  - dominant_style (the plan category that should win)
  - positive_preferences / negative_preferences (tag-like signals)
  - flags: is_student, is_couple, is_solo, is_family, has_children, is_first_time

Output feeds into UserIntent.
"""
from __future__ import annotations
import re
import unicodedata
from typing import List, Dict, Tuple, Set, Optional


def _no_accent(s: str) -> str:
    """Remove Vietnamese diacritics for accent-insensitive matching."""
    if not s:
        return ""
    # Use NFD decomposition then drop combining marks
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


# Style mapping: each style has a list of (keyword, weight) tuples
# Higher weight = stronger signal.
# We accumulate weighted votes across all signals and pick the highest.
STYLE_KEYWORDS: Dict[str, List[Tuple[str, float]]] = {
    "quiet": [
        ("yên tĩnh", 3.0), ("im lặng", 2.0), ("tĩnh lặng", 2.5),
        ("tránh đông", 3.0), ("không thích đông", 3.5), ("ít người", 2.5),
        ("chill", 1.5), ("chữa lành", 2.0), ("healing", 1.5),
        ("nghỉ ngơi", 1.5), ("thư giãn", 1.0), ("bình yên", 2.0),
        ("peaceful", 2.5), ("quiet", 3.0), ("trầm", 1.5),
        ("introvert", 2.5), ("hướng nội", 2.5), ("riêng tư", 1.5),
        ("không ồn ào", 3.0), ("không náo nhiệt", 3.0),
        ("tránh ồn", 3.0), ("yên ắng", 2.5),
    ],
    "romantic": [
        ("lãng mạn", 3.0), ("romantic", 3.0), ("honeymoon", 3.5),
        ("tuần trăng mật", 3.5), ("kỷ niệm", 2.0), ("anniversary", 3.0),
        ("đi với người yêu", 3.5), ("đi cặp đôi", 3.0), ("đi vợ chồng", 3.0),
        ("2 người yêu nhau", 3.0), ("cùng người yêu", 3.0),
        ("đôi ta", 1.5), ("vợ chồng son", 2.5),
        ("người yêu", 2.0), ("bạn gái", 2.0), ("bạn trai", 2.0),
        ("đi với ny", 3.0), ("ny", 2.0),
    ],
    "foodie": [
        ("ẩm thực", 3.0), ("ăn uống", 2.5), ("food", 2.5), ("foodie", 3.5),
        ("ăn gì", 2.5), ("đặc sản", 2.0), ("món ngon", 2.5),
        ("bún bò", 2.0), ("mì quảng", 2.0), ("cao lầu", 2.0),
        ("cơm hến", 2.0), ("bánh bèo", 1.5), ("bánh mì", 1.5),
        ("hải sản", 2.0), ("seafood", 2.0), ("chè", 1.5),
        ("street food", 2.0), ("quán ăn", 1.5), ("nhà hàng", 1.5),
        ("bún chả cá", 2.0), ("bánh tráng", 1.5),
        ("ăn vặt", 1.5), ("ăn đêm", 1.0),
    ],
    "budget": [
        ("tiết kiệm", 3.0), ("budget", 3.0), ("rẻ", 2.0), ("sinh viên", 3.5),
        ("student", 3.0), ("backpacker", 3.5), ("ít tiền", 3.0),
        ("tiền ít", 2.5), ("tiền eo hẹp", 2.5), ("giá rẻ", 2.5),
        ("hostel", 2.5), ("homestay", 1.5), ("cheap", 2.5),
        ("affordable", 2.0), ("không tốn kém", 2.0),
        ("ngân sách thấp", 3.0), ("ngan sach thap", 3.0),
        ("giá hợp lý", 1.5), ("tiết kiệm chi phí", 3.0),
    ],
    "history": [
        ("lịch sử", 2.5), ("history", 2.5), ("di sản", 2.0),
        ("cố đô", 2.0), ("triều nguyễn", 2.5), ("đại nội", 2.0),
        ("lăng tẩm", 2.0), ("bảo tàng", 2.0), ("museum", 2.0),
        ("kiến trúc", 1.5), ("văn hóa", 1.0),
        ("đam mê lịch sử", 3.5), ("rất thích lịch sử", 3.5),
        ("thích lịch sử", 2.5), ("tìm hiểu lịch sử", 3.0),
    ],
    "family": [
        ("gia đình", 3.0), ("family", 3.0), ("có con nhỏ", 3.5),
        ("có bé", 3.0), ("trẻ em", 2.5), ("với con", 3.0),
        ("ba mẹ", 2.5), ("ông bà", 2.0), ("cả nhà", 2.5),
        ("đi cùng gia đình", 3.0), ("kids", 2.5),
    ],
    "adventure": [
        ("phiêu lưu", 3.0), ("adventure", 3.0), ("khám phá", 1.5),
        ("trekking", 3.0), ("leo núi", 2.5), ("năng động", 2.0),
        ("outdoor", 2.5), ("hoạt động ngoài trời", 2.5),
        ("mạo hiểm", 3.0), ("thể thao", 1.5), ("đi bộ đường dài", 2.5),
        ("hiking", 3.0), ("cắm trại", 2.0),
    ],
    "relax": [
        ("nghỉ dưỡng", 3.0), ("resort", 2.5), ("thư giãn", 2.0),
        ("biển", 1.0), ("beach", 1.0), ("spa", 2.5), ("massage", 2.0),
        ("bơi", 1.0), ("tắm biển", 1.5), ("nằm dài", 1.5),
        ("đọc sách", 1.0), ("chill", 1.5),
    ],
    "balanced": [
        ("lần đầu", 2.0), ("first time", 2.0), ("khám phá", 1.0),
        ("cân bằng", 2.5), ("đầy đủ", 1.5), ("tổng quan", 1.5),
        ("đi lần đầu", 2.5), ("chưa đi bao giờ", 2.0),
        ("muốn xem hết", 1.5), ("nổi bật", 1.0),
    ],
    "photography": [
        ("chụp ảnh", 3.0), ("photography", 3.0), ("photo", 2.0),
        ("aesthetic", 2.0), ("nghệ thuật", 1.5), ("art", 1.5),
        ("sáng tạo", 1.5), ("handmade", 1.0), ("lantern", 1.0),
    ],
    "spiritual": [
        ("chùa", 1.5), ("pagoda", 1.5), ("thiền", 2.0), ("meditation", 2.0),
        ("tâm linh", 3.0), ("spiritual", 3.0), ("phật", 1.5),
        ("hành hương", 2.0), ("cầu nguyện", 1.5),
    ],
}

# Hard signals for "adaptive" triggers (overrides any "core" preference)
ADAPTIVE_TRIGGERS: Dict[str, List[str]] = {
    "quiet": [
        "yên tĩnh", "im lặng", "không thích đông", "tránh đông",
        "chill", "chữa lành", "ít người", "peaceful", "quiet", "introvert",
    ],
    "romantic": [
        "lãng mạn", "romantic", "honeymoon", "tuần trăng mật",
        "đi với người yêu", "đi cặp đôi", "kỷ niệm",
    ],
    "budget": [
        "sinh viên", "student", "backpacker", "tiết kiệm", "rẻ",
        "ít tiền", "hostel", "ngân sách thấp", "ngan sach thap",
        "tiet kiem",
    ],
}

# Negative preference patterns: things user does NOT want
# Each entry: (regex, tag). Regex is matched against accent-stripped lowercase query.
NEGATIVE_PATTERNS: List[Tuple[str, str]] = [
    (r"khong thich dong", "crowded"),
    (r"tranh dong", "crowded"),
    (r"it nguoi", "crowded"),
    (r"khong thich di bo", "long_walk"),
    (r"khong thich di bo nhieu", "long_walk"),
    (r"khong thich lich trinh day", "packed"),
    (r"khong thich di nhieu", "packed"),
    (r"khong thich dat", "expensive"),
    (r"khong thich diem dat", "expensive"),
    (r"khong thich gia cao", "expensive"),
    (r"khong thich tourist", "touristy"),
    (r"khong thich du lich doan", "touristy"),
    (r"khong thich nightlife", "nightlife"),
    (r"khong thich quan bar", "nightlife"),
    (r"khong thich club", "nightlife"),
    (r"khong thich quan nhau", "nightlife"),
    (r"khong thich an cay", "spicy"),
    (r"khong thich do an cay", "spicy"),
    (r"khong thich leo nui", "trekking"),
    (r"khong thich trekking", "trekking"),
    (r"ghet dong", "crowded"),
    (r"ghet cho dong", "crowded"),
]

# Positive preference patterns: things user DOES want
POSITIVE_PATTERNS: List[Tuple[str, str]] = [
    (r"thich yen tinh", "quiet"),
    (r"thich chill", "quiet"),
    (r"thich chua lanh", "quiet"),
    (r"thich bien", "beach"),
    (r"thich beach", "beach"),
    (r"thich tam bien", "beach"),
    (r"thich lang man", "romantic"),
    (r"thich romantic", "romantic"),
    (r"thich am thuc", "food"),
    (r"thich an uong", "food"),
    (r"thich food", "food"),
    (r"thich lich su", "history"),
    (r"thich history", "history"),
    (r"thich di san", "history"),
    (r"thich chup anh", "photography"),
    (r"thich photography", "photography"),
    (r"thich photo", "photography"),
    (r"thich nghi duong", "spa"),
    (r"thich spa", "spa"),
    (r"thich massage", "spa"),
    (r"thich di bo", "active"),
    (r"thich walking", "active"),
    (r"thich trekking", "active"),
    (r"thich mac hiem", "adventure"),
    (r"thich adventure", "adventure"),
    (r"thich kham pha", "adventure"),
    (r"thich cafe", "cafe"),
    (r"thich quan cafe", "cafe"),
    (r"thich chua", "spiritual"),
    (r"thich thien", "spiritual"),
    (r"thich spiritual", "spiritual"),
    (r"thich mua sam", "shopping"),
    (r"thich shopping", "shopping"),
]

# Companion / family / etc. signal patterns
COMPANION_SIGNALS: Dict[str, List[str]] = {
    "solo": ["một mình", "1 mình", "solo", "alone", "đi một mình", "cá nhân"],
    "couple": ["2 người", "hai người", "vợ chồng", "người yêu", "cùng ny", "với bạn trai", "với bạn gái", "couple", "đôi ta", "đi cặp"],
    "family": ["gia đình", "family", "ba mẹ", "ông bà", "con cái", "cả nhà"],
    "friends": ["bạn bè", "friends", "nhóm bạn", "đám bạn", "tụi mình"],
    "group": ["nhóm", "group", "đoàn", "nhiều người", "công ty"],
}

CHILD_SIGNALS = ["con nhỏ", "có con", "em bé", "có bé", "trẻ em", "kids", "đi với con", "baby"]


def detect_personality(query: str) -> Dict[str, any]:
    """
    Detect personality / travel style from user query (Vietnamese-friendly).
    Accent-insensitive: "yen tinh" and "yên tĩnh" both match.
    """
    if not query:
        return _empty_personality()
    # Normalize: lowercase + strip accents
    q_lower = query.lower()
    q_no_accent = _no_accent(q_lower)
    q_norm = " ".join(q_no_accent.split())  # canonical form for keyword matching

    # 1. Score each style (accent-insensitive)
    style_scores: Dict[str, float] = {}
    matched_keywords: Dict[str, List[str]] = {}
    for style, kws in STYLE_KEYWORDS.items():
        score = 0.0
        matches: List[str] = []
        for kw, weight in kws:
            # Check accent-insensitive version
            kw_no_accent = _no_accent(kw.lower())
            if kw_no_accent and kw_no_accent in q_norm:
                score += weight
                matches.append(kw)
        if score > 0:
            style_scores[style] = score
            matched_keywords[style] = matches

    # 2. Pick dominant
    if style_scores:
        # Tie-breaker: prefer 'quiet' / 'budget' / 'romantic' over generic 'balanced'
        priority = ["quiet", "budget", "romantic", "history", "foodie", "family", "adventure", "photography", "spiritual", "relax", "balanced"]
        # First: highest score
        max_score = max(style_scores.values())
        top_styles = [s for s, sc in style_scores.items() if sc == max_score]
        if len(top_styles) > 1:
            # Use priority order
            for p in priority:
                if p in top_styles:
                    dominant_style = p
                    break
            else:
                dominant_style = top_styles[0]
        else:
            dominant_style = top_styles[0]
    else:
        dominant_style = None

    # 2b. Check for STRONG signal: if user query contains explicit activity words
    # like "ăn", "chụp ảnh", "lịch sử", "leo núi" — that's a stronger signal than just budget
    strong_signals = {
        "foodie": ["an", "am thuc", "mon ngon", "food", "an uong", "bun", "my", "banh"],
        "history": ["lich su", "lich su", "di san", "kien truc", "trieu nguyen", "dai noi", "lang"],
        "romantic": ["lang man", "romantic", "honeymoon", "tuan trang mat", "cap doi", "vo chong", "nguoi yeu"],
        "adventure": ["phieu luu", "trekking", "leo nui", "nang dong", "outdoor", "mao hiem", "kham pha"],
        "photography": ["chup anh", "photography", "photo", "aesthetic", "nghe thuat", "art"],
        "quiet": ["yen tinh", "im lang", "tinh lang", "tranh dong", "khong thich dong", "chill", "chua lanh", "it nguoi"],
    }
    strong_matches = []
    for style, words in strong_signals.items():
        for w in words:
            if w in q_norm:
                strong_matches.append(style)
                break
    has_strong_intent = len(strong_matches) > 0
    # Override: if user has strong intent for a non-budget style AND budget came
    # only from "X triệu" pattern (which is just a number, not "tiết kiệm" word),
    # then prefer the strong intent style.
    only_budget_from_money = (
        "budget" in style_scores
        and not any(w in q_norm for w in ["tiet kiem", "sinh vien", "student", "backpacker", "re ", "it tien", "hostel"])
    )
    if has_strong_intent and only_budget_from_money:
        # Pick the strong signal with highest score
        candidates = [(s, style_scores.get(s, 0)) for s in strong_matches if s in style_scores]
        if candidates:
            # Re-pick dominant from strong matches
            candidates.sort(key=lambda x: -x[1])
            new_dominant = candidates[0][0]
            # Only override if new_dominant has at least 2.0 score (real signal)
            if style_scores.get(new_dominant, 0) >= 2.0:
                dominant_style = new_dominant

    # 2c. DEMOTE 'budget' style if it's only there because user said "budget X triệu"
    # (which is just a number, not a real "tiết kiệm/rẻ" intent).
    # However, if the actual budget amount is low (<4M VND), the user clearly wants
    # budget travel — keep budget as dominant.
    only_budget_keyword = (
        "budget" in style_scores
        and not any(w in q_norm for w in [
            "tiet kiem", "sinh vien", "student", "backpacker",
            "re ", "it tien", "hostel",
            "ngan sach thap", "ngan sach re", "re tien",
            "chi phi thap", "gia re",
        ])
    )
    if dominant_style == "budget" and only_budget_keyword:
        # Try to detect actual budget amount from query
        import re as _re
        money_match = _re.search(r"(\d+(?:[.,]\d+)?)\s*(triệu|tr|trieu|ty)\b", q_no_accent.replace(",", "."))
        money_val = None
        if money_match:
            num = float(money_match.group(1).replace(",", "."))
            unit = money_match.group(2)
            if unit in ("ty",):
                money_val = num * 1_000_000_000
            else:
                money_val = num * 1_000_000  # triệu
        # If budget is low (<4M), keep budget as dominant
        if money_val is None or money_val >= 4_000_000:
            # Check if any other style exists with non-zero score
            others = {k: v for k, v in style_scores.items() if k != "budget" and v > 0}
            if others:
                best = max(others.items(), key=lambda x: x[1])
                dominant_style = best[0]
            else:
                dominant_style = "balanced"
                style_scores["balanced"] = style_scores.get("balanced", 0) + 1.5

    # 3. Adaptive triggers: any style whose trigger words appear
    adaptive_triggers: List[str] = []
    for style, triggers in ADAPTIVE_TRIGGERS.items():
        if any(_no_accent(t) in q_norm for t in triggers):
            adaptive_triggers.append(style)

    # 4. Positive / negative preferences via regex (accent-insensitive)
    positive_preferences: List[str] = []
    negative_preferences: List[str] = []
    for pat, tag in POSITIVE_PATTERNS:
        pat_no_accent = _no_accent(pat)
        if re.search(pat_no_accent, q_norm):
            if tag not in positive_preferences:
                positive_preferences.append(tag)
    for pat, tag in NEGATIVE_PATTERNS:
        pat_no_accent = _no_accent(pat)
        if re.search(pat_no_accent, q_norm):
            if tag not in negative_preferences:
                negative_preferences.append(tag)

    # 5. Companion signals
    detected_companion: Optional[str] = None
    for comp, kws in COMPANION_SIGNALS.items():
        for k in kws:
            if _no_accent(k) in q_norm:
                detected_companion = comp
                break
        if detected_companion:
            break

    is_student = any(_no_accent(k) in q_norm for k in ["sinh vien", "student", "sv "])
    is_first_time = any(_no_accent(k) in q_norm for k in ["lan dau", "first time", "di lan dau", "chua di bao gio"])
    has_children = any(_no_accent(k) in q_norm for k in CHILD_SIGNALS)
    is_couple = detected_companion == "couple"
    is_solo = detected_companion == "solo"
    is_family = detected_companion == "family" or has_children

    return {
        "dominant_style": dominant_style,
        "style_scores": style_scores,
        "matched_keywords": matched_keywords,
        "positive_preferences": positive_preferences,
        "negative_preferences": negative_preferences,
        "adaptive_triggers": adaptive_triggers,
        "is_student": is_student,
        "is_first_time": is_first_time,
        "is_couple": is_couple,
        "is_solo": is_solo,
        "is_family": is_family,
        "has_children": has_children,
        "detected_companion": detected_companion,
    }


def _empty_personality() -> Dict[str, any]:
    return {
        "dominant_style": None,
        "style_scores": {},
        "matched_keywords": {},
        "positive_preferences": [],
        "negative_preferences": [],
        "adaptive_triggers": [],
        "is_student": False,
        "is_first_time": False,
        "is_couple": False,
        "is_solo": False,
        "is_family": False,
        "has_children": False,
        "detected_companion": None,
    }
