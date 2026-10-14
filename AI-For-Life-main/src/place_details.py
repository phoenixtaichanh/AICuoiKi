"""
Module để quản lý và truy vấn thông tin chi tiết về địa danh
"""

import json
import os
from typing import Dict, Any, Optional
import pandas as pd
from rapidfuzz import process, fuzz

class PlaceDetailsManager:
    """Quản lý thông tin chi tiết về địa danh"""
    
    def __init__(self, details_file: str = "data/placesdetail.csv"):
        self.details_file = details_file
        self.details = {}
        self._load_details()
    
    def _load_details(self):
        """Load thông tin chi tiết từ file CSV"""
        # Thử load từ CSV trước
        if os.path.exists(self.details_file):
            try:
                df = pd.read_csv(self.details_file, encoding='utf-8')
                df = df.fillna('')
                
                # Convert DataFrame thành dict keyed by place_name
                for _, row in df.iterrows():
                    place_name = str(row.get('place_name', '')).strip()
                    if place_name:
                        self.details[place_name] = {
                            'place_id': str(row.get('place_id', '')),
                            'place_name': place_name,
                            'history': str(row.get('history', '')),
                            'highlights': str(row.get('highlights', '')),
                            'cultural_info': str(row.get('cultural_info', '')),
                            'events': str(row.get('events', '')),
                            'architecture': str(row.get('architecture', '')),
                            'significance': str(row.get('significance', '')),
                            'visitor_tips': str(row.get('visitor_tips', '')),
                            'nearby_attractions': str(row.get('nearby_attractions', '')),
                            'detailed_description': str(row.get('detailed_description', '')),
                            'images': str(row.get('images', '')),
                            'videos': str(row.get('videos', '')),
                            'source_urls': str(row.get('source_urls', '')),
                            'last_updated': str(row.get('last_updated', ''))
                        }
                
                print(f"[OK] Loaded {len(self.details)} place details from {self.details_file}")
            except Exception as e:
                print(f"[WARN] Error loading place details from CSV: {e}")
                self.details = {}
        else:
            # Fallback: thử load từ JSON nếu có
            json_file = "data/places_details.json"
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        self.details = json.load(f)
                    print(f"[OK] Loaded {len(self.details)} place details from {json_file}")
                except Exception as e:
                    print(f"[WARN] Error loading place details from JSON: {e}")
                    self.details = {}
            else:
                print(f"[WARN] Place details file not found: {self.details_file} or {json_file}")
                self.details = {}
    
    def get_details(self, place_name: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chi tiết về một địa danh"""
        # Tìm exact match trước
        if place_name in self.details:
            return self.details[place_name]
        
        # Fuzzy match
        place_names = list(self.details.keys())
        if place_names:
            best_match = process.extractOne(
                place_name,
                place_names,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=70
            )
            
            if best_match:
                matched_name, score, _ = best_match
                return self.details[matched_name]
        
        return None
    
    def get_history(self, place_name: str) -> str:
        """Lấy lịch sử hình thành của địa danh"""
        details = self.get_details(place_name)
        if details:
            return details.get('history', '')
        return ''
    
    def get_highlights(self, place_name: str) -> str:
        """Lấy điểm nổi bật của địa danh"""
        details = self.get_details(place_name)
        if details:
            return details.get('highlights', '')
        return ''
    
    def get_features(self, place_name: str) -> str:
        """Lấy đặc điểm nổi bật của địa danh"""
        details = self.get_details(place_name)
        if details:
            # Thử nhiều key names
            return (details.get('features', '') or 
                   details.get('architecture', '') or
                   details.get('highlights', ''))
        return ''
    
    def get_cultural_significance(self, place_name: str) -> str:
        """Lấy ý nghĩa văn hóa của địa danh"""
        details = self.get_details(place_name)
        if details:
            # Thử nhiều key names
            return (details.get('cultural_significance', '') or
                   details.get('cultural_info', '') or
                   details.get('significance', ''))
        return ''
    
    def get_tips(self, place_name: str) -> str:
        """Lấy mẹo du lịch cho địa danh"""
        details = self.get_details(place_name)
        if details:
            return details.get('tips', '')
        return ''
    
    def get_nearby_attractions(self, place_name: str) -> str:
        """Lấy địa điểm gần đó"""
        details = self.get_details(place_name)
        if details:
            return details.get('nearby_attractions', '')
        return ''
    
    def get_full_info(self, place_name: str) -> Dict[str, Any]:
        """Lấy toàn bộ thông tin chi tiết về địa danh"""
        details = self.get_details(place_name)
        if not details:
            return {}
        
        return {
            'place_name': details.get('place_name', place_name),
            'place_id': details.get('place_id', ''),
            'history': details.get('history', ''),
            'highlights': details.get('highlights', ''),
            'features': details.get('features', '') or details.get('architecture', ''),
            'cultural_significance': (details.get('cultural_significance', '') or
                                    details.get('cultural_info', '') or
                                    details.get('significance', '')),
            'tips': details.get('tips', '') or details.get('visitor_tips', ''),
            'nearby_attractions': details.get('nearby_attractions', ''),
            'full_description': (details.get('full_description', '') or
                               details.get('detailed_description', '')),
            'events': details.get('events', ''),
            'images': details.get('images', ''),
            'videos': details.get('videos', ''),
            'source_urls': details.get('source_urls', ''),
            'last_updated': details.get('last_updated', '')
        }
    
    def search_by_keyword(self, keyword: str) -> list:
        """Tìm kiếm địa danh theo từ khóa trong thông tin chi tiết"""
        results = []
        keyword_lower = keyword.lower()
        
        for place_name, details in self.details.items():
            # Tìm trong các trường
            search_text = ' '.join([
                place_name,
                details.get('history', ''),
                details.get('highlights', ''),
                details.get('features', ''),
                details.get('full_description', '')
            ]).lower()
            
            if keyword_lower in search_text:
                results.append({
                    'place_name': place_name,
                    'match_score': search_text.count(keyword_lower),
                    'details': details
                })
        
        # Sắp xếp theo score
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:10]  # Top 10

