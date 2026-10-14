"""
Plan index loader - load 3 city plan files into in-memory structure.
Also exposes helpers to look up plans by id / city.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# Folder chứa plan files
PLANS_DIR = Path(__file__).parent

# Canonical city keys (must match CITY_MAP in recommender.py and CITY_PATTERNS in query_extractor.py)
CITY_KEYS = {
    "da nang": "danang",
    "danang": "danang",
    "đà nẵng": "danang",
    "dn": "danang",
    "hoi an": "hoian",
    "hoian": "hoian",
    "hội an": "hoian",
    "hue": "hue",
    "huế": "hue",
}

# City -> filename (without extension)
CITY_FILES = {
    "danang": "danang.json",
    "hoian": "hoian.json",
    "hue": "hue.json",
}


def _normalize_city(city: str) -> Optional[str]:
    """Normalize city input to canonical key (danang/hoian/hue)."""
    if not city:
        return None
    key = city.strip().lower()
    return CITY_KEYS.get(key, key) if key in CITY_KEYS else None


def _validate_plan(plan: Dict[str, Any], city: str) -> List[str]:
    """Light validation. Returns list of error strings (empty = ok)."""
    errors: List[str] = []
    required = [
        "id", "plan_type", "name", "default_days", "default_nights",
        "budget_min", "budget_max", "travel_style", "intensity",
        "preferred_categories", "preferred_tags", "preferred_price_levels"
    ]
    for r in required:
        if r not in plan:
            errors.append(f"plan missing required field: {r}")
    if plan.get("plan_type") not in ("core", "adaptive"):
        errors.append(f"plan_type must be 'core' or 'adaptive'")
    if not isinstance(plan.get("intent_keywords", []), list):
        errors.append("intent_keywords must be list")
    if not isinstance(plan.get("preference_keywords", []), list):
        errors.append("preference_keywords must be list")
    return errors


def load_city_plans(city: str) -> List[Dict[str, Any]]:
    """Load plans for a given city (canonical key or alias)."""
    city_key = _normalize_city(city)
    if not city_key or city_key not in CITY_FILES:
        return []
    filepath = PLANS_DIR / CITY_FILES[city_key]
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Error loading {filepath}: {e}")
        return []
    plans = data.get("plans", [])
    # validate each plan, and inject city into each plan dict
    valid: List[Dict[str, Any]] = []
    for p in plans:
        errs = _validate_plan(p, city_key)
        if errs:
            print(f"[WARN] Plan {p.get('id', '?')} in {city_key} has errors: {errs}")
            continue
        # Make sure each plan has 'city' key for downstream filtering
        if "city" not in p:
            p["city"] = city_key
        valid.append(p)
    return valid


def load_all_plans() -> Dict[str, List[Dict[str, Any]]]:
    """Load all plans grouped by city. Returns {city_key: [plan, ...]}"""
    result: Dict[str, List[Dict[str, Any]]] = {}
    for city_key, filename in CITY_FILES.items():
        filepath = PLANS_DIR / filename
        if not filepath.exists():
            print(f"[WARN] Plan file missing: {filepath}")
            result[city_key] = []
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            plans = data.get("plans", [])
            valid: List[Dict[str, Any]] = []
            for p in plans:
                errs = _validate_plan(p, city_key)
                if errs:
                    print(f"[WARN] Plan {p.get('id', '?')} in {city_key} has errors: {errs}")
                    continue
                # Ensure each plan has 'city' key for downstream filtering
                if "city" not in p:
                    p["city"] = city_key
                valid.append(p)
            result[city_key] = valid
            print(f"[OK] Loaded {len(valid)} plans for {city_key}")
        except Exception as e:
            print(f"[ERROR] Error loading {filename}: {e}")
            result[city_key] = []
    return result


def get_plan_by_id(plan_id: str, plans_index: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> Optional[Dict[str, Any]]:
    """Look up a plan by id across all cities."""
    if plans_index is None:
        plans_index = load_all_plans()
    for city_plans in plans_index.values():
        for p in city_plans:
            if p.get("id") == plan_id:
                return p
    return None


def list_all_plans(plans_index: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> List[Dict[str, Any]]:
    """Return flat list of all plans (with city attached)."""
    if plans_index is None:
        plans_index = load_all_plans()
    flat: List[Dict[str, Any]] = []
    for city_key, plans in plans_index.items():
        for p in plans:
            p_copy = dict(p)
            p_copy["city"] = city_key
            flat.append(p_copy)
    return flat
