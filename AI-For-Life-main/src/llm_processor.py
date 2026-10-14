"""
LLM Integration - Xử lý query tự nhiên với LLM
Hỗ trợ OpenAI và có thể mở rộng cho các LLM khác
"""
import os
from typing import Dict, List, Optional, Any
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class LLMProcessor:
    """Xử lý query tự nhiên với LLM"""
    
    def __init__(self, provider: str = "openai", model: str = "gpt-4o-mini"):
        """
        Khởi tạo LLM Processor
        
        Args:
            provider: LLM provider ("openai", "gemini", etc.)
            model: Model name
        """
        self.provider = provider
        self.model = model
        self.client = None
        self.enabled = False
        
        if provider == "openai":
            self._init_openai()
        elif provider == "gemini":
            self._init_gemini()
        else:
            logger.warning(f"[WARN] LLM provider '{provider}' chưa được hỗ trợ")
    
    def _init_openai(self):
        """Khởi tạo OpenAI client"""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                logger.warning("[WARN] OPENAI_API_KEY chưa được set trong .env")
                return
            
            self.client = OpenAI(api_key=api_key)
            self.enabled = True
            logger.info(f"[OK] LLM Processor (OpenAI {self.model}) đã được khởi tạo")
        except ImportError:
            logger.error("[ERROR] Cần cài đặt: pip install openai")
        except Exception as e:
            logger.error(f"[ERROR] Lỗi khởi tạo OpenAI: {e}")
    
    def _init_gemini(self):
        """Khởi tạo Gemini client"""
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            
            if not api_key:
                logger.warning("[WARN] GEMINI_API_KEY chưa được set trong .env")
                return
            
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(self.model)
            self.enabled = True
            logger.info(f"[OK] LLM Processor (Gemini {self.model}) đã được khởi tạo")
        except ImportError:
            logger.error("[ERROR] Cần cài đặt: pip install google-generativeai")
        except Exception as e:
            logger.error(f"[ERROR] Lỗi khởi tạo Gemini: {e}")
    
    def process_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Xử lý query tự nhiên với LLM
        
        Args:
            query: Câu truy vấn từ user
            context: Context bổ sung (city, preferences, etc.)
            
        Returns:
            Dict chứa thông tin đã được xử lý
        """
        if not self.enabled:
            logger.warning("LLM Processor chưa được khởi tạo")
            return {
                "success": False,
                "error": "LLM chưa được cấu hình"
            }
        
        try:
            if self.provider == "openai":
                return self._process_openai(query, context)
            elif self.provider == "gemini":
                return self._process_gemini(query, context)
        except Exception as e:
            logger.error(f"[ERROR] Lỗi xử lý query với LLM: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_openai(self, query: str, context: Optional[Dict]) -> Dict[str, Any]:
        """Xử lý với OpenAI"""
        prompt = self._build_prompt(query, context)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là trợ lý du lịch thông minh. Phân tích câu hỏi và trả về JSON với các thông tin: budget, days, city, travel_companion, preferences."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        result["success"] = True
        result["llm_provider"] = "openai"
        
        return result
    
    def _process_gemini(self, query: str, context: Optional[Dict]) -> Dict[str, Any]:
        """Xử lý với Gemini"""
        prompt = self._build_prompt(query, context)
        
        response = self.client.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 500,
            }
        )
        
        import json
        try:
            # Gemini có thể trả về text hoặc JSON
            result_text = response.text
            # Tìm JSON trong response
            if "{" in result_text:
                start = result_text.find("{")
                end = result_text.rfind("}") + 1
                result = json.loads(result_text[start:end])
            else:
                result = {"raw_response": result_text}
            
            result["success"] = True
            result["llm_provider"] = "gemini"
            
            return result
        except Exception as e:
            logger.error(f"Lỗi parse Gemini response: {e}")
            return {
                "success": False,
                "error": f"Lỗi parse response: {e}",
                "raw_response": response.text
            }
    
    def _build_prompt(self, query: str, context: Optional[Dict]) -> str:
        """Xây dựng prompt cho LLM"""
        prompt = f"""
Phân tích câu hỏi du lịch sau và trả về JSON:

Câu hỏi: "{query}"

Context: {context or "Không có"}

Trả về JSON với format:
{{
    "budget": số tiền (VND) hoặc null nếu không có,
    "days": số ngày hoặc null nếu không có,
    "city": tên thành phố hoặc null nếu không có,
    "travel_companion": "solo" | "couple" | "family" | "friends" | "group" hoặc null,
    "preferences": ["biển", "ẩm thực", "check-in", ...],
    "intent": "itinerary" | "qa" | "recommendation"
}}

Chỉ trả về JSON, không có text khác.
"""
        return prompt
    
    def enhance_query(self, query: str, place_data: Optional[Dict] = None) -> str:
        """
        Cải thiện query với LLM
        
        Args:
            query: Query gốc
            place_data: Dữ liệu địa điểm (nếu có)
            
        Returns:
            Query đã được cải thiện
        """
        if not self.enabled:
            return query
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Bạn là trợ lý du lịch. Cải thiện câu hỏi để rõ ràng và dễ hiểu hơn, nhưng giữ nguyên ý nghĩa."
                        },
                        {
                            "role": "user",
                            "content": f"Cải thiện câu hỏi này: '{query}'"
                        }
                    ],
                    temperature=0.3,
                    max_tokens=200
                )
                return response.choices[0].message.content.strip()
            else:
                return query
        except Exception as e:
            logger.error(f"Lỗi enhance query: {e}")
            return query


# Global instance
llm_processor_instance = None

def init_llm_processor(provider: str = "openai", model: str = "gpt-4o-mini"):
    """Khởi tạo LLM Processor instance"""
    global llm_processor_instance
    try:
        llm_processor_instance = LLMProcessor(provider, model)
        return llm_processor_instance
    except Exception as e:
        logger.error(f"[ERROR] Lỗi khởi tạo LLM Processor: {e}")
        return None

