"""
Plan-aware place scoring.
Takes a list of places (DataFrame rows) and a plan, computes a per-place score
using the plan's preferred_categories / preferred_tags / excluded_tags /
preferred_price_levels / scoring weights, and returns the places sorted
descending by score.

This is a layer on top of the existing recommender.py — it does NOT replace
the semantic search, it ADDS plan-driven re-ranking AFTER retrieval.

Design:
  - Input: pd.DataFrame of place rows (from data/places_clean.csv or filtered subset)
            + a plan dict + UserIntent
  - Output: same DataFrame with extra columns:
      - plan_score: final plan-aware score (0-100)
      - plan_score_breakdown: dict of component scores
      - plan_reasons: list of human-readable reasons
  - Sorted by plan_score descending
"""
from __future__ import annotations
import re
import math
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple


def _norm(s: Any) -> str:
    if s is None or (isinstance(s, float) and (math.isnan(s) or math.isinf(s))):
        return ""
    return str(s).strip().lower()


def _split_tags(raw: Any) -> List[str]:
    """Split a tag cell into list of lowercased tokens. Handles ';' or ',' separator."""
    if raw is None or (isinstance(raw, float) and (math.isnan(raw) or math.isinf(raw))):
        return []
    s = str(raw)
    for sep in [";", ","]:
        if sep in s:
            return [t.strip().lower() for t in s.split(sep) if t.strip()]
    # single tag
    return [s.strip().lower()] if s.strip() else []


def _parse_price_level(value: Any) -> int:
    """Map '$', '$$', '$$$' to 1, 2, 3. Unknown -> 2."""
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return 2
    s = str(value).strip()
    if s == "$":
        return 1
    if s == "$$":
        return 2
    if s == "$$$":
        return 3
    return 2


def _parse_closed_days(raw: Any) -> set:
    """Parse closed_days cell into set of weekday ints (0=Mon)."""
    if raw is None or (isinstance(raw, float) and (math.isnan(raw) or math.isinf(raw))):
        return set()
    s = str(raw).strip().lower()
    if not s:
        return set()
    days_map = {
        "mon": 0, "monday": 0, "thứ 2": 0, "thứ hai": 0, "t2": 0,
        "tue": 1, "tuesday": 1, "thứ 3": 1, "thứ ba": 1, "t3": 1,
        "wed": 2, "wednesday": 2, "thứ 4": 2, "thứ tư": 2, "t4": 2,
        "thu": 3, "thursday": 3, "thứ 5": 3, "thứ năm": 3, "t5": 3,
        "fri": 4, "friday": 4, "thứ 6": 4, "thứ sáu": 4, "t6": 4,
        "sat": 5, "saturday": 5, "thứ 7": 5, "thứ bảy": 5, "t7": 5,
        "sun": 6, "sunday": 6, "chủ nhật": 6, "cn": 6,
    }
    out = set()
    for k, v in days_map.items():
        if k in s:
            out.add(v)
    return out


def _parse_time_minutes(raw: Any) -> Optional[int]:
    """Parse HH:MM or H:MM to minutes since midnight."""
    if raw is None or (isinstance(raw, float) and (math.isnan(raw) or math.isinf(raw))):
        return None
    s = str(raw).strip()
    m = re.match(r"^(\d{1,2}):(\d{2})$", s)
    if not m:
        return None
    h, mm = int(m.group(1)), int(m.group(2))
    if 0 <= h < 24 and 0 <= mm < 60:
        return h * 60 + mm
    return None


def _bayesian_rating(rating: float, review_count: int, dataset_mean: float, m: float = 50.0) -> float:
    """Bayesian average to weight rating by review confidence.
    m = minimum reviews threshold. Higher m = more weight on dataset mean.
    """
    if rating is None or np.isnan(rating) or rating == 0:
        return dataset_mean
    if review_count is None or np.isnan(review_count) or review_count <= 0:
        return dataset_mean
    return (review_count / (review_count + m)) * rating + (m / (review_count + m)) * dataset_mean


def _normalize(value: float, vmin: float, vmax: float) -> float:
    """Normalize value to 0-1. If vmax == vmin, return 0.5."""
    if vmax <= vmin:
        return 0.5
    return max(0.0, min(1.0, (value - vmin) / (vmax - vmin)))


def score_place(
    place: Dict[str, Any],
    plan: Dict[str, Any],
    dataset_mean_rating: float = 4.0,
    rating_min: float = 0.0,
    rating_max: float = 5.0,
    cost_min: float = 0.0,
    cost_max: float = 1_000_000.0,
) -> Dict[str, Any]:
    """
    Score a single place against a plan. Returns a dict with:
      - plan_score: 0-100
      - breakdown: dict of component scores (0-1 each)
      - reasons: list of human-readable strings
    """
    # ---- Parse fields ----
    name = _norm(place.get("name"))
    category = _norm(place.get("category"))
    tags = _split_tags(place.get("tags"))
    price_level_int = _parse_price_level(place.get("price_level"))

    rating = float(place.get("rating") or 0)
    review_count = float(place.get("review_count") or 0)
    popularity = float(place.get("popularity") or 0)
    avg_cost = float(place.get("avg_cost") or 0)

    # ---- Component scores (each 0-1) ----

    # 1. Category match
    plan_categories = [_norm(c) for c in plan.get("preferred_categories", [])]
    cat_match = 1.0 if category in plan_categories else 0.0
    if not plan_categories:
        cat_match = 0.5  # neutral if plan has no category preference

    # 2. Tag match (Jaccard-like)
    plan_tags = [_norm(t) for t in plan.get("preferred_tags", []) if t]
    plan_excluded = [_norm(t) for t in plan.get("excluded_tags", []) if t]
    if plan_tags:
        matched = sum(1 for t in plan_tags if any(t in pt or pt in t for pt in tags))
        tag_match = matched / len(plan_tags)
    else:
        tag_match = 0.5

    # 3. Price level match
    plan_prices = plan.get("preferred_price_levels", [])
    if plan_prices:
        plan_price_ints = [_parse_price_level(p) for p in plan_prices]
        if price_level_int in plan_price_ints:
            price_match = 1.0
        else:
            # distance penalty
            dist = min(abs(price_level_int - pi) for pi in plan_price_ints)
            price_match = max(0.0, 1.0 - dist * 0.5)
    else:
        price_match = 0.5

    # 4. Rating (Bayesian-adjusted, then normalized)
    adj_rating = _bayesian_rating(rating, review_count, dataset_mean_rating)
    rating_score = _normalize(adj_rating, rating_min, rating_max)

    # 5. Review confidence (count signal)
    # We use log-scaled review count
    if review_count > 0:
        review_score = min(1.0, math.log10(review_count + 1) / 5.0)  # log10(100000)=5
    else:
        review_score = 0.0

    # 6. Popularity (0-1)
    pop_score = _normalize(popularity, 0.0, 1.0)

    # 7. Budget fit (cost in plan's range)
    rules = plan.get("rules", {})
    max_price_level_str = rules.get("max_price_level")
    max_avg_cost = rules.get("max_avg_cost")
    budget_match = 1.0
    if max_avg_cost and avg_cost > max_avg_cost:
        budget_match = max(0.0, 1.0 - (avg_cost - max_avg_cost) / max(1, max_avg_cost))
    if max_price_level_str:
        max_pi = _parse_price_level(max_price_level_str)
        if price_level_int > max_pi:
            budget_match *= max(0.0, 1.0 - (price_level_int - max_pi) * 0.4)

    # 8. Min rating gate
    min_rating = rules.get("min_rating")
    if min_rating and rating and rating < min_rating:
        budget_match = 0.0  # effectively disqualifies

    # 9. Min review count gate
    min_review = rules.get("min_review_count")
    if min_review and review_count and review_count < min_review:
        budget_match *= 0.4  # soften penalty

    # 10. Max popularity gate (for quiet plans)
    max_pop = rules.get("max_popularity")
    if max_pop is not None and popularity > max_pop:
        budget_match *= 0.3  # soft penalty

    # 11. Excluded tag penalty
    excluded_penalty = 0.0
    if plan_excluded:
        hits = sum(1 for t in plan_excluded if any(t in pt or pt in t for pt in tags))
        excluded_penalty = min(1.0, hits * 0.5)

    # 12. Plan weight multipliers
    budget_w = plan.get("budget_weight", 0.7)
    rating_w = plan.get("rating_weight", 1.0)
    popularity_w = plan.get("popularity_weight", 1.0)
    distance_w = plan.get("distance_weight", 0.8)
    preference_w = plan.get("preference_weight", 1.0)

    # ---- Combine (each 0-1) ----
    # Per spec section 6: preferenceMatch 25, tagMatch 15, categoryMatch 15,
    # budgetFit 10, rating 8, reviewConfidence 5, popularity 5, ...
    # Here we use simpler weights and apply plan multipliers on top.

    # Sub-scores
    s_pref = (cat_match * 0.5 + tag_match * 0.5) * preference_w   # combined
    s_budget = budget_match * budget_w
    s_rating = rating_score * rating_w
    s_review = review_score
    s_pop = pop_score * popularity_w

    # Combine into 0-100
    # Weighted sum, then add tag/category contribution
    raw = (
        25.0 * s_pref +
        10.0 * s_budget +
        8.0 * s_rating +
        5.0 * s_review +
        5.0 * s_pop
    ) / (25.0 + 10.0 + 8.0 + 5.0 + 5.0)

    # Penalty for excluded tags
    raw *= (1.0 - excluded_penalty * 0.7)

    plan_score = round(max(0.0, min(100.0, raw)), 2)

    # Build reasons
    reasons: List[str] = []
    if cat_match >= 1.0:
        reasons.append(f"category '{category}' khớp plan")
    if tag_match >= 0.5:
        # find which tag matched
        for t in plan_tags:
            if any(t in pt or pt in t for pt in tags):
                reasons.append(f"tag '{t}' khớp")
                break
    if budget_match >= 0.9:
        reasons.append("trong tầm giá")
    elif budget_match < 0.4:
        reasons.append("giá ngoài ngân sách")
    if rating_score >= 0.85:
        reasons.append(f"rating cao ({rating:.1f}/5)")
    if review_score >= 0.7:
        reasons.append(f"nhiều review ({int(review_count):,})")
    if excluded_penalty > 0:
        reasons.append("bị loại bởi excluded tags")
    if max_pop is not None and popularity > max_pop:
        reasons.append("popularity cao (có thể đông)")

    return {
        "plan_score": plan_score,
        "breakdown": {
            "category_match": round(cat_match, 3),
            "tag_match": round(tag_match, 3),
            "price_match": round(price_match, 3),
            "rating": round(rating_score, 3),
            "review_confidence": round(review_score, 3),
            "popularity": round(pop_score, 3),
            "budget_fit": round(budget_match, 3),
            "excluded_penalty": round(excluded_penalty, 3),
        },
        "reasons": reasons,
    }


def rank_places_by_plan(
    df: pd.DataFrame,
    plan: Dict[str, Any],
    exclude_place_ids: Optional[List[int]] = None,
) -> pd.DataFrame:
    """
    Score and rank all places in df according to plan.
    Returns the same df with extra columns, sorted by plan_score desc.
    """
    if df is None or df.empty:
        return df
    if exclude_place_ids is None:
        exclude_place_ids = []
    exclude_set = set(int(x) for x in exclude_place_ids if x is not None)

    # Dataset mean rating for Bayesian adjustment
    if "rating" in df.columns:
        valid_ratings = df["rating"].apply(lambda x: float(x) if pd.notna(x) and x > 0 else None)
        valid_ratings = [r for r in valid_ratings if r is not None]
        dataset_mean = float(np.mean(valid_ratings)) if valid_ratings else 4.0
    else:
        dataset_mean = 4.0

    # Compute score per row
    scores: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        # Skip excluded IDs
        try:
            pid = int(row.get("id", -1))
        except (ValueError, TypeError):
            pid = -1
        if pid in exclude_set:
            continue
        s = score_place(row.to_dict(), plan, dataset_mean_rating=dataset_mean)
        scores.append(s)

    if not scores:
        df_out = df.copy()
        df_out["plan_score"] = 0.0
        df_out["plan_score_breakdown"] = None
        df_out["plan_reasons"] = None
        return df_out

    # Add to df
    df_out = df.copy()
    df_out["plan_score"] = [s["plan_score"] for s in scores]
    df_out["plan_score_breakdown"] = [s["breakdown"] for s in scores]
    df_out["plan_reasons"] = [s["reasons"] for s in scores]

    # Sort
    df_out = df_out.sort_values("plan_score", ascending=False).reset_index(drop=True)
    return df_out


# ---- Public utility: dataset filter for plan ----

def filter_places_for_plan(
    df: pd.DataFrame,
    plan: Dict[str, Any],
    city: Optional[str] = None,
) -> pd.DataFrame:
    """Apply hard filters: city, price level, basic gates.
    Does NOT score — just filter candidates."""
    if df is None or df.empty:
        return df
    out = df.copy()

    if city and "city" in out.columns:
        city_norm = _norm(city)
        # Map canonical key to display names
        city_display_map = {
            "danang": ["Da Nang", "Đà Nẵng"],
            "hoian": ["Hoi An", "Hội An"],
            "hue": ["Hue", "Huế"],
        }
        display_names = city_display_map.get(city_norm, [city])
        out = out[out["city"].astype(str).str.strip().isin(display_names)]

    # max price level
    rules = plan.get("rules", {})
    max_pl = rules.get("max_price_level")
    if max_pl and "price_level" in out.columns:
        max_pi = _parse_price_level(max_pl)
        out = out[out["price_level"].apply(lambda x: _parse_price_level(x) <= max_pi)]

    # min rating (soft - keep but lower weight later)
    # Not filtered here so we have fallback

    return out
