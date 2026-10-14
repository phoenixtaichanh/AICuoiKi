# Travel Plans Data

This folder contains predefined travel plans for the 3 supported cities:
- **Đà Nẵng** (`danang.json`) — 5 core + 3 adaptive = 8 plans
- **Hội An** (`hoian.json`) — 5 core + 3 adaptive = 8 plans
- **Huế** (`hue.json`) — 5 core + 3 adaptive = 8 plans

**Total: 24 plans.**

## Plan Structure

Each plan has:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique code: `DN01` (core) or `DNA01` (adaptive), `HOI01` / `HOA01`, `HUE01` / `HUEA01` |
| `plan_type` | "core" / "adaptive" | Core = always matchable; Adaptive = match by personality |
| `name` | string | Display name (Vietnamese) |
| `description` | string | Short description (Vietnamese) |
| `default_days` | int | Default trip duration (days) |
| `default_nights` | int | Default nights |
| `budget_min` / `budget_max` | int | VND per person (total) |
| `travel_style` | string | One of: balanced, relax, adventure, foodie, family, romantic, quiet, history, budget, photography |
| `intensity` | "slow" / "balanced" / "active" | Trip pace |
| `suitable_for` | list | User profiles this plan fits |
| `intent_keywords` | list | Phrases that **strongly** indicate this plan |
| `preference_keywords` | list | Soft signal phrases |
| `preferred_categories` | list | Categories from dataset (food, sightseeing, etc.) |
| `preferred_tags` | list | Tag prefixes to boost |
| `excluded_tags` | list | Tag prefixes to penalize / exclude |
| `preferred_price_levels` | list | "$", "$$", "$$$" |
| `budget_weight` | float | Multiplier on budget score (1.0 = neutral) |
| `rating_weight` | float | Multiplier on rating score |
| `popularity_weight` | float | Multiplier on popularity score |
| `distance_weight` | float | Multiplier on distance score |
| `preference_weight` | float | Multiplier on preference/tag match |
| `rules` | object | Hard constraints: min_rating, max_places_per_day, etc. |
| `itinerary_rules` | list | Free-form rules for LLM / builder |
| `tags` | list | Plan-level tags (display) |

## Design Principles

1. **Dataset is source of truth** — plans contain NO place names. They contain *preferences* and *rules*. Place selection always reads `data/places_clean.csv`.

2. **Plans adapt** — `default_days` is the **base**, not the limit. If user says "5 days", we expand; "2 days" → we compress. See `src/plans/plan_engine.py::adapt_plan_to_days()`.

3. **Budget tiers** — `budget_min`/`budget_max` define the **default range**. The matcher re-weights scores when user is in low / mid / high tier. See `BudgetTier` enum.

4. **No LLM hallucination** — the LLM is only used to *narrate* the final itinerary. The matched plan + ranked places are pre-computed by deterministic code.

## How to add a new plan

1. Add the plan object to the appropriate city's JSON file
2. Run the server — plans are loaded at import time
3. Add a test in `tests/test_plans.py`

## How to add a new city

1. Create `data/yourcity.csv` with the same schema as `places_clean.csv`
2. Create `src/plans/yourcity.json` with 5+3 plans
3. Update `src/plans/index.py::load_all_plans()` to include the new file
4. Update `src/plans/plan_engine.py::CITY_KEYWORDS` and `src/query_extractor.py::CITY_PATTERNS`
