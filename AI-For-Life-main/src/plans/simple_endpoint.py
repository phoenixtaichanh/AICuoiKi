"""
Simple match endpoint - match simple prompts to 24 hard-coded plans.
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
import json

from .simple_matcher import match_simple_plan, get_simple_plan, SIMPLE_PROMPTS


def get_simple_plan_response(plan_id: str, query: str) -> dict:
    """Build full plan response from a hard-coded simple plan."""
    plan = get_simple_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

    # Calculate itinerary as Day list
    itinerary = []
    for d, day in enumerate(plan.get("days", [])):
        # Preserve activities exactly as in plan (don't filter to single object)
        activities = []
        for act in day.get("activities", []):
            loc = act.get("location")
            activities.append({
                "time": act.get("time", ""),
                "period": act.get("period", ""),
                "type": act.get("type", ""),
                "location": loc,
                "description": act.get("description", ""),
                "costPerPerson": act.get("costPerPerson", loc.get("avgCost", 0) if loc else 0),
                "durationMinutes": act.get("durationMinutes", loc.get("durationMinutes", 60) if loc else 60),
                "travelFromPreviousMinutes": act.get("travelFromPreviousMinutes"),
            })

        # Find hotel for this day
        hotel = None
        for a in activities:
            if a.get("type") == "hotel":
                hotel = a.get("location")
                break
        if not hotel:
            hotel = plan.get("hotel")

        # Group activities by period (Sáng / Trưa / Chiều / Tối / Cả ngày)
        # Each period can have multiple activities (e.g., Sáng có Mỳ Quảng + Bãi biển)
        def by_period(period):
            return [a for a in activities if a.get("period") == period]

        morning_list = by_period("Sáng")
        lunch_list = by_period("Trưa")
        afternoon_list = by_period("Chiều")
        evening_list = by_period("Tối")
        full_day_list = by_period("Cả ngày")

        # Legacy single-slot (for backward compat) - pick first of each period
        morning = morning_list[0] if morning_list else None
        lunch = lunch_list[0] if lunch_list else None
        afternoon = afternoon_list[0] if afternoon_list else None
        evening = evening_list[0] if evening_list else None

        # Tính day_cost_estimate
        def slot_cost(slot):
            if not slot:
                return 0
            loc = slot.get("location") or {}
            try:
                return float(loc.get("avgCost") or loc.get("avg_cost") or 0)
            except (ValueError, TypeError):
                return 0

        people = int(plan.get("travelers", {}).get("max", 1)) or 1
        all_slots = morning_list + lunch_list + afternoon_list + evening_list + full_day_list
        # Filter out hotel-type activities from attractions cost
        attractions_per_person = sum(slot_cost(s) for s in all_slots if s.get("type") != "hotel")
        attractions_total = attractions_per_person * people

        hotel_total = 0
        if d == 0 and hotel:
            try:
                hotel_per_night = float((hotel or {}).get("avgCost") or (hotel or {}).get("avg_cost") or 0)
            except (ValueError, TypeError):
                hotel_per_night = 0
            nights = max(1, plan.get("durationNights", plan.get("durationDays", 3) - 1))
            rooms = max(1, (people + 1) // 2)
            hotel_total = hotel_per_night * nights * rooms

        day_cost_estimate = int(attractions_total + hotel_total)

        itinerary.append({
            "day": day.get("day"),
            "title": day.get("title", ""),
            # Legacy single-slot fields (backward compat)
            "morning": morning,
            "lunch": lunch,
            "afternoon": afternoon,
            "evening": evening,
            "hotel": hotel,
            # New: all activities grouped by period
            "morning_activities": morning_list,
            "lunch_activities": lunch_list,
            "afternoon_activities": afternoon_list,
            "evening_activities": evening_list,
            "full_day_activities": full_day_list,
            # All activities (raw)
            "activities": activities,
            "day_cost_estimate": day_cost_estimate,
        })

    # Total cost
    total_cost = plan.get("estimatedTotalPerPerson", 0) * (plan.get("travelers", {}).get("max", 1))

    return {
        "success": True,
        "source": "simple_matcher",
        "query": query,
        "primary_plan": {
            "id": plan.get("id"),
            "name": plan.get("title"),
            "city": plan.get("city"),
            "description": plan.get("title", ""),
            "travel_style": plan.get("style"),
            "default_days": plan.get("durationDays"),
            "default_nights": plan.get("durationNights"),
            "budget_min": plan.get("budgetPerPerson", {}).get("min", 0),
            "budget_max": plan.get("budgetPerPerson", {}).get("max", 0),
            "tags": [plan.get("style", "")],
        },
        "secondary_plans": [],
        "adapted_plan": {
            "id": plan.get("id"),
            "name": plan.get("title"),
            "default_days": plan.get("durationDays"),
            "requested_days": plan.get("durationDays"),
            "adapted": False,
            "budget_tier": "mid",
        },
        "itinerary": itinerary,
        "hotel": plan.get("hotel"),
        "total_cost_estimate": int(total_cost),
        "cost_min_estimate": int(plan.get("costBreakdown", {}).get("hotel", 0) * plan.get("durationNights", 0) + plan.get("costBreakdown", {}).get("food", 0)),
        "cost_max_estimate": int(total_cost * 1.2),
        "cost_source": "hardcoded_plan",
        "days": plan.get("durationDays"),
        "costBreakdown": plan.get("costBreakdown", {}),
        "estimatedTotalPerPerson": plan.get("estimatedTotalPerPerson", 0),
        "personality": {
            "dominant_style": plan.get("style"),
        },
    }


def register(app):
    """Register simple match endpoints."""

    @app.post("/api/travel-plans/simple-match")
    async def simple_match(request: Request):
        """
        Match simple Vietnamese prompt to 1 of 24 hard-coded plans.

        Request body:
        {
            "query": "đi đà nẵng 3 ngày 2 đêm, 4.5-6 triệu, 2-3 người"
        }

        Response: full plan response with day-by-day itinerary
        """
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        query = body.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="Missing 'query'")

        # Match
        match = match_simple_plan(query)
        plan_id = match["plan_id"]

        # If no plan matched (rejected by matcher, e.g. invalid city)
        if not plan_id:
            return {
                "success": False,
                "error": "No matching plan",
                "error_detail": "Chỉ hỗ trợ 24 plan cố định cho Đà Nẵng / Hội An / Huế. Vui lòng dùng prompt từ rule.txt hoặc chọn 1 trong 3 thành phố Đà Nẵng / Hội An / Huế.",
                "match": match,
                "query": query,
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

        # Get full plan
        return get_simple_plan_response(plan_id, query)

    @app.get("/api/travel-plans/simple-list")
    async def simple_list(city: Optional[str] = None):
        """List all 24 simple plans."""
        plans = SIMPLE_PROMPTS
        if city:
            city_norm = city.strip().lower().replace("-", "_")
            # SIMPLE_PROMPTS uses "da_nang", "hoian", "hue" (with underscore)
            plans = [p for p in plans if p["city"] == city_norm or p["city"].replace("_", "") == city_norm.replace("_", "")]
        return {
            "success": True,
            "count": len(plans),
            "city": city,
            "plans": plans,
        }

    @app.get("/api/travel-plans/simple-detail/{plan_id}")
    async def simple_detail(plan_id: str):
        """Get full detail of a simple plan."""
        return get_simple_plan_response(plan_id, f"GET {plan_id}")