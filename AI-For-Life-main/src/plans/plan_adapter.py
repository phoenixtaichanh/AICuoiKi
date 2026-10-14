"""
Plan adaptations:
  - DayAdapter: compress/expand itinerary to fit user-requested number of days
  - BudgetAdapter: re-weight plan scoring + recompute per-day budget based on tier

These adapters do NOT change plan metadata on disk; they produce
runtime overrides that the recommender uses.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple

from .plan_model import UserIntent
from .plan_matcher import classify_budget_tier, BUDGET_TIER_LOW_MAX, BUDGET_TIER_MID_MAX


# Heuristic: how many "core" places per day each pace produces
PACE_PLACES_PER_DAY = {
    "slow": 2.5,
    "balanced": 3.5,
    "active": 4.5,
}


def adapt_plan_to_days(plan: Dict[str, Any], requested_days: Optional[int]) -> Dict[str, Any]:
    """
    Returns a copy of plan with adjusted rules for the requested day count.

    If requested_days is None or equals default_days, return plan as-is.

    If requested_days > default_days: expand max_places_per_day, relax min_relax_time.
    If requested_days < default_days: tighten max_places_per_day, increase min_relax_time.
    """
    if not requested_days or requested_days <= 0:
        return dict(plan)
    plan = dict(plan)  # shallow copy
    default_days = plan.get("default_days", 3)
    # Always record requested_days (even if equal) for downstream consumers
    plan["requested_days"] = requested_days
    plan["day_diff"] = requested_days - default_days
    if requested_days == default_days:
        plan["adapted"] = False
        plan["adapt_type"] = None
        return plan

    plan["adapted"] = True
    plan["adapt_type"] = "expand" if requested_days > default_days else "compress"

    # Adjust rules
    rules = dict(plan.get("rules", {}))
    default_max = rules.get("max_places_per_day", 4)
    default_relax = rules.get("min_relax_time_per_day", 60)

    if requested_days > default_days:
        # Expand: keep density, can add free time / cafe
        rules["max_places_per_day"] = max(default_max, int(default_max * 1.1) + 1)
        rules["min_relax_time_per_day"] = max(30, default_relax - 15)
    else:
        # Compress: fewer places per day
        reduction = default_days / max(1, requested_days)
        new_max = max(1, int(default_max / max(1.1, reduction)))
        rules["max_places_per_day"] = new_max
        rules["min_relax_time_per_day"] = min(240, default_relax + 30)

    plan["rules"] = rules
    return plan


def adapt_plan_to_budget(plan: Dict[str, Any], user_budget_total: Optional[int], days: Optional[int]) -> Tuple[Dict[str, Any], str]:
    """
    Adapt plan scoring weights based on user's budget tier.

    Returns (adapted_plan, tier_label).
    """
    tier = classify_budget_tier(user_budget_total, days)
    plan = dict(plan)  # shallow copy
    plan["budget_tier"] = tier
    plan["adapted"] = True

    # Recompute weights
    base_budget_w = plan.get("budget_weight", 0.7)
    base_rating_w = plan.get("rating_weight", 1.0)
    base_pop_w = plan.get("popularity_weight", 1.0)
    base_dist_w = plan.get("distance_weight", 0.8)
    base_pref_w = plan.get("preference_weight", 1.0)

    if tier == "low":
        # User is budget-conscious: amplify budget weight, reduce preference/luxury tags
        plan["budget_weight"] = base_budget_w * 1.5
        plan["rating_weight"] = base_rating_w * 0.9
        plan["popularity_weight"] = base_pop_w
        plan["distance_weight"] = base_dist_w * 0.8  # less travel = less cost
        plan["preference_weight"] = base_pref_w * 1.2
        # Tighten max price level
        rules = dict(plan.get("rules", {}))
        rules.setdefault("max_price_level", "$")
        plan["rules"] = rules
    elif tier == "high":
        # User has more money: amplify rating + preference, reduce budget constraint
        plan["budget_weight"] = base_budget_w * 0.6
        plan["rating_weight"] = base_rating_w * 1.3
        plan["popularity_weight"] = base_pop_w * 0.9
        plan["distance_weight"] = base_dist_w
        plan["preference_weight"] = base_pref_w * 1.2
    else:
        # mid: leave mostly as-is
        plan["budget_weight"] = base_budget_w
        plan["rating_weight"] = base_rating_w
        plan["popularity_weight"] = base_pop_w
        plan["distance_weight"] = base_dist_w
        plan["preference_weight"] = base_pref_w

    return plan, tier


def compute_per_day_budget(budget_total: Optional[int], days: Optional[int], people_count: int = 1) -> int:
    """Compute per-day-per-person budget."""
    if not budget_total or not days or days <= 0:
        return 1_000_000  # default 1M/day
    per_day = budget_total // days
    return max(100_000, per_day)
