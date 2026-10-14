"""
Plan Guard - Validate và kiểm tra tính hợp lý của itinerary
"""
from typing import Dict, List, Any, Optional
import numpy as np


class PlanGuard:
    """Hệ thống validate itinerary"""
    
    # Thresholds
    MAX_DISTANCE_KM = 50.0  # Khoảng cách tối đa giữa các điểm trong 1 ngày
    MAX_BUDGET_OVERRUN = 0.15  # Cho phép vượt budget tối đa 15%
    MIN_TIME_BETWEEN_PLACES = 30  # Thời gian tối thiểu giữa 2 địa điểm (phút)
    
    @classmethod
    def haversine(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Tính khoảng cách Haversine (km)"""
        import math
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dl = math.radians(lon1 - lon2)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
        return 2 * R * math.asin(math.sqrt(a))
    
    @classmethod
    def validate_budget(cls, day_plan: Dict, per_day_budget: float) -> Dict[str, Any]:
        """Validate budget cho 1 ngày"""
        day_cost = day_plan.get('day_cost_estimate', 0)
        over_budget = day_cost > per_day_budget * (1 + cls.MAX_BUDGET_OVERRUN)
        over_percentage = ((day_cost - per_day_budget) / per_day_budget * 100) if per_day_budget > 0 else 0
        
        return {
            'valid': not over_budget,
            'day_cost': day_cost,
            'budget_limit': per_day_budget,
            'over_budget': over_budget,
            'over_percentage': over_percentage,
            'warnings': [] if not over_budget else [
                f"Vượt ngân sách {over_percentage:.1f}%"
            ]
        }
    
    @classmethod
    def validate_distance(cls, places: List[Dict]) -> Dict[str, Any]:
        """Validate khoảng cách giữa các địa điểm"""
        if len(places) < 2:
            return {'valid': True, 'max_distance': 0, 'warnings': []}
        
        distances = []
        warnings = []
        
        for i in range(len(places) - 1):
            p1 = places[i]
            p2 = places[i + 1]
            
            lat1 = p1.get('lat')
            lon1 = p1.get('lon')
            lat2 = p2.get('lat')
            lon2 = p2.get('lon')
            
            if lat1 and lon1 and lat2 and lon2:
                try:
                    dist = cls.haversine(float(lat1), float(lon1), float(lat2), float(lon2))
                    distances.append(dist)
                    
                    if dist > cls.MAX_DISTANCE_KM:
                        warnings.append(
                            f"Khoảng cách giữa {p1.get('name', 'N/A')} và {p2.get('name', 'N/A')} "
                            f"quá xa ({dist:.1f}km)"
                        )
                except:
                    pass
        
        max_dist = max(distances) if distances else 0
        
        return {
            'valid': max_dist <= cls.MAX_DISTANCE_KM,
            'max_distance': max_dist,
            'distances': distances,
            'warnings': warnings
        }
    
    @classmethod
    def validate_time_slots(cls, day_plan: Dict) -> Dict[str, Any]:
        """Validate thời gian các slot trong ngày"""
        slots = ['morning', 'lunch', 'afternoon', 'evening']
        warnings = []
        
        for slot in slots:
            place = day_plan.get(slot)
            if place:
                open_time = place.get('open_time', '')
                close_time = place.get('close_time', '')
                
                if not open_time or not close_time:
                    warnings.append(f"{slot.capitalize()}: Thiếu thông tin giờ mở cửa")
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings
        }
    
    @classmethod
    def validate_day(cls, day_plan: Dict, per_day_budget: float) -> Dict[str, Any]:
        """Validate toàn bộ 1 ngày"""
        # Collect places
        places = []
        for slot in ['morning', 'lunch', 'afternoon', 'evening', 'hotel']:
            place = day_plan.get(slot)
            if place:
                places.append(place)
        
        # Validate từng aspect
        budget_check = cls.validate_budget(day_plan, per_day_budget)
        distance_check = cls.validate_distance(places)
        time_check = cls.validate_time_slots(day_plan)
        
        all_warnings = budget_check['warnings'] + distance_check['warnings'] + time_check['warnings']
        
        return {
            'day': day_plan.get('day', 0),
            'valid': budget_check['valid'] and distance_check['valid'] and time_check['valid'],
            'budget_check': budget_check,
            'distance_check': distance_check,
            'time_check': time_check,
            'warnings': all_warnings,
            'score': 1.0 if len(all_warnings) == 0 else max(0.0, 1.0 - len(all_warnings) * 0.2)
        }
    
    @classmethod
    def validate_itinerary(cls, itinerary: Dict) -> Dict[str, Any]:
        """Validate toàn bộ itinerary"""
        days = itinerary.get('itinerary', [])
        per_day_budget = itinerary.get('per_day_budget', 0)
        
        if not days:
            return {
                'valid': False,
                'error': 'Itinerary rỗng',
                'days_validation': []
            }
        
        days_validation = []
        all_warnings = []
        
        for day_plan in days:
            day_validation = cls.validate_day(day_plan, per_day_budget)
            days_validation.append(day_validation)
            all_warnings.extend(day_validation['warnings'])
        
        overall_valid = all(d['valid'] for d in days_validation)
        overall_score = np.mean([d['score'] for d in days_validation]) if days_validation else 0.0
        
        return {
            'valid': overall_valid,
            'overall_score': overall_score,
            'total_warnings': len(all_warnings),
            'warnings': all_warnings,
            'days_validation': days_validation,
            'summary': {
                'total_days': len(days),
                'valid_days': sum(1 for d in days_validation if d['valid']),
                'total_cost': itinerary.get('total_cost_estimate', 0),
                'budget_total': itinerary.get('per_day_budget', 0) * len(days)
            }
        }

