"""
Plan model and PlanScore breakdown dataclasses.
Mirrors the spec in section 2 of the requirements.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PlanScoreBreakdown:
    city_match: float = 0.0
    intent_match: float = 0.0
    preference_match: float = 0.0
    budget_match: float = 0.0
    days_match: float = 0.0
    traveler_type_match: float = 0.0
    negative_preference_penalty: float = 0.0


@dataclass
class PlanMatchResult:
    plan: Dict[str, Any]
    score: float
    breakdown: PlanScoreBreakdown
    matched_keywords: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    role: str = "primary"  # "primary" or "secondary"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan.get("id"),
            "plan_name": self.plan.get("name"),
            "plan_type": self.plan.get("plan_type"),
            "city": self.plan.get("city"),
            "role": self.role,
            "score": round(self.score, 2),
            "matched_keywords": self.matched_keywords,
            "reasons": self.reasons,
            "breakdown": {
                k: round(v, 2)
                for k, v in self.breakdown.__dict__.items()
            },
        }


@dataclass
class UserIntent:
    """Structured user intent extracted from query."""
    city: Optional[str] = None
    days: Optional[int] = None
    nights: Optional[int] = None
    budget_total: Optional[int] = None  # VND, total
    budget_per_day: Optional[int] = None
    budget_type: str = "total"  # "total" or "per_day"
    travel_companion: str = "solo"  # solo / couple / family / friends / group
    people_count: int = 1

    # Personality / preferences
    positive_preferences: List[str] = field(default_factory=list)
    negative_preferences: List[str] = field(default_factory=list)

    # Strong signals from personality detector
    dominant_style: Optional[str] = None  # "quiet", "romantic", "foodie", "budget", "history", "family", "adventure", "relax", "balanced"
    is_student: bool = False
    is_first_time: bool = False
    is_couple: bool = False
    is_solo: bool = False
    is_family: bool = False
    has_children: bool = False

    # Raw query
    raw_query: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "city": self.city,
            "days": self.days,
            "nights": self.nights,
            "budget_total": self.budget_total,
            "budget_per_day": self.budget_per_day,
            "budget_type": self.budget_type,
            "travel_companion": self.travel_companion,
            "people_count": self.people_count,
            "positive_preferences": self.positive_preferences,
            "negative_preferences": self.negative_preferences,
            "dominant_style": self.dominant_style,
            "is_student": self.is_student,
            "is_first_time": self.is_first_time,
            "is_couple": self.is_couple,
            "is_solo": self.is_solo,
            "is_family": self.is_family,
            "has_children": self.has_children,
            "raw_query": self.raw_query,
        }
