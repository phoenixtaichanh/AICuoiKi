"""
Query Extractor - Trích xuất thông tin từ query tự nhiên
- Budget (ngân sách)
- Days (số ngày)
- Travel companion (đi với ai)
- City (thành phố)
"""
import re
from typing import Dict, Optional, Tuple


class QueryExtractor:
    """Trích xuất thông tin từ query tự nhiên"""
    
    # Default values
    DEFAULT_BUDGET = 3000000  # 3 triệu VND
    DEFAULT_DAYS = 1
    DEFAULT_TRAVEL_COMPANION = "solo"  # Đi 1 mình
    DEFAULT_CITY = "Da Nang"
    
    # Patterns để extract budget
    BUDGET_PATTERNS = [
        (r'(\d+)\s*(?:triệu|million|tr)', lambda m: int(m.group(1)) * 1000000),
        (r'(\d+)\s*(?:nghìn|k|thousand)', lambda m: int(m.group(1)) * 1000),
        (r'(\d+)\s*(?:vnd|đồng|dong)', lambda m: int(m.group(1))),
        (r'budget[:\s]+(\d+)', lambda m: int(m.group(1))),
        (r'ngân sách[:\s]+(\d+)', lambda m: int(m.group(1))),
        (r'chi phí[:\s]+(\d+)', lambda m: int(m.group(1))),
    ]
    
    # Patterns để extract days
    DAYS_PATTERNS = [
        (r'(\d+)\s*(?:ngày|day|days)', lambda m: int(m.group(1))),
        (r'(\d+)\s*(?:đêm|night|nights)', lambda m: int(m.group(1))),
        (r'(\d+)\s*(?:ngày\s+)?(\d+)\s*(?:đêm)', lambda m: int(m.group(1)) + int(m.group(2)) / 2),
    ]
    
    # Patterns để detect travel companion
    COMPANION_PATTERNS = {
        'solo': [r'1 mình', r'một mình', r'đi một mình', r'solo', r'alone', r'cá nhân'],
        'couple': [r'2 người', r'hai người', r'đôi', r'couple', r'vợ chồng', r'người yêu'],
        'family': [r'gia đình', r'family', r'với con', r'với trẻ em', r'với bé'],
        'friends': [r'bạn bè', r'friends', r'nhóm bạn', r'với bạn'],
        'group': [r'nhóm', r'group', r'đoàn', r'nhiều người', r'(\d+)\s*người'],
    }
    
    # City patterns - hỗ trợ 3 thành phố miền Trung
    CITY_PATTERNS = {
        'da nang': [r'đà nẵng', r'da nang', r'danang', r'\bdn\b'],
        'hoi an': [r'hội an', r'hoi an', r'hoian'],
        'hue': [r'huế(?!\s*nội)', r'\bhue\b'],
    }
    
    @classmethod
    def extract_budget(cls, query: str) -> Optional[int]:
        """Trích xuất budget từ query"""
        query_lower = query.lower()
        
        for pattern, converter in cls.BUDGET_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    return converter(match)
                except:
                    continue
        
        return None
    
    @classmethod
    def extract_budget_with_context(cls, query: str, days: Optional[int] = None) -> Tuple[Optional[int], str]:
        """
        Trích xuất budget và xác định loại budget (per_day hoặc total)
        Returns: (budget_value, budget_type)
        - budget_type: "per_day" nếu là "X triệu 1 ngày", "total" nếu là tổng cho nhiều ngày
        """
        query_lower = query.lower()
        budget = cls.extract_budget(query)
        
        if budget is None:
            return None, "total"  # Default là total
        
        # Kiểm tra các pattern cho "X triệu 1 ngày" hoặc "X triệu/ngày"
        per_day_patterns = [
            r'(\d+)\s*(?:triệu|million|tr)\s*(?:1\s*ngày|/ngày|mỗi\s*ngày|một\s*ngày)',
            r'(\d+)\s*(?:triệu|million|tr)\s*(?:cho\s*)?1\s*ngày',
            r'(\d+)\s*(?:triệu|million|tr)\s*/\s*ngày',
            r'(\d+)\s*(?:triệu|million|tr)\s*mỗi\s*ngày',
        ]
        
        for pattern in per_day_patterns:
            if re.search(pattern, query_lower):
                return budget, "per_day"
        
        # Nếu có số ngày và budget được đề cập cùng lúc, có thể là total
        # Ví dụ: "4 triệu và đi 3 ngày", "4 triệu cho 3 ngày"
        if days and days > 1:
            # Kiểm tra xem budget và days có xuất hiện gần nhau không
            budget_pos = None
            days_pos = None
            
            # Tìm vị trí của budget
            for pattern, _ in cls.BUDGET_PATTERNS:
                match = re.search(pattern, query_lower)
                if match:
                    budget_pos = match.start()
                    break
            
            # Tìm vị trí của days
            for pattern, _ in cls.DAYS_PATTERNS:
                match = re.search(pattern, query_lower)
                if match:
                    days_pos = match.start()
                    break
            
            # Nếu budget và days xuất hiện gần nhau (trong vòng 30 ký tự), có thể là total
            if budget_pos is not None and days_pos is not None:
                distance = abs(budget_pos - days_pos)
                if distance < 30:
                    # Kiểm tra xem có từ khóa "và", "cho", "trong" không
                    context = query_lower[min(budget_pos, days_pos):max(budget_pos, days_pos) + 20]
                    if any(keyword in context for keyword in ['và', 'cho', 'trong', 'với']):
                        return budget, "total"
        
        # Default: nếu không rõ, giả sử là total (an toàn hơn)
        return budget, "total"
    
    @classmethod
    def extract_days(cls, query: str) -> Optional[int]:
        """Trích xuất số ngày từ query"""
        query_lower = query.lower()
        
        for pattern, converter in cls.DAYS_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    days = converter(match)
                    return max(1, min(10, int(days)))  # Limit 1-10 days
                except:
                    continue
        
        return None
    
    @classmethod
    def extract_travel_companion(cls, query: str) -> str:
        """Trích xuất thông tin đi với ai"""
        query_lower = query.lower()
        
        # Check từng loại companion
        for companion_type, patterns in cls.COMPANION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    if companion_type == 'group':
                        # Extract số người nếu có
                        num_match = re.search(r'(\d+)\s*người', query_lower)
                        if num_match:
                            return f"group_{num_match.group(1)}"
                    return companion_type
        
        # Default: solo (đi 1 mình)
        return cls.DEFAULT_TRAVEL_COMPANION
    
    @classmethod
    def extract_city(cls, query: str) -> Optional[str]:
        """Trích xuất thành phố từ query"""
        query_lower = query.lower()
        
        for city_name, patterns in cls.CITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return city_name
        
        return None
    
    @classmethod
    def extract_all(cls, query: str) -> Dict:
        """Trích xuất tất cả thông tin từ query"""
        days = cls.extract_days(query)
        budget, budget_type = cls.extract_budget_with_context(query, days)
        companion = cls.extract_travel_companion(query)
        city = cls.extract_city(query)
        
        # Tính toán budget total và per_day dựa trên budget_type
        final_days = days if days else cls.DEFAULT_DAYS
        if budget:
            if budget_type == "per_day":
                # Budget là mỗi ngày, tính total
                budget_total = budget * final_days
                budget_per_day = budget
            else:
                # Budget là total, tính per_day
                budget_total = budget
                budget_per_day = budget // final_days if final_days > 0 else budget
        else:
            budget_total = cls.DEFAULT_BUDGET
            budget_per_day = cls.DEFAULT_BUDGET // final_days if final_days > 0 else cls.DEFAULT_BUDGET
        
        return {
            'budget': budget_total,  # Total budget
            'budget_per_day': budget_per_day,  # Budget mỗi ngày
            'budget_type': budget_type,  # "per_day" hoặc "total"
            'days': final_days,
            'travel_companion': companion,
            'city': city if city else cls.DEFAULT_CITY,
            'extracted': {
                'budget_found': budget is not None,
                'days_found': days is not None,
                'companion_found': companion != cls.DEFAULT_TRAVEL_COMPANION,
                'city_found': city is not None,
                'budget_type': budget_type,
            }
        }

