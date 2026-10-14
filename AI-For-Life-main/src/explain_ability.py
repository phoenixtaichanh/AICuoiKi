"""
Explain Ability Mini - Giải thích tại sao recommend các địa điểm
"""
from typing import Dict, List, Any, Optional


class ExplainAbility:
    """Hệ thống giải thích recommendations"""
    
    @classmethod
    def explain_recommendation(cls, place: Dict, query: str, scores: Dict) -> str:
        """Tạo explanation cho 1 recommendation"""
        reasons = []
        
        # Cosine similarity reason
        nn_cos = scores.get('nn_cos', 0)
        if nn_cos > 0.7:
            reasons.append("Phù hợp cao với yêu cầu của bạn")
        elif nn_cos > 0.5:
            reasons.append("Khá phù hợp với yêu cầu")
        
        # Cross-encoder score
        ce_score = scores.get('ce_score', 0)
        if ce_score > 0.7:
            reasons.append("Được đánh giá cao bởi AI")
        
        # Rating reason
        rating = place.get('rating', 0)
        if rating >= 4.5:
            reasons.append(f"Đánh giá xuất sắc ({rating:.1f}/5)")
        elif rating >= 4.0:
            reasons.append(f"Đánh giá tốt ({rating:.1f}/5)")
        
        # Category match
        category = place.get('category', '')
        query_lower = query.lower()
        if category == 'sightseeing' and any(kw in query_lower for kw in ['thăm quan', 'ngắm cảnh', 'check in']):
            reasons.append("Phù hợp cho tham quan và chụp ảnh")
        elif category == 'food' and any(kw in query_lower for kw in ['ăn', 'ẩm thực', 'hải sản']):
            reasons.append("Phù hợp cho ẩm thực")
        elif category == 'hotel' and any(kw in query_lower for kw in ['nghỉ', 'khách sạn', 'resort']):
            reasons.append("Phù hợp cho nghỉ dưỡng")
        
        # Budget reason
        avg_cost = place.get('avg_cost', 0)
        if avg_cost > 0:
            if avg_cost < 500000:
                reasons.append("Chi phí hợp lý")
            elif avg_cost < 2000000:
                reasons.append("Chi phí trung bình")
            else:
                reasons.append("Chi phí cao nhưng chất lượng tốt")
        
        # Best time reason
        best_time = place.get('best_time', '')
        if best_time:
            reasons.append(f"Thời gian tốt nhất: {best_time}")
        
        # Default explanation nếu không có reason
        if not reasons:
            reasons.append("Được đề xuất dựa trên sở thích của bạn")
        
        return " | ".join(reasons)
    
    @classmethod
    def explain_itinerary_slot(cls, place: Dict, slot: str, day: int) -> str:
        """Giải thích tại sao chọn địa điểm cho slot này"""
        slot_names = {
            'morning': 'Buổi sáng',
            'lunch': 'Bữa trưa',
            'afternoon': 'Buổi chiều',
            'evening': 'Buổi tối',
            'hotel': 'Khách sạn'
        }
        
        slot_name = slot_names.get(slot, slot)
        place_name = place.get('name', 'N/A')
        
        reasons = [f"Chọn cho {slot_name.lower()} ngày {day}"]
        
        # Time-based reasons
        open_time = place.get('open_time', '')
        close_time = place.get('close_time', '')
        
        if slot == 'morning' and open_time:
            if '06:00' in open_time or '07:00' in open_time or '08:00' in open_time:
                reasons.append("Mở cửa sớm phù hợp buổi sáng")
        
        if slot == 'evening' and close_time:
            if '22:00' in close_time or '23:00' in close_time:
                reasons.append("Mở cửa muộn phù hợp buổi tối")
        
        # Distance reason (nếu có)
        # Category reason
        category = place.get('category', '')
        if slot == 'lunch' and category == 'food':
            reasons.append("Nhà hàng phù hợp cho bữa trưa")
        elif slot == 'hotel' and category == 'hotel':
            reasons.append("Khách sạn chất lượng tốt")
        
        return " | ".join(reasons)
    
    @classmethod
    def explain_day(cls, day_plan: Dict, day: int) -> Dict[str, Any]:
        """Giải thích toàn bộ 1 ngày"""
        explanations = {}
        
        for slot in ['morning', 'lunch', 'afternoon', 'evening', 'hotel']:
            place = day_plan.get(slot)
            if place:
                explanations[slot] = {
                    'place_name': place.get('name', 'N/A'),
                    'explanation': cls.explain_itinerary_slot(place, slot, day)
                }
        
        return {
            'day': day,
            'explanations': explanations,
            'summary': f"Ngày {day} được sắp xếp với {len(explanations)} địa điểm phù hợp"
        }
    
    @classmethod
    def explain_full_itinerary(cls, itinerary: Dict, query: str) -> Dict[str, Any]:
        """Giải thích toàn bộ itinerary"""
        days = itinerary.get('itinerary', [])
        
        days_explanations = []
        for day_plan in days:
            day_num = day_plan.get('day', 0)
            day_explanation = cls.explain_day(day_plan, day_num)
            days_explanations.append(day_explanation)
        
        return {
            'query': query,
            'total_days': len(days),
            'total_cost': itinerary.get('total_cost_estimate', 0),
            'per_day_budget': itinerary.get('per_day_budget', 0),
            'days_explanations': days_explanations,
            'overall_explanation': (
                f"Itinerary {len(days)} ngày được tạo dựa trên yêu cầu '{query}'. "
                f"Tổng chi phí ước tính: {itinerary.get('total_cost_estimate', 0):,} VND"
            )
        }

