"""
Simple matcher: exact-match the 24 simple prompts (e.g. "đi đà nẵng 3 ngày 2 đêm, 4.5-6 triệu, 2-3 người")
to fixed plan IDs (DN01-s, DN02-s, ...).

Strategy:
  1. Try exact-match against the 24 known prompts in rule.txt
  2. If no exact match, use deterministic heuristic:
     - detect city
     - detect days
     - detect budget
     - detect people count + style signals
     - return best matching plan_id from the 24
"""
from __future__ import annotations
import re
import json
import unicodedata
from pathlib import Path
from typing import Optional, Dict, Any, List


# Load 24 simple prompts from rule.txt (hard-coded map)
# Each entry: { "plan_id": "DN01-s", "city": "da_nang", "days": 3, "nights": 2,
#   "budget_min": 4500000, "budget_max": 6000000, "people_min": 2, "people_max": 3, "style": "balanced" }

# These mirror the simple prompts in rule.txt Part B
SIMPLE_PROMPTS = [
    # ĐÀ NẴNG
    {"id": "DN01-s",  "city": "da_nang", "city_vn": "Đà Nẵng", "days": 3, "nights": 2,
     "budget_min": 4500000, "budget_max": 6000000, "people_min": 2, "people_max": 3, "style": "balanced",
     "canonical_query": "đi đà nẵng 3 ngày 2 đêm, 4.5-6 triệu, 2-3 người"},
    {"id": "DN02-s",  "city": "da_nang", "city_vn": "Đà Nẵng", "days": 3, "nights": 2,
     "budget_min": 5000000, "budget_max": 7000000, "people_min": 2, "people_max": 2, "style": "romantic",
     "canonical_query": "đi đà nẵng 3 ngày 2 đêm, 5-7 triệu, 2 người cặp đôi"},
    {"id": "DN03-s",  "city": "da_nang", "city_vn": "Đà Nẵng", "days": 4, "nights": 3,
     "budget_min": 6000000, "budget_max": 8000000, "people_min": 3, "people_max": 4, "style": "adventure",
     "canonical_query": "đi đà nẵng 4 ngày 3 đêm, 6-8 triệu, nhóm 3-4 bạn trẻ"},
    {"id": "DN04-s",  "city": "da_nang", "city_vn": "Đà Nẵng", "days": 3, "nights": 2,
     "budget_min": 3500000, "budget_max": 5000000, "people_min": 1, "people_max": 2, "style": "foodie",
     "canonical_query": "đi đà nẵng 3 ngày 2 đêm, 3.5-5 triệu, 1-2 người, thích ăn"},
    {"id": "DN05-s",  "city": "da_nang", "city_vn": "Đà Nẵng", "days": 4, "nights": 3,
     "budget_min": 6000000, "budget_max": 9000000, "people_min": 4, "people_max": 6, "style": "family",
     "canonical_query": "đi đà nẵng 4 ngày 3 đêm, 6-9 triệu, gia đình có trẻ nhỏ + người lớn tuổi"},
    {"id": "DNA01-s", "city": "da_nang", "city_vn": "Đà Nẵng", "days": 3, "nights": 2,
     "budget_min": 3500000, "budget_max": 5500000, "people_min": 1, "people_max": 1, "style": "quiet",
     "canonical_query": "đi đà nẵng 3 ngày 2 đêm, 3.5-5.5 triệu, 1 người, tìm chỗ yên tĩnh"},
    {"id": "DNA02-s", "city": "da_nang", "city_vn": "Đà Nẵng", "days": 3, "nights": 2,
     "budget_min": 6000000, "budget_max": 10000000, "people_min": 2, "people_max": 2, "style": "honeymoon",
     "canonical_query": "đi đà nẵng 3 ngày 2 đêm, 6-10 triệu, 2 người honeymoon"},
    {"id": "DNA03-s", "city": "da_nang", "city_vn": "Đà Nẵng", "days": 3, "nights": 2,
     "budget_min": 2500000, "budget_max": 4000000, "people_min": 1, "people_max": 1, "style": "student",
     "canonical_query": "đi đà nẵng 3 ngày 2 đêm, 2.5-4 triệu, 1 người sinh viên"},

    # HỘI AN
    {"id": "HOI01-s", "city": "hoian", "city_vn": "Hội An", "days": 3, "nights": 2,
     "budget_min": 3500000, "budget_max": 5500000, "people_min": 3, "people_max": 4, "style": "family",
     "canonical_query": "đi hội an 3 ngày 2 đêm, 3.5-5.5 triệu, gia đình 3-4 người"},
    {"id": "HOI02-s", "city": "hoian", "city_vn": "Hội An", "days": 3, "nights": 2,
     "budget_min": 4500000, "budget_max": 7000000, "people_min": 2, "people_max": 2, "style": "romantic",
     "canonical_query": "đi hội an 3 ngày 2 đêm, 4.5-7 triệu, cặp đôi"},
    {"id": "HOI03-s", "city": "hoian", "city_vn": "Hội An", "days": 4, "nights": 3,
     "budget_min": 5000000, "budget_max": 7000000, "people_min": 3, "people_max": 3, "style": "friends",
     "canonical_query": "đi hội an 4 ngày 3 đêm, 5-7 triệu, 3 người bạn"},
    {"id": "HOI04-s", "city": "hoian", "city_vn": "Hội An", "days": 3, "nights": 2,
     "budget_min": 3000000, "budget_max": 5000000, "people_min": 1, "people_max": 2, "style": "foodie",
     "canonical_query": "đi hội an 3 ngày 2 đêm, 3-5 triệu, 1-2 người thích ăn"},
    {"id": "HOI05-s", "city": "hoian", "city_vn": "Hội An", "days": 4, "nights": 3,
     "budget_min": 5000000, "budget_max": 8000000, "people_min": 3, "people_max": 5, "style": "family",
     "canonical_query": "đi hội an 4 ngày 3 đêm, 5-8 triệu, gia đình đa thế hệ"},
    {"id": "HOA01-s", "city": "hoian", "city_vn": "Hội An", "days": 3, "nights": 2,
     "budget_min": 3000000, "budget_max": 5000000, "people_min": 1, "people_max": 1, "style": "quiet",
     "canonical_query": "đi hội an 3 ngày 2 đêm, 3-5 triệu, 1 người yên tĩnh"},
    {"id": "HOA02-s", "city": "hoian", "city_vn": "Hội An", "days": 3, "nights": 2,
     "budget_min": 4000000, "budget_max": 6500000, "people_min": 1, "people_max": 2, "style": "photographer",
     "canonical_query": "đi hội an 3 ngày 2 đêm, 4-6.5 triệu, 1-2 người thích chụp ảnh"},
    {"id": "HOA03-s", "city": "hoian", "city_vn": "Hội An", "days": 3, "nights": 2,
     "budget_min": 2500000, "budget_max": 4000000, "people_min": 1, "people_max": 1, "style": "backpacker",
     "canonical_query": "đi hội an 3 ngày 2 đêm, 2.5-4 triệu, 1 người backpacker"},

    # HUẾ
    {"id": "HUE01-s", "city": "hue", "city_vn": "Huế", "days": 3, "nights": 2,
     "budget_min": 3500000, "budget_max": 5500000, "people_min": 3, "people_max": 4, "style": "family",
     "canonical_query": "đi huế 3 ngày 2 đêm, 3.5-5.5 triệu, gia đình 3-4 người"},
    {"id": "HUE02-s", "city": "hue", "city_vn": "Huế", "days": 3, "nights": 2,
     "budget_min": 3000000, "budget_max": 4500000, "people_min": 1, "people_max": 2, "style": "foodie",
     "canonical_query": "đi huế 3 ngày 2 đêm, 3-4.5 triệu, 1-2 người thích ăn"},
    {"id": "HUE03-s", "city": "hue", "city_vn": "Huế", "days": 3, "nights": 2,
     "budget_min": 3500000, "budget_max": 5000000, "people_min": 2, "people_max": 3, "style": "elderly",
     "canonical_query": "đi huế 3 ngày 2 đêm, 3.5-5 triệu, đi cùng người lớn tuổi"},
    {"id": "HUE04-s", "city": "hue", "city_vn": "Huế", "days": 4, "nights": 3,
     "budget_min": 5000000, "budget_max": 7000000, "people_min": 1, "people_max": 1, "style": "history",
     "canonical_query": "đi huế 4 ngày 3 đêm, 5-7 triệu, 1 người thích lịch sử"},
    {"id": "HUE05-s", "city": "hue", "city_vn": "Huế", "days": 4, "nights": 3,
     "budget_min": 5000000, "budget_max": 8000000, "people_min": 3, "people_max": 5, "style": "family",
     "canonical_query": "đi huế 4 ngày 3 đêm, 5-8 triệu, gia đình đa thế hệ"},
    {"id": "HUEA01-s", "city": "hue", "city_vn": "Huế", "days": 3, "nights": 2,
     "budget_min": 3000000, "budget_max": 5000000, "people_min": 1, "people_max": 1, "style": "quiet",
     "canonical_query": "đi huế 3 ngày 2 đêm, 3-5 triệu, 1 người yên tĩnh"},
    {"id": "HUEA02-s", "city": "hue", "city_vn": "Huế", "days": 4, "nights": 3,
     "budget_min": 5000000, "budget_max": 7500000, "people_min": 1, "people_max": 1, "style": "history_deep",
     "canonical_query": "đi huế 4 ngày 3 đêm, 5-7.5 triệu, 1 người đam mê lịch sử"},
    {"id": "HUEA03-s", "city": "hue", "city_vn": "Huế", "days": 3, "nights": 2,
     "budget_min": 2500000, "budget_max": 4000000, "people_min": 1, "people_max": 1, "style": "student",
     "canonical_query": "đi huế 3 ngày 2 đêm, 2.5-4 triệu, 1 sinh viên"},
]

# Map plan_id -> full plan data
_PLANS_DB: Dict[str, Dict[str, Any]] = {}
_PLANS_LOADED = False


def _load_plans():
    global _PLANS_DB, _PLANS_LOADED
    if _PLANS_LOADED:
        return
    plan_path = Path(__file__).parent / "plans_simple.json"
    with open(plan_path, encoding="utf-8") as f:
        data = json.load(f)
    for p in data.get("plans", []):
        _PLANS_DB[p["id"]] = p
    _PLANS_LOADED = True


def get_simple_plan(plan_id: str) -> Optional[Dict[str, Any]]:
    """Get full plan by ID (e.g. 'DN01-s')."""
    _load_plans()
    return _PLANS_DB.get(plan_id)


def _no_accent(s: str) -> str:
    if not s:
        return ""
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def _detect_city(query: str) -> Optional[str]:
    """Detect city from query. Returns 'da_nang' / 'hoian' / 'hue' or None."""
    q = query.lower()
    q_no = _no_accent(q)
    # Đà Nẵng
    if "đà nẵng" in q or "da nang" in q_no or "danang" in q_no:
        return "da_nang"
    # Hội An
    if "hội an" in q or "hoi an" in q_no or "hoian" in q_no:
        return "hoian"
    # Huế
    if "huế" in q or "hue" in q_no:
        return "hue"
    return None


def _detect_days(query: str) -> Optional[int]:
    """Detect number of days from query (e.g. '3 ngày 2 đêm' -> 3)."""
    m = re.search(r"(\d+)\s*ngày", query)
    if m:
        return int(m.group(1))
    return None


def _detect_budget(query: str) -> Optional[int]:
    """Detect budget in VND. '5 triệu' or '5-7 triệu' -> mid value 6_000_000."""
    # Match ranges: "4.5-6 triệu" or "5-7 triệu"
    m = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*triệu", query)
    if m:
        lo = float(m.group(1))
        hi = float(m.group(2))
        # Return mid value
        return int(((lo + hi) / 2) * 1_000_000)
    # Single value: "5 triệu"
    m = re.search(r"(\d+(?:\.\d+)?)\s*triệu", query)
    if m:
        return int(float(m.group(1)) * 1_000_000)
    return None


def _detect_people(query: str) -> Optional[int]:
    """Detect number of people (e.g. '2-3 người' -> 2, '4 người' -> 4)."""
    m = re.search(r"(\d+)\s*-\s*(\d+)\s*người", query)
    if m:
        return int(m.group(1))  # use min
    m = re.search(r"(\d+)\s*người", query)
    if m:
        return int(m.group(1))
    # Singular: "1 người"
    m = re.search(r"1\s*người", query)
    if m:
        return 1
    # "sinh viên" or "1 mình" or "một mình" -> 1
    if re.search(r"sinh viên|1 mình|một mình|solo", query.lower()):
        return 1
    # "cặp đôi" / "couple" -> 2
    if re.search(r"cặp đôi|couple|2 người|honeymoon", query.lower()):
        return 2
    # "gia đình" / "family" -> 4
    if re.search(r"gia đình|family|nhóm|group", query.lower()):
        return 4
    return None


def _detect_style(query: str) -> Optional[str]:
    """Detect travel style from query keywords."""
    q = query.lower()
    if re.search(r"yên tĩnh|healing|slow|chữa lành|chậm", q):
        return "quiet"
    if re.search(r"cặp đôi|honeymoon|lãng mạn|romantic|2 người", q):
        return "romantic" if "honeymoon" in q else "romantic"
    if re.search(r"thích ăn|foodie|ẩm thực|food", q):
        return "foodie"
    if re.search(r"bạn trẻ|trẻ|adventure|năng động|trekking", q):
        return "adventure"
    if re.search(r"gia đình|family|trẻ nhỏ|người lớn tuổi|đa thế hệ", q):
        return "family"
    if re.search(r"sinh viên|student|tiết kiệm|backpacker|ngân sách", q):
        return "backpacker"
    if re.search(r"lịch sử|history", q):
        return "history"
    if re.search(r"chụp ảnh|photo|photographer", q):
        return "photographer"
    if re.search(r"người lớn tuổi|elderly|chậm", q):
        return "elderly"
    return None


def match_simple_plan(query: str) -> Dict[str, Any]:
    """
    Match a simple Vietnamese query to one of 24 fixed plans.

    Returns:
    {
      "plan_id": "DN01-s" | ...,
      "match_type": "exact" | "fuzzy",
      "match_score": float (0-1),
      "alternatives": [list of close plan_ids],
      "candidates": [list of all considered plans with scores],
    }
    """
    _load_plans()

    city = _detect_city(query)
    days = _detect_days(query)
    budget = _detect_budget(query)
    people = _detect_people(query)
    style = _detect_style(query)

    # Try EXACT match: re.sub whitespace, lowercase, strip
    q_norm = re.sub(r"\s+", " ", query.strip().lower())
    for p in SIMPLE_PROMPTS:
        c_norm = re.sub(r"\s+", " ", p["canonical_query"].lower())
        if q_norm == c_norm:
            return {
                "plan_id": p["id"],
                "match_type": "exact",
                "match_score": 1.0,
                "alternatives": [],
                "candidates": [{"id": p["id"], "score": 1.0}],
                "parsed": {"city": city, "days": days, "budget": budget, "people": people, "style": style},
            }

    # FUZZY: score each plan
    candidates = []
    for p in SIMPLE_PROMPTS:
        score = 0.0
        if city and p["city"] == city:
            score += 0.40
        if days is not None:
            # 3 ngày plans
            if p["days"] == days:
                score += 0.20
            elif abs(p["days"] - days) == 1:
                score += 0.10
        if budget is not None:
            if p["budget_min"] <= budget <= p["budget_max"]:
                score += 0.20
            else:
                # partial credit: ratio of overlap
                lo = max(p["budget_min"], budget * 0.6)
                hi = min(p["budget_max"], budget * 1.4)
                if hi > lo:
                    score += 0.10
        if people is not None:
            if p["people_min"] <= people <= p["people_max"]:
                score += 0.10
            elif abs(people - p["people_min"]) <= 1:
                score += 0.05
        if style and p["style"] == style:
            score += 0.10
        candidates.append({"id": p["id"], "score": round(score, 3)})

    candidates.sort(key=lambda x: x["score"], reverse=True)
    best = candidates[0]
    alts = [c["id"] for c in candidates[1:4] if c["score"] > 0.3]

    # Confidence gating: if city not detected AND signal is weak, reject
    if city is None and best["score"] < 0.4:
        return {
            "plan_id": None,
            "match_type": "rejected",
            "match_score": best["score"],
            "alternatives": alts,
            "candidates": candidates,
            "parsed": {"city": city, "days": days, "budget": budget, "people": people, "style": style},
            "reject_reason": "no_city_detected_and_weak_signal",
        }
    if best["score"] < 0.3:
        return {
            "plan_id": None,
            "match_type": "rejected",
            "match_score": best["score"],
            "alternatives": alts,
            "candidates": candidates,
            "parsed": {"city": city, "days": days, "budget": budget, "people": people, "style": style},
            "reject_reason": "low_signal",
        }

    return {
        "plan_id": best["id"],
        "match_type": "fuzzy",
        "match_score": best["score"],
        "alternatives": alts,
        "candidates": candidates,
        "parsed": {"city": city, "days": days, "budget": budget, "people": people, "style": style},
    }


if __name__ == "__main__":
    # Quick test
    tests = [
        "đi đà nẵng 3 ngày 2 đêm, 4.5-6 triệu, 2-3 người",
        "đi hội an 4 ngày 3 đêm, 5-7 triệu, 3 người bạn",
        "đi huế 3 ngày 2 đêm, 3-4.5 triệu, 1-2 người thích ăn",
        "đi đà nẵng 5 ngày 4 đêm, 5 triệu, 2 người",  # không khớp exact
    ]
    for t in tests:
        result = match_simple_plan(t)
        print(f"\nQ: {t}")
        print(f"  → {result['plan_id']} ({result['match_type']}, score={result['match_score']})")
        if result["alternatives"]:
            print(f"    alts: {result['alternatives']}")