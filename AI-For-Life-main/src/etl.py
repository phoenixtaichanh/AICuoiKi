import pandas as pd
import numpy as np
import re
from typing import Set

def strip_accents(s: str) -> str:
    """Remove accents từ string"""
    if not isinstance(s, str):
        return ""
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[đ]', 'd', s)
    s = re.sub(r'[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ]', 'A', s)
    s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
    s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
    s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
    s = re.sub(r'[ÙÚỤỦŨƯỪỨỰỬỮ]', 'U', s)
    s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
    s = re.sub(r'[Đ]', 'D', s)
    return s

def parse_closed_days(closed_str: str) -> Set[int]:
    """
    Parse closed_days string thành set of weekday numbers (0=Mon, 6=Sun)
    """
    if not isinstance(closed_str, str):
        return set()
    
    closed_str = closed_str.lower()
    days_map = {
        'mon': 0, 'monday': 0, 'thứ 2': 0, 'thứ hai': 0,
        'tue': 1, 'tuesday': 1, 'thứ 3': 1, 'thứ ba': 1, 
        'wed': 2, 'wednesday': 2, 'thứ 4': 2, 'thứ tư': 2,
        'thu': 3, 'thursday': 3, 'thứ 5': 3, 'thứ năm': 3,
        'fri': 4, 'friday': 4, 'thứ 6': 4, 'thứ sáu': 4,
        'sat': 5, 'saturday': 5, 'thứ 7': 5, 'thứ bảy': 5,
        'sun': 6, 'sunday': 6, 'chủ nhật': 6, 'cn': 6
    }
    
    result = set()
    for key, value in days_map.items():
        if key in closed_str:
            result.add(value)
    
    return result

def load_dataset(csv_path: str = "data/itinerary_dataset.csv") -> pd.DataFrame:
    """
    Load và clean dataset
    """
    try:
        # ƯU TIÊN CSV ĐÃ CLEAN
        df = pd.read_csv("data/itinerary_dataset.clean.csv")
        print("[OK] Loaded cleaned CSV dataset")
    except:
        try:
            df = pd.read_csv("data/places.csv")
            print("[OK] Loaded places CSV dataset")
        except:
            try:
                df = pd.read_csv(csv_path)
                print("[OK] Loaded CSV dataset")
            except FileNotFoundError:
                print("[ERROR] Dataset file not found")
                raise
    
    # Clean data
    df = df.fillna('')
    
    # Ensure numeric columns
    numeric_cols = ['avg_cost', 'duration_min', 'rating', 'review_count', 'popularity']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df