"""Extract relevant places/restaurants from dataset for plan building."""
import json
import pandas as pd
from pathlib import Path

csv = Path("D:/AI-For-Life-main/AI-For-Life-main/data/places_clean.csv")
df = pd.read_csv(csv)
df["city_norm"] = df["city"].astype(str).str.strip()

# Group by city + category, sort by rating
for city_key, city_vn in [("Da Nang", "Đà Nẵng"), ("Hoi An", "Hội An"), ("Hue", "Huế")]:
    print(f"\n========== {city_vn} ({city_key}) ==========")
    sub = df[df["city_norm"] == city_key].copy()
    print(f"Total: {len(sub)}")
    for cat in ["food", "hotel", "sightseeing", "cultural", "museum", "beach", "entertainment", "shopping"]:
        c = sub[sub["category"] == cat].sort_values(["rating", "review_count"], ascending=False)
        if not c.empty:
            print(f"\n--- {cat} ({len(c)}) ---")
            for _, r in c.head(25).iterrows():
                tags = (str(r.get("tags", ""))[:50] if pd.notna(r.get("tags")) else "")
                print(f"  id={int(r['id']):>4} {r['name'][:40]:<40} *{r['rating']:.1f} ({int(r['review_count'])}) {int(r['avg_cost']):>9,}₫ {tags}")