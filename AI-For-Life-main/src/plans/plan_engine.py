"""
Plan Engine - the main entrypoint for plan-driven itinerary generation.

This is the layer that:
  1. Loads all plans
  2. Builds a UserIntent from query (reusing QueryExtractor for budget/days/city)
  3. Detects personality
  4. Matches primary + secondary plans
  5. Adapts plans to user's day count + budget tier
  6. Ranks places by plan
  7. Returns a structured plan_response dict

The LLM (if available) is then asked to narrate the plan_response into
natural language, using the structured data as ground truth.
"""
from __future__ import annotations
import os
import re
import json
import math
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from .index import load_all_plans, get_plan_by_id, _normalize_city, list_all_plans
from .plan_model import UserIntent, PlanMatchResult
from .personality import detect_personality
from .plan_matcher import (
    match_plan, match_all_plans, select_primary_and_secondary,
    classify_budget_tier,
)
from .plan_adapter import adapt_plan_to_days, adapt_plan_to_budget, compute_per_day_budget
from .place_scorer import rank_places_by_plan, filter_places_for_plan, score_place


# Lazy load dataset to avoid circular imports
_DATASET_DF: Optional[pd.DataFrame] = None


def _get_dataset() -> pd.DataFrame:
    global _DATASET_DF
    if _DATASET_DF is None:
        paths = [
            "data/itinerary_dataset.clean.csv",
            "data/places_clean.csv",
            "data/places.csv",
        ]
        for p in paths:
            if os.path.exists(p):
                try:
                    _DATASET_DF = pd.read_csv(p)
                    print(f"[OK] Plan engine loaded dataset: {p} ({len(_DATASET_DF)} rows)")
                    break
                except Exception as e:
                    print(f"[WARN] Error loading {p}: {e}")
        if _DATASET_DF is None:
            print("[ERROR] Plan engine: no dataset found")
            _DATASET_DF = pd.DataFrame()
    return _DATASET_DF


def build_user_intent(
    query: str,
    city: Optional[str] = None,
    days: Optional[int] = None,
    budget_total: Optional[int] = None,
    travel_companion: Optional[str] = None,
) -> UserIntent:
    """
    Build a UserIntent from raw query + optional explicit overrides.
    Reuses QueryExtractor from src.query_extractor for budget/days parsing.
    """
    # Lazy import to avoid circular dep
    from src.query_extractor import QueryExtractor

    extracted = QueryExtractor.extract_all(query or "")
    detected_city = city or extracted.get("city")
    detected_days = days or extracted.get("days")
    detected_budget = budget_total if budget_total is not None else extracted.get("budget")
    detected_companion = travel_companion or extracted.get("travel_companion", "solo")
    budget_type = extracted.get("budget_type", "total")

    # Personality detection
    personality = detect_personality(query or "")

    intent = UserIntent(
        city=_normalize_city(detected_city) if detected_city else None,
        days=detected_days,
        nights=(detected_days - 1) if detected_days else None,
        budget_total=detected_budget,
        budget_per_day=extracted.get("budget_per_day"),
        budget_type=budget_type,
        travel_companion=detected_companion,
        # Sử dụng _get_people_count để map chính xác (family=4, group_X=X, ...)
        people_count=_get_people_count(detected_companion),
        positive_preferences=personality.get("positive_preferences", []),
        negative_preferences=personality.get("negative_preferences", []),
        dominant_style=personality.get("dominant_style"),
        is_student=personality.get("is_student", False),
        is_first_time=personality.get("is_first_time", False),
        is_couple=personality.get("is_couple", False),
        is_solo=personality.get("is_solo", False),
        is_family=personality.get("is_family", False),
        has_children=personality.get("has_children", False),
        raw_query=query or "",
    )
    return intent


def _get_people_count(companion: str) -> int:
    m = {
        "solo": 1,
        "couple": 2,
        "family": 4,
        "friends": 2,
    }
    if companion and companion.startswith("group_"):
        try:
            return int(companion.split("_")[1])
        except Exception:
            return 3
    return m.get(companion, 1)


def _select_diverse_top_k(
    df: pd.DataFrame,
    k: int,
    used_ids: set,
    score_col: str = "plan_score",
) -> pd.DataFrame:
    """Pick top k by score, skipping already-used ids and forcing category diversity."""
    if df is None or df.empty:
        return df
    # Sort by score desc
    df_sorted = df.sort_values(score_col, ascending=False).reset_index(drop=True)
    selected: List[int] = []  # dataframe indices
    used_categories: Dict[str, int] = {}
    for idx, row in df_sorted.iterrows():
        try:
            pid = int(row.get("id", -1))
        except (ValueError, TypeError):
            continue
        if pid in used_ids:
            continue
        cat = str(row.get("category", "")).lower().strip()
        if used_categories.get(cat, 0) >= 2:
            # already have 2 of this category
            continue
        selected.append(idx)
        used_ids.add(pid)
        used_categories[cat] = used_categories.get(cat, 0) + 1
        if len(selected) >= k:
            break
    if selected:
        return df_sorted.iloc[selected].copy()
    return df_sorted.head(min(k, len(df_sorted))).copy()


def build_itinerary_from_plan(
    plan: Dict[str, Any],
    intent: UserIntent,
    df_places: Optional[pd.DataFrame] = None,
) -> List[Dict[str, Any]]:
    """
    Build a day-by-day itinerary using the plan's rules.
    Returns list of {day, morning, lunch, afternoon, evening, hotel, day_cost_estimate}.
    """
    if df_places is None:
        df_places = _get_dataset()
    if df_places is None or df_places.empty:
        return []

    # Filter by city
    city_norm = _normalize_city(intent.city) if intent.city else None
    if city_norm:
        # Map canonical key back to display form
        city_display_map = {
            "danang": ["Da Nang", "Đà Nẵng"],
            "hoian": ["Hoi An", "Hội An"],
            "hue": ["Hue", "Huế"],
        }
        display_names = city_display_map.get(city_norm, [intent.city])
        mask = df_places["city"].astype(str).str.strip().isin(display_names)
        city_df = df_places[mask]
    else:
        city_df = df_places.copy()

    if city_df.empty:
        return []

    # Rank by plan
    rules = plan.get("rules", {})
    max_places = int(rules.get("max_places_per_day", 4))

    # We'll pick: morning, lunch, afternoon, evening, hotel (5 slots)
    # But exclude hotel from "places" pool, since hotel needs different logic
    # Use plan_score as primary sort
    ranked = rank_places_by_plan(city_df, plan)

    # Separate by category
    food_pool = ranked[ranked["category"].astype(str).str.lower().isin(["food", "shopping"])].copy()  # shopping can double as food court
    sightseeing_pool = ranked[~ranked["category"].astype(str).str.lower().isin(["food", "shopping", "hotel"])].copy()
    hotel_pool = ranked[ranked["category"].astype(str).str.lower() == "hotel"].copy()

    # Hotel budget gate: lọc cứng theo max_hotel_avg_cost (cost/đêm) trong rules.
    # max_hotel_avg_cost = giới hạn cost/đêm cho phòng (1 phòng).
    # Áp dụng cho mọi plan có rule này. Mặc định nếu không có: filter
    # theo budget_max của plan ÷ (nights + 1) ÷ 2 (couple 2 người 1 phòng).
    rules = plan.get("rules", {})
    max_hotel_cost = rules.get("max_hotel_avg_cost")
    if max_hotel_cost is None:
        # Fallback: budget_max của plan (per person cho cả chuyến) ÷ (số đêm + 1 buffer)
        # giới hạn cost/đêm cho 1 phòng. Chia thêm 1.5 để chừa biên.
        budget_max = plan.get("budget_max") or 6000000
        nights = max(1, (plan.get("default_days", 3) or 3) - 1)
        # Công thức: (budget_max * 1 người) * 0.45 (phần cho hotel) / nights
        max_hotel_cost = int((budget_max * 0.45) / nights)

    # Filter hotel theo avg_cost
    if "avg_cost" in hotel_pool.columns and max_hotel_cost > 0:
        # Resort cũng dùng category "hotel" (cùng pool) trong dataset này
        hotel_pool = hotel_pool[hotel_pool["avg_cost"].fillna(0) <= max_hotel_cost]
    if hotel_pool.empty:
        # Nếu filter quá chặt, nới lỏng: lấy tất cả hotel
        hotel_pool = ranked[ranked["category"].astype(str).str.lower() == "hotel"].copy()

    # Adjust max for compress/expand
    requested_days = intent.days or plan.get("default_days", 3)
    if requested_days < plan.get("default_days", 3):
        # compress: keep 2-3 slots instead of 4
        max_places = min(max_places, 3)

    days_plan: List[Dict[str, Any]] = []
    used_food: set = set()
    used_sightseeing: set = set()

    for d in range(requested_days):
        day = d + 1
        # Morning: sightseeing
        morning_df = _select_diverse_top_k(
            sightseeing_pool[~sightseeing_pool["id"].astype(str).isin(used_sightseeing)],
            k=1, used_ids=used_sightseeing,
        )
        morning = morning_df.iloc[0].to_dict() if not morning_df.empty else None

        # Lunch: food
        lunch_df = _select_diverse_top_k(
            food_pool[~food_pool["id"].astype(str).isin(used_food)],
            k=1, used_ids=used_food,
        )
        lunch = lunch_df.iloc[0].to_dict() if not lunch_df.empty else None

        # Afternoon: sightseeing (different from morning)
        afternoon_df = _select_diverse_top_k(
            sightseeing_pool[~sightseeing_pool["id"].astype(str).isin(used_sightseeing)],
            k=1, used_ids=used_sightseeing,
        )
        afternoon = afternoon_df.iloc[0].to_dict() if not afternoon_df.empty else None

        # Evening: sightseeing (or food for romantic plans)
        if plan.get("travel_style") in ("romantic", "foodie"):
            evening_df = _select_diverse_top_k(
                food_pool[~food_pool["id"].astype(str).isin(used_food)],
                k=1, used_ids=used_food,
            )
        else:
            evening_df = _select_diverse_top_k(
                sightseeing_pool[~sightseeing_pool["id"].astype(str).isin(used_sightseeing)],
                k=1, used_ids=used_sightseeing,
            )
        evening = evening_df.iloc[0].to_dict() if not evening_df.empty else None

        # Hotel: from hotel pool, pick highest-scored not-yet-used (allow reuse across days)
        if d == 0 or not days_plan or not days_plan[-1].get("hotel"):
            hotel_df = _select_diverse_top_k(
                hotel_pool, k=1, used_ids=set(),  # allow reuse
            )
            hotel = hotel_df.iloc[0].to_dict() if not hotel_df.empty else None
        else:
            hotel = days_plan[-1].get("hotel")  # reuse same hotel

        # Costs
        def cost(p):
            if not p:
                return 0
            # Hỗ trợ cả cấu trúc cũ (flat) và mới (location wrapper)
            loc = p.get("location") if isinstance(p.get("location"), dict) else p
            val = (loc or {}).get("avgCost") if "avgCost" in (loc or {}) else (loc or {}).get("avg_cost")
            if val is None:
                val = (loc or {}).get("avgCost") or (loc or {}).get("avg_cost") or 0
            try:
                return float(val)
            except (ValueError, TypeError):
                return 0

        people = _get_people_count(intent.travel_companion)
        # Hotel cost is per-room per-night; multiply by rooms
        rooms = max(1, math.ceil(people / 2))

        # Tính cost cho attractions (morning/lunch/afternoon/evening)
        # People count: food/sightseeing cost tính theo số người (mỗi người 1 phần)
        attractions_cost = (
            cost(morning) + cost(lunch) + cost(afternoon) + cost(evening)
        ) * people

        # Hotel cost: tổng tiền phòng cho cả chuyến = (số đêm) × (cost/đêm) × (số phòng)
        # Số đêm = max(1, days - 1). Vì logic dùng cùng hotel cho cả chuyến,
        # chỉ tính 1 LẦN ở ngày đầu tiên (= requested_days - 1 đêm).
        hotel_cost = 0
        if d == 0:
            nights = max(1, requested_days - 1)
            hotel_cost = cost(hotel) * rooms * nights

        day_cost_total = int(attractions_cost + hotel_cost)

        # Strip plan_score columns to keep output clean
        def clean_place(p):
            if not p:
                return None
            out = {k: v for k, v in p.items() if k not in ("plan_score", "plan_score_breakdown", "plan_reasons")}
            return out

        days_plan.append({
            "day": day,
            "morning": clean_place(morning),
            "lunch": clean_place(lunch),
            "afternoon": clean_place(afternoon),
            "evening": clean_place(evening),
            "hotel": clean_place(hotel),
            "day_cost_estimate": int(day_cost_total),
        })

    return days_plan


def generate_plan_response(
    query: str,
    city: Optional[str] = None,
    days: Optional[int] = None,
    budget_total: Optional[int] = None,
    travel_companion: Optional[str] = None,
    max_secondary: int = 2,
) -> Dict[str, Any]:
    """
    Main entrypoint: take a user query, return a structured plan response.

    Returns:
    {
      "intent": { ... UserIntent ... },
      "primary_plan": { id, name, ..., reasons },
      "secondary_plans": [ ... ],
      "adapted_plan": { ... plan after day/budget adaptation ... },
      "itinerary": [ { day, morning, lunch, ... }, ... ],
      "total_cost_estimate": int,
      "budget_tier": "low" | "mid" | "high",
      "personality": { ... }
    }
    """
    # 1. Build intent
    intent = build_user_intent(
        query=query,
        city=city,
        days=days,
        budget_total=budget_total,
        travel_companion=travel_companion,
    )

    # 1b. PRIORITY: Try simple matcher (24 hard-coded plans)
    # If exact OR fuzzy match with high confidence, return immediately
    try:
        from .simple_matcher import match_simple_plan
        from .simple_endpoint import get_simple_plan_response
        simple_match = match_simple_plan(query or "")
        plan_id = simple_match.get("plan_id")
        match_score = simple_match.get("match_score", 0)
        # If plan_id exists (not None) AND score is high enough, use simple plan
        if plan_id and match_score >= 0.4:
            result = get_simple_plan_response(plan_id, query)
            if result:
                result["intent"] = intent.to_dict()
                result["match_type"] = simple_match.get("match_type", "unknown")
                result["match_score"] = match_score
                return result
        # If simple_matcher rejected (e.g. invalid city), still proceed to legacy scoring
        # but the legacy scoring won't find a match either, so we'll surface the rejection
    except Exception as e:
        print(f"[plan_engine] simple_matcher failed, falling back to scoring: {e}")

    # 2. Load plans
    plans_index = load_all_plans()

    # 3. Match primary + secondary
    primary, secondaries = select_primary_and_secondary(intent, plans_index, max_secondary=max_secondary)

    if not primary:
        # No matching plan: try with relaxed city
        if intent.city:
            intent2 = UserIntent(**{**intent.__dict__, "city": None})
            primary, secondaries = select_primary_and_secondary(intent2, plans_index, max_secondary=max_secondary)
        if not primary:
            return {
                "success": False,
                "error": "No matching plan found for the given intent",
                "error_detail": "Chỉ hỗ trợ 24 plan cố định cho Đà Nẵng / Hội An / Huế. Vui lòng dùng prompt từ rule.txt hoặc chọn 1 trong 3 thành phố Đà Nẵng / Hội An / Huế.",
                "intent": intent.to_dict(),
                "supported_cities": ["Đà Nẵng", "Hội An", "Huế"],
                "supported_plan_ids": [
                    "DN01-s", "DN02-s", "DN03-s", "DN04-s", "DN05-s",
                    "DNA01-s", "DNA02-s", "DNA03-s",
                    "HOI01-s", "HOI02-s", "HOI03-s", "HOI04-s", "HOI05-s",
                    "HOA01-s", "HOA02-s", "HOA03-s",
                    "HUE01-s", "HUE02-s", "HUE03-s", "HUE04-s", "HUE05-s",
                    "HUEA01-s", "HUEA02-s", "HUEA03-s",
                ],
            }

    # 4. Adapt plan to days + budget
    adapted, tier = adapt_plan_to_budget(primary.plan, intent.budget_total, intent.days)
    adapted = adapt_plan_to_days(adapted, intent.days)

    # 5. Build itinerary from adapted plan
    itinerary = build_itinerary_from_plan(adapted, intent)

    # 6. Total cost
    total_cost = sum(d.get("day_cost_estimate", 0) for d in itinerary)

    # 6b. Plan cost estimate: dùng budget_min/budget_max của plan
    # QUAN TRỌNG: budget_min/budget_max trong plan JSON là TỔNG cho cả chuyến (per person),
    # KHÔNG phải per-day. Theo docstring trong plan_matcher.py:
    #   "BUDGET_TIER_LOW_MAX = 4_000_000  # < 4M = low" - rõ ràng là tổng
    #   "Budget tier boundaries (VND per person for the whole trip)"
    # Nên KHÔNG nhân với requested_days, chỉ nhân với people_count.
    plan_budget_min = int(adapted.get("budget_min", 0) or primary.plan.get("budget_min", 0) or 0)
    plan_budget_max = int(adapted.get("budget_max", 0) or primary.plan.get("budget_max", 0) or 0)
    requested_days = intent.days or adapted.get("default_days", 3)
    people = _get_people_count(intent.travel_companion)

    # Cost ước tính cho cả nhóm (per person × số người)
    plan_cost_min = plan_budget_min * people
    plan_cost_max = plan_budget_max * people

    # Ưu tiên dùng cost từ plan (chính xác hơn dataset khi dataset có nhiều place avg_cost=0 miễn phí).
    # Chỉ dùng dataset sum khi plan không có budget (hiếm gặp).
    if plan_cost_max > 0:
        # Estimate = trung bình giữa min và max của plan × people
        final_cost_estimate = (plan_cost_min + plan_cost_max) // 2
        cost_source = "plan_budget"
    elif total_cost > 0:
        final_cost_estimate = int(total_cost)
        cost_source = "itinerary_sum"
    else:
        final_cost_estimate = 0
        cost_source = "unknown"

    # 7. Compose response
    response = {
        "success": True,
        "intent": intent.to_dict(),
        "primary_plan": {
            "id": primary.plan.get("id"),
            "name": primary.plan.get("name"),
            "plan_type": primary.plan.get("plan_type"),
            "city": primary.plan.get("city"),
            "description": primary.plan.get("description", ""),
            "default_days": primary.plan.get("default_days"),
            "default_nights": primary.plan.get("default_nights"),
            "budget_min": plan_budget_min,
            "budget_max": plan_budget_max,
            "travel_style": primary.plan.get("travel_style"),
            "intensity": primary.plan.get("intensity"),
            "tags": primary.plan.get("tags", []),
            "score": round(primary.score, 2),
            "matched_keywords": primary.matched_keywords,
            "reasons": primary.reasons,
            "breakdown": {k: round(v, 2) for k, v in primary.breakdown.__dict__.items()},
        },
        "secondary_plans": [
            {
                "id": s.plan.get("id"),
                "name": s.plan.get("name"),
                "plan_type": s.plan.get("plan_type"),
                "city": s.plan.get("city"),
                "description": s.plan.get("description", ""),
                "default_days": s.plan.get("default_days"),
                "default_nights": s.plan.get("default_nights"),
                "budget_min": int(s.plan.get("budget_min", 0) or 0),
                "budget_max": int(s.plan.get("budget_max", 0) or 0),
                "travel_style": s.plan.get("travel_style"),
                "intensity": s.plan.get("intensity"),
                "tags": s.plan.get("tags", []),
                "score": round(s.score, 2),
                "matched_keywords": s.matched_keywords,
                "reasons": s.reasons,
            }
            for s in secondaries
        ],
        "adapted_plan": {
            "id": adapted.get("id"),
            "name": adapted.get("name"),
            "default_days": adapted.get("default_days"),
            "requested_days": adapted.get("requested_days"),
            "adapted": adapted.get("adapted", False),
            "adapt_type": adapted.get("adapt_type"),
            "budget_tier": tier,
            "rules": adapted.get("rules", {}),
            "tags": adapted.get("tags", []),
        },
        "itinerary": itinerary,
        "total_cost_estimate": int(final_cost_estimate),
        "cost_min_estimate": int(plan_cost_min),
        "cost_max_estimate": int(plan_cost_max),
        "cost_source": cost_source,
        "budget_tier": tier,
        "days": requested_days,
        "personality": {
            "dominant_style": intent.dominant_style,
            "is_student": intent.is_student,
            "is_first_time": intent.is_first_time,
            "is_couple": intent.is_couple,
            "is_solo": intent.is_solo,
            "is_family": intent.is_family,
            "has_children": intent.has_children,
            "positive_preferences": intent.positive_preferences,
            "negative_preferences": intent.negative_preferences,
        },
    }
    return _sanitize_for_json(response)


def _sanitize_for_json(obj):
    """Recursively replace NaN/Inf floats with None, handle non-serializable types."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(x) for x in obj]
    if isinstance(obj, tuple):
        return [_sanitize_for_json(x) for x in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    return obj


def list_all_plans_for_ui() -> List[Dict[str, Any]]:
    """List all plans for the UI's suggested-plans gallery."""
    plans = list_all_plans()
    return [
        {
            "id": p.get("id"),
            "city": p.get("city"),
            "plan_type": p.get("plan_type"),
            "name": p.get("name"),
            "description": p.get("description"),
            "default_days": p.get("default_days"),
            "default_nights": p.get("default_nights"),
            "budget_min": p.get("budget_min"),
            "budget_max": p.get("budget_max"),
            "travel_style": p.get("travel_style"),
            "intensity": p.get("intensity"),
            "tags": p.get("tags", []),
        }
        for p in plans
    ]
