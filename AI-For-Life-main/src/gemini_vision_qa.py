import os
import json
import pandas as pd
from rapidfuzz import process, fuzz
import google.generativeai as genai
from typing import Optional, Dict, Any
import logging
import requests
from PIL import Image
import io

_DEFAULT_PLACE_LIST = """            - Cầu Rồng, Cầu Thuận Phước, Cầu Trần Thị Lý
            - Bà Nà Hills, Sun World Ba Na Hills, Cầu Vàng (Golden Bridge)
            - Biển Mỹ Khê, Biển Non Nước, Bãi biển Phạm Văn Đồng
            - Chùa Linh Ứng, Chùa Tam Thai, Chùa Quan Âm
            - Ngũ Hành Sơn (Núi Marble)
            - Bán đảo Sơn Trà, Đỉnh Bàn Cờ
            - Bảo tàng Nghệ thuật Điêu khắc Chăm
            - Công viên Châu Á (Asia Park), Sun Wheel
            - Chợ Hàn, Chợ Cồn
            - Sân bay Đà Nẵng, Ga Đà Nẵng"""
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiVisionQA:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.df_places = None
        self._load_places_data()
        print(f"[OK] Google Gemini Vision QA initialized with model: {model}")
    
    def _load_places_data(self):
        """Load dữ liệu địa điểm từ CSV"""
        try:
            self.df_places = pd.read_csv("data/places.csv")
            logger.info(f"[OK] Gemini Vision QA loaded {len(self.df_places)} places from CSV")
        except FileNotFoundError:
            logger.error("[ERROR] File data/places.csv không tồn tại")
            # Fallback to comprehensive mock data
            self.df_places = pd.DataFrame({
                'name': [
                    'Cầu Rồng', 'Bà Nà Hills', 'Biển Mỹ Khê', 'Chùa Linh Ứng',
                    'Ngũ Hành Sơn', 'Công viên Châu Á', 'Bán đảo Sơn Trà',
                    'Cầu Thuận Phước', 'Chợ Hàn', 'Bảo tàng Nghệ thuật Điêu khắc Chăm'
                ],
                'description': [
                    'Cầu Rồng phun lửa và nước vào cuối tuần, biểu tượng của Đà Nẵng',
                    'Khu du lịch trên núi với cáp treo dài nhất thế giới và Làng Pháp',
                    'Bãi biển đẹp nhất Đà Nẵng với cát trắng và nước trong xanh',
                    'Ngôi chùa lớn nhất Đà Nẵng với tượng Phật Quan Âm cao 67 mét',
                    '5 ngọn núi đá cẩm thạch với hang động và chùa chiền',
                    'Công viên giải trí với vòng quay Sun Wheel biểu tượng',
                    'Khu bảo tồn thiên nhiên với rừng nguyên sinh và khỉ',
                    'Cầu dây văng dài nhất Việt Nam, nối hai bờ sông Hàn',
                    'Chợ truyền thống lớn nhất Đà Nẵng với đặc sản địa phương',
                    'Bảo tàng trưng bày hiện vật văn hóa Chăm Pa quý giá'
                ],
                'address': [
                    'Cầu Rồng, Sơn Trà, Đà Nẵng',
                    'Bà Nà Hills, Hòa Vang, Đà Nẵng',
                    'Biển Mỹ Khê, Sơn Trà, Đà Nẵng',
                    'Chùa Linh Ứng, Sơn Trà, Đà Nẵng',
                    'Ngũ Hành Sơn, Đà Nẵng',
                    'Công viên Châu Á, Hải Châu, Đà Nẵng',
                    'Bán đảo Sơn Trà, Đà Nẵng',
                    'Cầu Thuận Phước, Sơn Trà, Đà Nẵng',
                    'Chợ Hàn, Hải Châu, Đà Nẵng',
                    'Bảo tàng Chăm, Hải Châu, Đà Nẵng'
                ],
                'category': [
                    'sightseeing', 'sightseeing', 'sightseeing', 'sightseeing',
                    'sightseeing', 'sightseeing', 'sightseeing', 'sightseeing',
                    'shopping', 'museum'
                ]
            })
    
    def _download_image(self, image_url: str) -> Optional[Image.Image]:
        """Download image từ URL với timeout và error handling cải tiến"""
        try:
            print(f"📥 Downloading image from: {image_url}")
            
            # Thêm headers để tránh bị chặn
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.google.com/'
            }
            
            response = requests.get(image_url, timeout=15, headers=headers)
            response.raise_for_status()
            
            # Kiểm tra content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.error(f"[ERROR] URL không phải là ảnh: {content_type}")
                return None
            
            # Kiểm tra kích thước file
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                logger.error(f"[ERROR] Ảnh quá lớn: {content_length} bytes")
                return None
            
            image = Image.open(io.BytesIO(response.content))
            
            # Resize ảnh nếu quá lớn để tiết kiệm bandwidth
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            print(f"[OK] Image downloaded successfully: {image.size} pixels")
            return image
            
        except requests.exceptions.Timeout:
            logger.error("[ERROR] Timeout khi download ảnh (quá 15 giây)")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"[ERROR] Lỗi HTTP {e.response.status_code}: {e.response.reason}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("[ERROR] Lỗi kết nối - không thể truy cập URL")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR] Lỗi download ảnh: {e}")
            return None
        except Exception as e:
            logger.error(f"[ERROR] Lỗi xử lý ảnh: {e}")
            return None
    
    def _load_local_image(self, image_path: str) -> Optional[Image.Image]:
        """Load image từ local file"""
        try:
            if not os.path.exists(image_path):
                logger.error(f"[ERROR] File không tồn tại: {image_path}")
                return None
            
            image = Image.open(image_path)
            
            # Resize ảnh nếu quá lớn
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            print(f"[OK] Local image loaded: {image.size} pixels")
            return image
            
        except Exception as e:
            logger.error(f"[ERROR] Lỗi load ảnh local: {e}")
            return None
    
    def _test_gemini_connection(self) -> bool:
        """Test kết nối với Gemini API"""
        try:
            # Test đơn giản với text prompt
            response = self.model.generate_content("Hello")
            return response.text is not None
        except Exception as e:
            logger.error(f"[ERROR] Gemini API connection test failed: {e}")
            return False
    
    def recognize_place(self, image_path_or_url: str, question: Optional[str] = None) -> Dict[str, Any]:
        """
        Nhận diện địa danh từ ảnh sử dụng Google Gemini Vision THẬT
        """
        try:
            print(f"🔍 Gemini Vision analyzing: {image_path_or_url}")
            
            # Không test connection trước (vì có thể fail do quota nhưng vẫn muốn thử)
            # Sẽ xử lý lỗi khi gọi API thực tế
            
            # Xác định loại ảnh và load
            if image_path_or_url.startswith(('http://', 'https://')):
                image = self._download_image(image_path_or_url)
            else:
                image = self._load_local_image(image_path_or_url)
            
            if not image:
                return {
                    "success": False,
                    "error": "Không thể tải hoặc xử lý ảnh",
                    "confidence": "thấp",
                    "source": "gemini_vision"
                }
            
            # Lấy danh sách địa danh từ database để cải thiện prompt
            place_list = ""
            place_details_list = ""
            if self.df_places is not None and len(self.df_places) > 0:
                # Lấy top 100 địa danh phổ biến nhất (sắp xếp theo popularity và rating)
                df_sorted = self.df_places.sort_values(
                    by=['popularity', 'rating', 'review_count'], 
                    ascending=[False, False, False]
                ).head(100)
                
                # Tạo danh sách tên địa danh
                place_names = df_sorted['name'].tolist()
                place_list = "\n".join([f"            - {name}" for name in place_names])
                
                # Tạo danh sách chi tiết với description cho các địa danh nổi tiếng nhất (top 50)
                top_50 = df_sorted.head(50)
                place_details = []
                for idx, row in top_50.iterrows():
                    name = str(row.get('name', ''))
                    desc = str(row.get('desc', ''))[:100]  # Giới hạn 100 ký tự
                    category = str(row.get('category', ''))
                    address = str(row.get('address', ''))[:50]  # Giới hạn 50 ký tự
                    if name and name != 'nan':
                        detail_str = f"            - {name}"
                        if desc and desc != 'nan' and len(desc) > 10:
                            detail_str += f" ({desc})"
                        if category and category != 'nan':
                            detail_str += f" [Loại: {category}]"
                        place_details.append(detail_str)
                
                place_details_list = "\n".join(place_details)
            
            # Prompt tối ưu cho Gemini Vision với context từ database
            base_prompt = f"""
            Bạn là chuyên gia nhận diện địa danh du lịch Việt Nam, đặc biệt ở Đà Nẵng.
            
            PHÂN TÍCH ẢNH VÀ TRẢ VỀ ĐỊNH DẠNG JSON CHÍNH XÁC:
            {{
                "place_name": "tên địa danh bằng tiếng Việt (CHÍNH XÁC từ danh sách dưới)",
                "confidence": "cao/trung bình/thấp",
                "reasoning": "giải thích ngắn dựa trên kiến trúc, đặc điểm nhận dạng, màu sắc, hình dạng"
            }}
            
            QUY TẮC QUAN TRỌNG:
            1. ƯU TIÊN tên tiếng Việt CHÍNH XÁC từ danh sách database (ví dụ: "Cầu Rồng" thay vì "Dragon Bridge")
            2. So sánh ảnh với các đặc điểm nhận dạng: kiến trúc, màu sắc, hình dạng, biểu tượng
            3. Chỉ trả về địa danh DU LỊCH ĐÀ NẴNG có trong database
            4. Nếu KHÔNG CHẮC CHẮN 100%, đặt confidence = "thấp"
            5. Nếu là ảnh CHUNG CHUNG (biển, núi, đường phố không rõ), trả place_name = ""
            6. LUÔN trả về JSON hợp lệ, KHÔNG thêm text nào khác
            7. Nếu nhận diện được nhưng không chắc tên chính xác, dùng fuzzy matching với danh sách
            
            ĐỊA DANH ĐÀ NẴNG TRONG DATABASE (TOP 100):
{place_list or _DEFAULT_PLACE_LIST}

            CHI TIẾT CÁC ĐỊA DANH NỔI TIẾNG NHẤT (TOP 50):
{place_details_list or ""}
            
            ĐẶC ĐIỂM NHẬN DẠNG QUAN TRỌNG:
            - Cầu Rồng: Cầu màu vàng với hình rồng, phun lửa/nước vào cuối tuần, biểu tượng Đà Nẵng
            - Cầu Vàng (Golden Bridge): Cầu đi bộ màu vàng, hai bàn tay khổng lồ đỡ cầu, ở Bà Nà Hills
            - Bà Nà Hills: Núi cao, cáp treo dài nhất thế giới, kiến trúc Pháp, Làng Pháp
            - Chùa Linh Ứng: Tượng Phật Quan Âm trắng lớn cao 67m, biển xung quanh, trên bán đảo Sơn Trà
            - Ngũ Hành Sơn: 5 ngọn núi đá cẩm thạch, hang động, chùa chiền
            - Biển Mỹ Khê: Bãi biển cát trắng, nước trong xanh, nhiều resort ven biển
            - Asia Park: Công viên giải trí với Sun Wheel (vòng quay lớn), nhiều trò chơi
            - Bảo tàng Chăm: Kiến trúc Pháp, trưng bày hiện vật Chăm Pa, màu vàng cam
            - Cầu Thuận Phước: Cầu dây văng dài, màu trắng, nối hai bờ sông Hàn
            - Chợ Hàn: Chợ truyền thống, kiến trúc cổ, nhiều quầy hàng
            
            Nếu ảnh KHÔNG PHẢI là địa danh Đà Nẵng trong danh sách, trả về place_name = ""
            """
            
            # Thêm question vào prompt nếu có
            if question:
                prompt = f"{base_prompt}\n\nCÂU HỎI CỦA NGƯỜI DÙNG: {question}\n\nHãy trả lời câu hỏi này dựa trên ảnh và trả về JSON với place_name."
            else:
                prompt = base_prompt
            
            print("🤖 Calling Gemini Vision API...")
            if question:
                print(f"📝 Question: {question}")
            
            # Gọi Gemini Vision API THẬT với error handling
            try:
                response = self.model.generate_content([
                    prompt,
                    image
                ])
            except Exception as api_error:
                error_str = str(api_error)
                # Kiểm tra lỗi quota/rate limit
                if "429" in error_str or "quota" in error_str.lower() or "Quota exceeded" in error_str:
                    return {
                        "success": False,
                        "error": "Gemini API đã hết quota (vượt giới hạn free tier). Vui lòng đợi một chút rồi thử lại.",
                        "error_type": "quota_exceeded",
                        "error_detail": "Gemini free tier có giới hạn số lần gọi API mỗi phút. Bạn có thể: 1) Đợi 10-15 giây rồi thử lại, 2) Nâng cấp lên paid plan tại https://ai.google.dev/pricing",
                        "confidence": "thấp",
                        "source": "gemini_vision"
                    }
                elif "rate limit" in error_str.lower():
                    return {
                        "success": False,
                        "error": "Đã vượt quá giới hạn số lần gọi API. Vui lòng đợi một chút rồi thử lại.",
                        "error_type": "rate_limit",
                        "confidence": "thấp",
                        "source": "gemini_vision"
                    }
                else:
                    # Re-raise để xử lý ở catch block bên ngoài
                    raise
            
            result_text = response.text.strip()
            print(f"[OK] Gemini Vision raw response: {result_text}")
            
            # Parse JSON response từ Gemini
            vision_result = self._parse_gemini_response(result_text)
            
            place_name = vision_result.get("place_name", "").strip()
            confidence = vision_result.get("confidence", "thấp")
            
            if not place_name:
                return {
                    "success": False,
                    "error": "Không thể nhận diện địa danh từ ảnh",
                    "confidence": "thấp",
                    "source": "gemini_vision",
                    "gemini_response": result_text
                }
            
            # Match với CSV data
            matched_place = self._fuzzy_match_place(place_name)
            
            result = {
                "success": True,
                "place_name": place_name,
                "confidence": confidence,
                "reasoning": vision_result.get("reasoning", ""),
                "source": "gemini_vision",
                "gemini_response": result_text
            }
            
            if matched_place:
                result["matched"] = matched_place
            else:
                result["note"] = "Đã nhận diện được địa danh nhưng không có trong database"
                # Vẫn trả về thông tin cơ bản ngay cả khi không match
                result["basic_info"] = {
                    "name": place_name,
                    "description": f"Địa danh được nhận diện: {place_name}",
                    "category": "sightseeing"
                }
            
            print(f"🎯 Final result: {result['place_name']} (confidence: {confidence})")
            return result
                
        except Exception as e:
            logger.error(f"[ERROR] Lỗi trong recognize_place: {str(e)}")
            return {
                "success": False,
                "error": f"Lỗi hệ thống: {str(e)}",
                "source": "gemini_vision"
            }
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse response từ Gemini thành JSON"""
        try:
            # Tìm JSON trong response (Gemini có thể thêm text xung quanh)
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                # Clean JSON string
                json_str = json_str.replace('```json', '').replace('```', '').strip()
                return json.loads(json_str)
            else:
                # Fallback: xử lý text response đơn giản
                lines = response_text.split('\n')
                place_name = ""
                confidence = "trung bình"
                reasoning = "Gemini trả về text thay vì JSON"
                
                for line in lines:
                    line_lower = line.lower()
                    if 'tên' in line_lower or 'place_name' in line_lower:
                        place_name = line.split(':')[-1].strip(' "\'')
                    elif 'confidence' in line_lower:
                        conf_text = line.split(':')[-1].strip().lower()
                        if 'cao' in conf_text:
                            confidence = "cao"
                        elif 'thấp' in conf_text:
                            confidence = "thấp"
                    elif 'reasoning' in line_lower or 'lý do' in line_lower:
                        reasoning = line.split(':')[-1].strip()
                
                return {
                    "place_name": place_name or "",
                    "confidence": confidence,
                    "reasoning": reasoning
                }
                
        except json.JSONDecodeError as e:
            logger.warning(f"[WARN] Không parse được JSON từ Gemini: {e}")
            # Try to extract place name from text
            place_name = ""
            if "Cầu Rồng" in response_text:
                place_name = "Cầu Rồng"
            elif "Bà Nà" in response_text:
                place_name = "Bà Nà Hills"
            elif "Mỹ Khê" in response_text:
                place_name = "Biển Mỹ Khê"
            elif "Linh Ứng" in response_text:
                place_name = "Chùa Linh Ứng"
                
            return {
                "place_name": place_name,
                "confidence": "trung bình",
                "reasoning": "Lỗi parse JSON từ Gemini response"
            }
    
    def _fuzzy_match_place(self, recognized_name: str) -> Optional[Dict[str, Any]]:
        """Fuzzy match tên địa danh với CSV"""
        if self.df_places is None or self.df_places.empty:
            return None
        
        place_names = self.df_places['name'].astype(str).tolist()
        
        # Tìm match tốt nhất
        best_match = process.extractOne(
            recognized_name, 
            place_names,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=50  # Giảm ngưỡng để match nhiều hơn
        )
        
        if best_match:
            matched_name, score, idx = best_match
            print(f"🔍 Fuzzy match: '{recognized_name}' -> '{matched_name}' (score: {score})")
            
            if score >= 60:  # Ngưỡng tin cậy
                matched_row = self.df_places.iloc[idx]
                return self._format_place_info(matched_row)
        
        return None
    
    def _format_place_info(self, row: pd.Series) -> Dict[str, Any]:
        """Định dạng thông tin địa điểm"""
        return {
            "name": row.get('name', ''),
            "description": row.get('description', ''),
            "address": row.get('address', ''),
            "opening_hours": f"{row.get('open_time', '')} - {row.get('close_time', '')}".strip(' -'),
            "best_time": row.get('best_time', 'Sáng sớm hoặc chiều tối'),
            "tags": row.get('tags', 'landmark,tourist,popular'),
            "tips": "Nên đến vào buổi sáng để tránh đông đúc",
            "avg_cost": row.get('avg_cost', ''),
            "category": row.get('category', 'sightseeing')
        }


# Global instance
gemini_vision_qa_instance = None

def init_gemini_vision_qa(api_key: str):
    """Khởi tạo Gemini Vision QA instance"""
    global gemini_vision_qa_instance
    try:
        gemini_vision_qa_instance = GeminiVisionQA(api_key)
        print(f"[OK] Gemini instance created: {gemini_vision_qa_instance is not None}")
        return gemini_vision_qa_instance
    except Exception as e:
        print(f"[ERROR] Lỗi khởi tạo Gemini Vision QA: {e}")
        return None