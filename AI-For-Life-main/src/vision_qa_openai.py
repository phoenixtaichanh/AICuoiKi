import os
import json
import pandas as pd
from rapidfuzz import process, fuzz
from typing import Optional, Dict, Any
import logging
import requests
from PIL import Image
import io
import base64
from openai import OpenAI

_DEFAULT_PLACE_LIST = """            - Cầu Rồng, Cầu Thuận Phước, Cầu Trần Thị Lý
            - Bà Nà Hills, Sun World Ba Na Hills, Cầu Vàng (Golden Bridge)
            - Biển Mỹ Khê, Biển Non Nước, Bãi biển Phạm Văn Đồng
            - Chùa Linh Ứng, Chùa Tam Thai, Chùa Quan Âm
            - Ngũ Hành Sơn (Núi Marble)
            - Bán đảo Sơn Trà, Đỉnh Bàn Cờ
            - Bảo tàng Nghệ thuật Điêu khắc Chăm
            - Công viên Châu Á (Asia Park), Sun Wheel
            - Chợ Hàn, Chợ Cồn"""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIVisionQA:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Khởi tạo OpenAI Vision QA với API key thật"""
        if not api_key or not api_key.startswith('sk-'):
            raise ValueError("OpenAI API key không hợp lệ. Key phải bắt đầu bằng 'sk-'")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.df_places = None
        self._load_places_data()
        print(f"[OK] OpenAI Vision QA initialized với model: {model}")
    
    def _load_places_data(self):
        """Load dữ liệu địa điểm từ CSV thật"""
        try:
            self.df_places = pd.read_csv("data/places.csv")
            logger.info(f"[OK] Đã load {len(self.df_places)} địa điểm từ CSV")
        except FileNotFoundError:
            logger.error("[ERROR] File data/places.csv không tồn tại")
            # Tạo dữ liệu mẫu tạm thời
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
        """Download image từ URL với error handling cải tiến"""
        try:
            print(f"📥 Đang download ảnh từ: {image_url}")
            
            # Headers chi tiết hơn để tránh bị chặn
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site',
                'Cache-Control': 'max-age=0'
            }
            
            # Thêm timeout và verify=False để bỏ qua SSL errors (chỉ cho test)
            response = requests.get(image_url, timeout=20, headers=headers, stream=True, verify=False)
            response.raise_for_status()
            
            # Kiểm tra content type
            content_type = response.headers.get('content-type', '').lower()
            valid_image_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif']
            
            if not any(img_type in content_type for img_type in valid_image_types):
                logger.error(f"[ERROR] URL không phải là ảnh hợp lệ: {content_type}")
                return None
            
            # Kiểm tra kích thước file
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > 20 * 1024 * 1024:  # 20MB limit
                logger.error(f"[ERROR] Ảnh quá lớn: {content_length} bytes")
                return None
            
            # Đọc ảnh với buffer
            image_data = io.BytesIO()
            total_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                total_size += len(chunk)
                if total_size > 20 * 1024 * 1024:  # 20MB limit
                    raise ValueError("Ảnh vượt quá kích thước cho phép")
                image_data.write(chunk)
            
            image_data.seek(0)
            
            # Kiểm tra xem có phải là ảnh hợp lệ không
            try:
                image = Image.open(image_data)
                # Thử verify ảnh
                image.verify()
            except Exception as e:
                logger.error(f"[ERROR] File không phải là ảnh hợp lệ: {e}")
                return None
            
            # Mở lại ảnh sau khi verify
            image_data.seek(0)
            image = Image.open(image_data)
            
            # Convert sang RGB nếu cần
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Resize ảnh nếu quá lớn
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            print(f"[OK] Download ảnh thành công: {image.size} pixels, format: {image.format}")
            return image
            
        except requests.exceptions.Timeout:
            logger.error("[ERROR] Timeout khi download ảnh (quá 20 giây)")
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
    
    def _test_openai_connection(self) -> bool:
        """Test kết nối với OpenAI API - không fail nếu có lỗi quota"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return response.choices[0].message.content is not None
        except Exception as e:
            error_str = str(e)
            # Nếu là lỗi quota, không log như lỗi nghiêm trọng, chỉ return False
            if "429" in error_str or "quota" in error_str.lower() or "insufficient_quota" in error_str.lower():
                logger.warning(f"[WARN] OpenAI API quota exceeded - sẽ hiển thị lỗi chi tiết khi upload ảnh")
                return False
            logger.error(f"[ERROR] Test kết nối OpenAI thất bại: {e}")
            return False
    
    def recognize_place(self, image_path_or_url: str, question: Optional[str] = None) -> Dict[str, Any]:
        """
        Nhận diện địa danh từ ảnh - xử lý cả file local và URL
        """
        try:
            print(f"🔍 OpenAI Vision đang phân tích: {image_path_or_url}")
            
            # Không test connection trước (vì có thể fail do quota nhưng vẫn muốn thử)
            # Sẽ xử lý lỗi khi gọi API thực tế
            
            image = None
            
            # Xác định loại input và xử lý
            if image_path_or_url.startswith(('http://', 'https://')):
                # URL - tải về
                print("🌐 Đang tải ảnh từ URL...")
                image = self._download_image(image_path_or_url)
                if not image:
                    return {
                        "success": False,
                        "error": f"Không thể tải ảnh từ URL: {image_path_or_url}",
                        "confidence": "thấp",
                        "source": "openai_vision"
                    }
            else:
                # File local
                if not os.path.exists(image_path_or_url):
                    return {
                        "success": False,
                        "error": f"File ảnh không tồn tại: {image_path_or_url}",
                        "confidence": "thấp",
                        "source": "openai_vision"
                    }
                
                try:
                    print(f"📁 Đang mở file ảnh local: {image_path_or_url}")
                    image = Image.open(image_path_or_url)
                    
                    # Convert sang RGB nếu cần
                    if image.mode in ('RGBA', 'LA', 'P'):
                        image = image.convert('RGB')
                    
                    # Resize ảnh nếu quá lớn
                    max_size = (1024, 1024)
                    if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                        image.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    print(f"[OK] Mở file ảnh thành công: {image.size} pixels, format: {image.format}")
                    
                except Exception as e:
                    logger.error(f"[ERROR] Lỗi mở file ảnh: {e}")
                    return {
                        "success": False,
                        "error": f"Không thể mở file ảnh: {str(e)}",
                        "confidence": "thấp",
                        "source": "openai_vision"
                    }
            
            # Convert ảnh sang base64
            print("🔄 Đang convert ảnh sang base64...")
            try:
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG", quality=85)
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                image_content = {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_base64}",
                        "detail": "high"
                    }
                }
            except Exception as e:
                logger.error(f"[ERROR] Lỗi convert ảnh sang base64: {e}")
                return {
                    "success": False,
                    "error": f"Lỗi xử lý ảnh: {str(e)}",
                    "confidence": "thấp",
                    "source": "openai_vision"
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
            
            # Prompt tối ưu cho OpenAI Vision với context từ database
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
{place_details_list if place_details_list else ""}

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
            
            print("🤖 Đang gọi OpenAI Vision API...")
            if question:
                print(f"📝 Question: {question}")
            
            # Gọi OpenAI Vision API với error handling tốt hơn
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                image_content
                            ]
                        }
                    ],
                    max_tokens=500,
                    temperature=0.1
                )
            except Exception as api_error:
                error_str = str(api_error)
                # Kiểm tra lỗi quota/rate limit trước khi throw
                if "429" in error_str or "quota" in error_str.lower() or "insufficient_quota" in error_str.lower():
                    return {
                        "success": False,
                        "error": "OpenAI API đã hết quota (hết tiền hoặc vượt giới hạn). Vui lòng kiểm tra tài khoản OpenAI và nạp thêm tiền.",
                        "error_type": "quota_exceeded",
                        "error_detail": "Bạn cần kiểm tra: 1) Tài khoản OpenAI có còn tiền không? 2) Đã vượt giới hạn sử dụng chưa? 3) Có thể cần nâng cấp gói dịch vụ.",
                        "confidence": "thấp",
                        "source": "openai_vision"
                    }
                elif "rate limit" in error_str.lower():
                    return {
                        "success": False,
                        "error": "Đã vượt quá giới hạn số lần gọi API. Vui lòng đợi một chút rồi thử lại.",
                        "error_type": "rate_limit",
                        "confidence": "thấp",
                        "source": "openai_vision"
                    }
                else:
                    # Re-raise để xử lý ở catch block bên ngoài
                    raise
            
            result_text = response.choices[0].message.content
            print(f"[OK] OpenAI Vision response: {result_text}")
            
            # Parse JSON response
            vision_result = self._parse_openai_response(result_text)
            place_name = vision_result.get("place_name", "").strip()
            confidence = vision_result.get("confidence", "thấp")
            
            if not place_name:
                return {
                    "success": False,
                    "error": "Không thể nhận diện địa danh từ ảnh",
                    "confidence": "thấp",
                    "source": "openai_vision",
                    "openai_response": result_text
                }
            
            # Match với CSV data
            matched_place = self._fuzzy_match_place(place_name)
            
            result = {
                "success": True,
                "place_name": place_name,
                "confidence": confidence,
                "reasoning": vision_result.get("reasoning", ""),
                "source": "openai_vision",
                "openai_response": result_text
            }
            
            if matched_place:
                result["matched"] = matched_place
            else:
                result["note"] = "Đã nhận diện được địa danh nhưng không có trong database"
                result["basic_info"] = {
                    "name": place_name,
                    "description": f"Địa danh được nhận diện: {place_name}",
                    "category": "sightseeing"
                }
            
            print(f"🎯 Kết quả cuối: {result['place_name']} (độ tin cậy: {confidence})")
            return result
                
        except Exception as e:
            error_str = str(e)
            logger.error(f"[ERROR] Lỗi trong recognize_place: {error_str}")
            
            # Xử lý lỗi quota/quota exceeded
            if "429" in error_str or "quota" in error_str.lower() or "insufficient_quota" in error_str.lower():
                return {
                    "success": False,
                    "error": "OpenAI API đã hết quota (hết tiền hoặc vượt giới hạn). Vui lòng kiểm tra tài khoản OpenAI và nạp thêm tiền.",
                    "error_type": "quota_exceeded",
                    "error_detail": "Bạn cần kiểm tra: 1) Tài khoản OpenAI có còn tiền không? 2) Đã vượt giới hạn sử dụng chưa? 3) Có thể cần nâng cấp gói dịch vụ.",
                    "confidence": "thấp",
                    "source": "openai_vision"
                }
            # Xử lý lỗi rate limit
            elif "rate limit" in error_str.lower() or "429" in error_str:
                return {
                    "success": False,
                    "error": "Đã vượt quá giới hạn số lần gọi API. Vui lòng đợi một chút rồi thử lại.",
                    "error_type": "rate_limit",
                    "confidence": "thấp",
                    "source": "openai_vision"
                }
            else:
                return {
                    "success": False,
                    "error": f"Lỗi hệ thống: {error_str}",
                    "error_type": "unknown",
                    "confidence": "thấp",
                    "source": "openai_vision"
                }
    
    def _parse_openai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse response từ OpenAI thành JSON"""
        try:
            # Tìm JSON trong response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                json_str = json_str.replace('```json', '').replace('```', '').strip()
                return json.loads(json_str)
            else:
                # Fallback: xử lý text response
                lines = response_text.split('\n')
                place_name = ""
                confidence = "trung bình"
                reasoning = "OpenAI trả về text thay vì JSON"
                
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
            logger.warning(f"[WARN] Không parse được JSON từ OpenAI: {e}")
            # Extract place name từ text
            place_name = ""
            if "Cầu Rồng" in response_text:
                place_name = "Cầu Rồng"
            elif "Bà Nà" in response_text or "Ba Na" in response_text:
                place_name = "Bà Nà Hills"
            elif "Mỹ Khê" in response_text or "My Khe" in response_text:
                place_name = "Biển Mỹ Khê"
            elif "Linh Ứng" in response_text:
                place_name = "Chùa Linh Ứng"
            elif "Cầu Vàng" in response_text or "Golden Bridge" in response_text:
                place_name = "Cầu Vàng"
                
            return {
                "place_name": place_name,
                "confidence": "trung bình",
                "reasoning": "Lỗi parse JSON từ OpenAI response"
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
            score_cutoff=50
        )
        
        if best_match:
            matched_name, score, idx = best_match
            print(f"🔍 Fuzzy match: '{recognized_name}' -> '{matched_name}' (điểm: {score})")
            
            if score >= 60:  # Ngưỡng tin cậy
                matched_row = self.df_places.iloc[idx]
                return {
                    "name": matched_row.get('name', ''),
                    "description": matched_row.get('description', ''),
                    "address": matched_row.get('address', ''),
                    "opening_hours": f"{matched_row.get('open_time', '')} - {matched_row.get('close_time', '')}".strip(' -'),
                    "best_time": matched_row.get('best_time', 'Sáng sớm hoặc chiều tối'),
                    "tags": matched_row.get('tags', 'landmark,tourist,popular'),
                    "tips": "Nên đến vào buổi sáng để tránh đông đúc",
                    "avg_cost": matched_row.get('avg_cost', ''),
                    "category": matched_row.get('category', 'sightseeing')
                }
        
        return None

# Global instance
vision_qa_instance = None

def init_vision_qa(api_key: str):
    """Khởi tạo Vision QA instance với OpenAI"""
    global vision_qa_instance
    try:
        if not api_key or not api_key.startswith('sk-'):
            raise ValueError("OpenAI API key không hợp lệ")
            
        vision_qa_instance = OpenAIVisionQA(api_key)
        print("[OK] OpenAI Vision QA khởi tạo thành công")
        return vision_qa_instance
    except Exception as e:
        print(f"[ERROR] Lỗi khởi tạo Vision QA: {e}")
        return None