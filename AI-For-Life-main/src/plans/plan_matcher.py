"""
Plan matcher - score plans against a UserIntent.
Returns ranked list of PlanMatchResult.
"""
from __future__ import annotations
import re
import unicodedata
from typing import List, Dict, Tuple, Optional, Any

from .plan_model import PlanScoreBreakdown, PlanMatchResult, UserIntent
from .index import _normalize_city, get_plan_by_id


def _no_accent(s: str) -> str:
    """Remove diacritics for accent-insensitive matching."""
    if not s:
        return ""
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


# Default scoring weights (per spec section 20)
DEFAULT_WEIGHTS = {
    "city": 40,
    "intent": 20,
    "preference": 20,
    "budget": 10,
    "days": 5,
    "traveler_type": 5,
}

# Budget tier boundaries (VND per person for the whole trip)
BUDGET_TIER_LOW_MAX = 4_000_000       # < 4M = low
BUDGET_TIER_MID_MAX = 7_000_000       # 4-7M = mid
                                  # > 7M = high


def classify_budget_tier(budget_total: Optional[int], days: Optional[int] = None) -> str:
    """Classify budget into 'low', 'mid', or 'high'."""
    if not budget_total:
        return "mid"
    # If user gave per-day budget, convert to total
    total = budget_total
    if days and days > 0:
        # Heuristic: if budget feels like per-day (very small), scale up
        if total < 2_000_000 and days > 1:
            total = total * days
    if total < BUDGET_TIER_LOW_MAX:
        return "low"
    if total < BUDGET_TIER_MID_MAX:
        return "mid"
    return "high"


def _keyword_match_score(plan: Dict[str, Any], query: str) -> Tuple[float, List[str]]:
    """Score plan against intent_keywords + preference_keywords in query.
    intent_keywords weighted higher than preference_keywords."""
    if not query:
        return 0.0, []
    q = " ".join(query.lower().split())
    score = 0.0
    matched: List[str] = []
    intent_kws = plan.get("intent_keywords", [])
    pref_kws = plan.get("preference_keywords", [])

    for kw in intent_kws:
        if kw and kw.lower() in q:
            score += 3.0  # strong signal
            matched.append(kw)
    for kw in pref_kws:
        if kw and kw.lower() in q:
            score += 1.0
            matched.append(kw)
    # Cap at 20
    return min(20.0, score), matched


def _budget_score(plan: Dict[str, Any], budget_total: Optional[int], budget_per_day: Optional[int], days: Optional[int]) -> Tuple[float, str]:
    """Score plan's budget fit."""
    if not budget_total:
        return 5.0, "no budget specified"
    plan_min = plan.get("budget_min", 0)
    plan_max = plan.get("budget_max", float("inf"))
    if plan_min <= budget_total <= plan_max:
        return 10.0, "trong khoảng ngân sách"
    if budget_total < plan_min:
        # User has less than plan's minimum
        diff_ratio = (plan_min - budget_total) / max(1, plan_min)
        return max(0.0, 5.0 - diff_ratio * 10.0), "dưới mức tối thiểu của plan"
    # User has more than plan's max (plan feels cheap)
    diff_ratio = (budget_total - plan_max) / max(1, plan_max)
    return max(0.0, 7.0 - diff_ratio * 7.0), "trên mức tối đa của plan"


def _days_score(plan: Dict[str, Any], days: Optional[int]) -> Tuple[float, str]:
    """Score plan's duration fit. Plans can adapt, so partial credit."""
    if not days:
        return 3.0, "no duration specified"
    default_days = plan.get("default_days", 3)
    diff = abs(days - default_days)
    if diff == 0:
        return 5.0, "khớp default"
    if diff == 1:
        return 4.0, "lệch 1 ngày (vẫn adapt OK)"
    if diff == 2:
        return 3.0, "lệch 2 ngày (sẽ adapt)"
    if diff == 3:
        return 2.0, "lệch 3 ngày (adapt mạnh)"
    return 1.0, "lệch nhiều ngày"


def _traveler_score(plan: Dict[str, Any], intent: UserIntent) -> Tuple[float, str]:
    """Score based on traveler type fit."""
    suitable = plan.get("suitable_for", [])
    score = 0.0
    reasons: List[str] = []

    if intent.is_couple and "couple" in suitable:
        score += 2.0
        reasons.append("phù hợp cặp đôi")
    if intent.is_family and "family" in suitable:
        score += 2.0
        reasons.append("phù hợp gia đình")
    if intent.is_solo and "solo" in suitable:
        score += 1.5
        reasons.append("phù hợp solo")
    if intent.is_student and "student" in suitable:
        score += 1.5
        reasons.append("phù hợp sinh viên")
    if intent.is_first_time and "first-time" in suitable:
        score += 1.0
        reasons.append("phù hợp first-time")

    # Style match (companion)
    if intent.dominant_style and intent.dominant_style in suitable:
        score += 1.0
        reasons.append(f"phù hợp style {intent.dominant_style}")

    return min(5.0, score), "; ".join(reasons) if reasons else "không rõ ràng"


def _preference_score(plan: Dict[str, Any], intent: UserIntent) -> Tuple[float, List[str]]:
    """Score based on positive/negative preference matching."""
    score = 0.0
    matched: List[str] = []

    plan_style = plan.get("travel_style", "")
    plan_tags = [t.lower() for t in plan.get("preferred_tags", [])]
    plan_excluded = [t.lower() for t in plan.get("excluded_tags", [])]

    # Strong boost if dominant_style matches plan's travel_style
    if intent.dominant_style and intent.dominant_style == plan_style:
        score += 12.0
        matched.append(f"dominant_style={intent.dominant_style}")

    # Boost if dominant_style appears in plan tags
    if intent.dominant_style:
        ds = intent.dominant_style.lower()
        if any(ds in tag for tag in plan_tags):
            score += 4.0
            matched.append(f"tag-matches-{ds}")

    # Penalty for negative preferences matching plan's content
    for neg in intent.negative_preferences:
        neg_lower = neg.lower()
        if neg_lower in plan_excluded:
            # This is GOOD - the plan excludes the same thing
            score += 2.0
            matched.append(f"avoids:{neg}")
        elif neg_lower in plan_tags or any(neg_lower in t for t in plan_tags):
            # This is BAD - plan promotes what user dislikes
            score -= 5.0
            matched.append(f"conflict:{neg}")
        # Special: "touristy" penalty
        if neg_lower == "touristy" and plan.get("plan_type") == "core":
            score -= 1.0

    # Boost for adaptive triggers matching adaptive plans
    if plan.get("plan_type") == "adaptive":
        plan_id = plan.get("id", "").lower()
        for trig in (intent.positive_preferences + ([intent.dominant_style] if intent.dominant_style else [])):
            if trig and trig.lower() in plan_id:
                score += 3.0
                matched.append(f"adaptive-trigger:{trig}")

    return min(20.0, score), matched


def _city_score(plan: Dict[str, Any], city: Optional[str]) -> Tuple[float, bool]:
    """Check city match. Returns (score, matches)."""
    if not city:
        return 0.0, False
    plan_city = plan.get("city", "")
    norm = _normalize_city(city)
    if plan_city == norm:
        return 40.0, True
    return 0.0, False


def match_plan(
    plan: Dict[str, Any],
    intent: UserIntent,
    city_norm: Optional[str] = None,
) -> PlanMatchResult:
    """Score a single plan against an intent."""
    breakdown = PlanScoreBreakdown()

    if city_norm is None:
        city_norm = _normalize_city(intent.city) if intent.city else None

    # 1. City (40) - hard gate
    city_sc, city_match = _city_score(plan, city_norm)
    breakdown.city_match = city_sc

    # If city doesn't match, this plan is not a candidate
    if city_norm and not city_match:
        return PlanMatchResult(
            plan=plan,
            score=0.0,
            breakdown=breakdown,
            matched_keywords=[],
            reasons=["city mismatch"],
            role="primary",
        )

    # 2. Intent (20) - strong signals from query
    intent_sc, intent_matched = _keyword_match_score(plan, intent.raw_query)
    breakdown.intent_match = intent_sc

    # 3. Preference (20) - personality match
    pref_sc, pref_matched = _preference_score(plan, intent)
    breakdown.preference_match = pref_sc

    # 4. Budget (10)
    budget_sc, budget_reason = _budget_score(
        plan, intent.budget_total, intent.budget_per_day, intent.days
    )
    breakdown.budget_match = budget_sc

    # 5. Days (5)
    days_sc, days_reason = _days_score(plan, intent.days)
    breakdown.days_match = days_sc

    # 6. Traveler type (5)
    trav_sc, trav_reason = _traveler_score(plan, intent)
    breakdown.traveler_type_match = trav_sc

    # Total
    total = (
        breakdown.city_match
        + breakdown.intent_match
        + breakdown.preference_match
        + breakdown.budget_match
        + breakdown.days_match
        + breakdown.traveler_type_match
    )

    # Build human-readable reasons
    reasons: List[str] = []
    if breakdown.city_match > 0:
        reasons.append(f"thành phố khớp ({plan.get('city')})")
    if intent_matched:
        reasons.append(f"keyword trùng: {', '.join(intent_matched[:3])}")
    if intent.dominant_style and intent.dominant_style == plan.get("travel_style"):
        reasons.append(f"phong cách {plan.get('travel_style')} khớp với tính cách bạn")
    if budget_reason:
        reasons.append(f"ngân sách: {budget_reason}")
    if days_reason:
        reasons.append(f"thời gian: {days_reason}")
    if trav_reason:
        reasons.append(trav_reason)
    if plan.get("plan_type") == "adaptive" and intent.dominant_style:
        reasons.append("adaptive plan - ưu tiên theo tính cách")

    return PlanMatchResult(
        plan=plan,
        score=total,
        breakdown=breakdown,
        matched_keywords=intent_matched + pref_matched,
        reasons=reasons,
        role="primary",
    )


def match_all_plans(
    intent: UserIntent,
    plans_index: Dict[str, List[Dict[str, Any]]],
) -> List[PlanMatchResult]:
    """Score all plans and return sorted list (highest first)."""
    city_norm = _normalize_city(intent.city) if intent.city else None
    results: List[PlanMatchResult] = []
    for city_key, plans in plans_index.items():
        for p in plans:
            # Filter out other cities early
            if city_norm and p.get("city") != city_norm:
                continue
            r = match_plan(p, intent, city_norm=city_norm)
            if r.score > 0:
                results.append(r)
    results.sort(key=lambda x: x.score, reverse=True)
    return results


def select_primary_and_secondary(
    intent: UserIntent,
    plans_index: Dict[str, List[Dict[str, Any]]],
    max_secondary: int = 2,
) -> Tuple[Optional[PlanMatchResult], List[PlanMatchResult]]:
    """
    Pick the best primary plan and up to max_secondary secondary plans.

    Strategy (priority order):
      1. STRONG ADAPTIVE TRIGGER: If user has a dominant_style that exactly matches
         an adaptive plan's travel_style, that adaptive plan wins.
      2. ADAPTIVE TRIGGER (weak): If user has any adaptive trigger, prefer
         the matching adaptive plan over core plans.
      3. CORE MATCH: Pick highest-scoring plan (works for "first time", "balanced", etc.)
      4. Secondaries: top max_secondary complementary plans.
    """
    all_matches = match_all_plans(intent, plans_index)
    if not all_matches:
        return None, []

    primary = None
    primary_reason = ""

    # Strategy 1 & 2: Adaptive plan priority
    if intent.dominant_style:
        ds = intent.dominant_style
        # Find best adaptive plan whose travel_style matches dominant_style
        adaptive_matches = [
            r for r in all_matches
            if r.plan.get("plan_type") == "adaptive"
            and r.plan.get("travel_style") == ds
        ]
        if adaptive_matches:
            adaptive_top = max(adaptive_matches, key=lambda x: x.score)
            # Check if there's a core plan with the SAME travel_style
            core_same_style = [
                r for r in all_matches
                if r.plan.get("plan_type") == "core"
                and r.plan.get("travel_style") == ds
            ]
            if core_same_style:
                core_top = max(core_same_style, key=lambda x: x.score)
                # If user has STRONG signal words (rất thích, cực kỳ, đam mê),
                # prefer adaptive (it's the "extreme" version of that style)
                q_lower = (intent.raw_query or "").lower()
                q_no_accent = _no_accent(q_lower)
                strong_intensifiers = ["rat thich", "cuc ky", "dam me", "yeu thich", "dien cuong", "sieu thich"]
                has_intensifier = any(w in q_no_accent for w in strong_intensifiers)

                if ds == "budget":
                    # Check for foodie plan that may have lost due to lower score
                    foodie_cores = [
                        r for r in all_matches
                        if r.plan.get("plan_type") == "core"
                        and r.plan.get("travel_style") == "foodie"
                        and any("food" in mk.lower() or "am thuc" in mk.lower() or "an" in mk.lower()
                                for mk in r.matched_keywords)
                    ]
                    if foodie_cores:
                        ft = max(foodie_cores, key=lambda x: x.score)
                        if ft.score >= adaptive_top.score * 0.85:
                            primary = ft
                            primary.reasons.insert(0, "core foodie plan match via 'ăn/uống' intent")
                            primary_reason = f"core:foodie-override-budget"

                if primary is None:
                    if has_intensifier and adaptive_top.score >= 30.0:
                        # Strong user signal: prefer adaptive
                        primary = adaptive_top
                        primary.reasons.insert(0, f"adaptive plan '{ds}' (user có cường từ)")
                        primary_reason = f"adaptive:{ds}:intensifier"
                    elif core_top.score > adaptive_top.score:
                        primary = core_top
                        primary.reasons.insert(0, f"core plan cho style '{ds}' (preferred over adaptive)")
                        primary_reason = f"core:{ds}"
                    elif core_top.score == adaptive_top.score:
                        # Tie: prefer core (more general / balanced) UNLESS user used a strong trigger word
                        trigger_words = [
                            "rat thich", "cuc ky", "dam me", "yeu thich",
                            "thich", "kham pha", "kham", "tim hieu",
                        ]
                        # Strip accents on user query
                        q_no = _no_accent((intent.raw_query or "").lower())
                        has_trigger = any(w in q_no for w in trigger_words)
                        if has_trigger:
                            primary = adaptive_top
                            primary.reasons.insert(0, f"adaptive plan '{ds}' (user có trigger word)")
                            primary_reason = f"adaptive:{ds}:trigger"
                        else:
                            primary = core_top
                            primary.reasons.insert(0, f"core plan cho style '{ds}' (tie-break → core)")
                            primary_reason = f"core:{ds}:tie"
                    else:
                        primary = adaptive_top
                        primary.reasons.insert(0, f"adaptive plan cho style '{ds}'")
                        primary_reason = f"adaptive:{ds}"
            else:
                primary = adaptive_top
                primary.reasons.insert(0, f"adaptive plan cho style '{ds}'")
                primary_reason = f"adaptive:{ds}"

    # Strategy 3: Highest overall score (when no adaptive plan fits or no dominant_style)
    if primary is None:
        # Prefer core plans (more general-purpose / well-rounded)
        core_matches = [r for r in all_matches if r.plan.get("plan_type") == "core"]
        adaptive_matches = [r for r in all_matches if r.plan.get("plan_type") == "adaptive"]
        if core_matches:
            # Small tie-break: when no personality was detected, prefer plans with
            # balanced/general travel_style (DN01, HOI01, HUE01) over specific ones.
            if intent.dominant_style is None:
                def core_pref(r):
                    s = r.score
                    style = r.plan.get("travel_style", "")
                    # First-trip / heritage plans are the canonical default
                    if r.plan.get("id") in ("DN01", "HOI01", "HUE01"):
                        s += 2.0
                    if style in ("balanced", "sightseeing", "heritage"):
                        s += 1.5
                    return s
                core_top = max(core_matches, key=core_pref)
            else:
                core_top = max(core_matches, key=lambda x: x.score)
            adaptive_top = max(adaptive_matches, key=lambda x: x.score) if adaptive_matches else None
            if adaptive_top and adaptive_top.score > core_top.score * 1.15:
                primary = adaptive_top
                primary.reasons.insert(0, f"adaptive plan vượt trội (score {adaptive_top.score:.1f} vs core {core_top.score:.1f})")
                primary_reason = f"adaptive:dominant-by-score"
            else:
                primary = core_top
                primary.reasons.insert(0, f"core plan phù hợp nhất")
                primary_reason = f"core:highest"
        else:
            # No core plans — pick highest overall
            all_matches.sort(key=lambda x: x.score, reverse=True)
            primary = all_matches[0]
            primary_reason = "highest_score"

    primary.role = "primary"

    # Build secondaries: exclude primary, prefer those that complement
    # (i.e. different travel_style from primary)
    others = [r for r in all_matches if r.plan.get("id") != primary.plan.get("id")]
    primary_style = primary.plan.get("travel_style", "")

    def secondary_score(r):
        # Prefer different style (complement), but keep some score
        s = r.score
        if r.plan.get("travel_style") != primary_style and r.plan.get("plan_type") == "core":
            s += 3.0  # small boost for complement
        return s

    others.sort(key=secondary_score, reverse=True)
    secondaries: List[PlanMatchResult] = []
    for r in others:
        if r.score < 5.0:  # absolute floor
            break
        r.role = "secondary"
        secondaries.append(r)
        if len(secondaries) >= max_secondary:
            break

    return primary, secondaries
