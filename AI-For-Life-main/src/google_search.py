"""
Google Search API Integration - Tìm kiếm thông tin bổ sung từ Google
"""
import os
import requests
from typing import Dict, List, Optional, Any
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GoogleSearchAPI:
    """Wrapper cho Google Custom Search API"""
    
    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        """
        Khởi tạo Google Search API
        
        Args:
            api_key: Google API Key (hoặc lấy từ env GOOGLE_SEARCH_API_KEY)
            search_engine_id: Custom Search Engine ID (hoặc lấy từ env GOOGLE_SEARCH_ENGINE_ID)
        """
        self.api_key = api_key or os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.api_key or not self.search_engine_id:
            logger.warning("[WARN] Google Search API chưa được cấu hình. Set GOOGLE_SEARCH_API_KEY và GOOGLE_SEARCH_ENGINE_ID trong .env")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("[OK] Google Search API đã được khởi tạo")
    
    def search(self, query: str, num_results: int = 5, language: str = "vi") -> List[Dict[str, Any]]:
        """
        Tìm kiếm trên Google
        
        Args:
            query: Câu truy vấn
            num_results: Số kết quả (max 10)
            language: Ngôn ngữ (vi, en, etc.)
            
        Returns:
            List các kết quả tìm kiếm
        """
        if not self.enabled:
            logger.warning("Google Search API chưa được cấu hình")
            return []
        
        try:
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": min(num_results, 10),  # Google limit: max 10
                "lr": f"lang_{language}",
                "safe": "active"
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            # Xử lý lỗi 429 (Too Many Requests)
            if response.status_code == 429:
                logger.warning(f"[WARN] Google Search API: Quota exceeded (429). Vui lòng đợi hoặc nâng cấp quota.")
                return []
            
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if "items" in data:
                for item in data["items"]:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "display_link": item.get("displayLink", "")
                    })
            
            logger.info(f"[OK] Tìm thấy {len(results)} kết quả từ Google Search cho query: {query}")
            return results
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"[WARN] Google Search API: Quota exceeded (429). Vui lòng đợi hoặc nâng cấp quota.")
            else:
                logger.error(f"[ERROR] Lỗi HTTP khi gọi Google Search API: {e}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR] Lỗi khi gọi Google Search API: {e}")
            return []
        except Exception as e:
            logger.error(f"[ERROR] Lỗi xử lý kết quả Google Search: {e}")
            return []
    
    def search_place_info(self, place_name: str, city: str = "Da Nang") -> Dict[str, Any]:
        """
        Tìm kiếm thông tin về địa điểm cụ thể
        
        Args:
            place_name: Tên địa điểm
            city: Thành phố
            
        Returns:
            Dict chứa thông tin tìm được
        """
        query = f"{place_name} {city} du lịch"
        results = self.search(query, num_results=3)
        
        if not results:
            return {
                "success": False,
                "message": "Không tìm thấy thông tin từ Google Search"
            }
        
        # Tổng hợp thông tin từ các kết quả
        snippets = [r["snippet"] for r in results]
        links = [r["link"] for r in results]
        
        return {
            "success": True,
            "place_name": place_name,
            "city": city,
            "snippets": snippets,
            "links": links,
            "top_result": {
                "title": results[0]["title"],
                "snippet": results[0]["snippet"],
                "link": results[0]["link"]
            }
        }
    
    def search_travel_tips(self, query: str, city: str = "Da Nang") -> List[Dict[str, Any]]:
        """
        Tìm kiếm tips du lịch
        
        Args:
            query: Câu truy vấn (ví dụ: "ăn gì", "đi đâu", "kinh nghiệm")
            city: Thành phố
            
        Returns:
            List các tips
        """
        full_query = f"{query} {city} du lịch"
        results = self.search(full_query, num_results=5)
        
        tips = []
        for result in results:
            tips.append({
                "title": result["title"],
                "content": result["snippet"],
                "source": result["display_link"],
                "link": result["link"]
            })
        
        return tips


# Global instance
google_search_instance = None

def init_google_search(api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
    """Khởi tạo Google Search instance"""
    global google_search_instance
    try:
        google_search_instance = GoogleSearchAPI(api_key, search_engine_id)
        return google_search_instance
    except Exception as e:
        logger.error(f"[ERROR] Lỗi khởi tạo Google Search: {e}")
        return None

