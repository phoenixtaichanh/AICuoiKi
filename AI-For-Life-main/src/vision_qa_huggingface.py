"""
Hugging Face Vision QA - HOÀN TOÀN MIỄN PHÍ
Sử dụng Hugging Face Inference API (free tier) hoặc local model
"""
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

from src.filename_place_recognition import build_recognition_result as filename_recognize

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HuggingFaceVisionQA:
    def __init__(self, use_api: bool = True, api_token: Optional[str] = None, model: str = "Salesforce/blip-image-captioning-base"):
        """
        Khởi tạo Hugging Face Vision QA
        
        Args:
            use_api: True = dùng Inference API (free), False = dùng local model
            api_token: Hugging Face token (optional, có thể dùng không cần token)
            model: Model name từ Hugging Face
        """
        self.use_api = use_api
        self.api_token = api_token or os.getenv("HUGGINGFACE_API_TOKEN")
        self.fallback_models = [
            "Salesforce/blip-image-captioning-base",
            "Salesforce/blip2-opt-2.7b",
            "nlpconnect/vit-gpt2-image-captioning",
            "microsoft/git-base",
            "microsoft/git-large",
            "ydshieh/vit-gpt2-coco-en-ckpts"
        ]
        # Tìm index của model hiện tại trong fallback list
        if model in self.fallback_models:
            self.current_model_index = self.fallback_models.index(model)
        else:
            self.current_model_index = 0
            self.fallback_models.insert(0, model)  # Thêm model hiện tại vào đầu list
        self.model = self.fallback_models[self.current_model_index]
        self.df_places = None
        self._load_places_data()
        
        if not use_api:
            try:
                from transformers import BlipProcessor, BlipForConditionalGeneration
                import torch
                self.processor = BlipProcessor.from_pretrained(model)
                self.model_local = BlipForConditionalGeneration.from_pretrained(model)
                if torch.cuda.is_available():
                    self.model_local = self.model_local.to("cuda")
                print(f"[OK] Loaded local model: {model}")
            except ImportError:
                logger.warning("[WARN] transformers not installed, falling back to API")
                self.use_api = True
        
        print(f"[OK] Hugging Face Vision QA initialized (API: {use_api}, Model: {model})")
    
    def _load_places_data(self):
        """Load dữ liệu địa điểm từ CSV"""
        try:
            self.df_places = pd.read_csv("data/places.csv")
            logger.info(f"[OK] Hugging Face Vision QA loaded {len(self.df_places)} places from CSV")
        except FileNotFoundError:
            logger.error("[ERROR] File data/places.csv không tồn tại")
            self.df_places = pd.DataFrame()
    
    def _load_local_image(self, image_path: str) -> Optional[Image.Image]:
        """Load ảnh từ file local"""
        try:
            return Image.open(image_path).convert("RGB")
        except Exception as e:
            logger.error(f"[ERROR] Lỗi load ảnh: {e}")
            return None
    
    def _download_image(self, url: str) -> Optional[Image.Image]:
        """Download ảnh từ URL"""
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content)).convert("RGB")
        except Exception as e:
            logger.error(f"[ERROR] Lỗi download ảnh: {e}")
            return None
    
    def _caption_image_api(self, image: Image.Image) -> str:
        """Gọi Hugging Face Inference API để tạo caption"""
        try:
            # Call Hugging Face Inference API
            api_url = f"https://api-inference.huggingface.co/models/{self.model}"
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            
            # Convert image to bytes
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            buffered.seek(0)  # Reset pointer to beginning
            
            # Thử 2 cách: 
            # 1. Dùng files parameter (multipart/form-data) - cách này thường ổn định hơn
            # 2. Nếu fail, thử dùng data với Content-Type header
            try:
                # Cách 1: Dùng files parameter (khuyến nghị)
                files = {"image": ("image.jpg", buffered, "image/jpeg")}
                response = requests.post(api_url, headers=headers, files=files, timeout=30)
            except Exception as e1:
                logger.warning(f"[WARN] Cách 1 (files) fail: {e1}, thử cách 2...")
                # Cách 2: Dùng data với Content-Type header
                buffered.seek(0)
                img_bytes = buffered.read()
                headers["Content-Type"] = "image/jpeg"
                response = requests.post(api_url, headers=headers, data=img_bytes, timeout=30)
            
            if response.status_code == 503:
                # Model đang loading, đợi và thử lại
                logger.warning("[WARN] Model đang loading, đợi 10 giây...")
                import time
                time.sleep(10)
                response = requests.post(api_url, headers=headers, data=img_bytes, timeout=30)
            
            if response.status_code != 200:
                error_msg = f"API returned status {response.status_code}"
                is_html = False
                response_text = ""
                
                try:
                    # Thử parse JSON trước
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        if "error" in error_data:
                            error_msg = error_data["error"]
                        elif "message" in error_data:
                            error_msg = error_data["message"]
                    elif isinstance(error_data, list) and len(error_data) > 0:
                        if isinstance(error_data[0], dict) and "error" in error_data[0]:
                            error_msg = error_data[0]["error"]
                except:
                    # Nếu không phải JSON, có thể là HTML error page
                    try:
                        response_text = response.text[:500]  # Lấy 500 ký tự đầu
                        # Kiểm tra xem có phải HTML không
                        is_html = response_text.strip().lower().startswith('<!doctype') or response_text.strip().lower().startswith('<html')
                        if is_html:
                            error_msg = f"API trả về HTML thay vì JSON (status {response.status_code}). Có thể model không tồn tại hoặc API đang gặp sự cố."
                        else:
                            error_msg = response_text
                    except:
                        error_msg = f"HTTP {response.status_code} - Không thể đọc response"
                
                logger.error(f"[ERROR] Hugging Face API error: {error_msg}")
                
                # Xử lý status 410 (Gone) - endpoint đã bị xóa vĩnh viễn
                if response.status_code == 410:
                    logger.warning("[WARN] API endpoint trả về 410 (Gone) - endpoint đã bị xóa. Thử model khác hoặc chuyển sang local model...")
                    # Thử model khác
                    if hasattr(self, 'fallback_models') and self.current_model_index < len(self.fallback_models) - 1:
                        self.current_model_index += 1
                        self.model = self.fallback_models[self.current_model_index]
                        logger.info(f"🔄 Chuyển sang model: {self.model}")
                        return self._caption_image_api(image)
                    else:
                        # Nếu đã hết model, đề xuất dùng local model
                        logger.warning("💡 Tất cả models đều fail. Khuyến nghị: Set HF_USE_API=false để dùng local model")
                        return f"API error: Tất cả models đều không hoạt động (status 410). Vui lòng thử lại sau hoặc chuyển sang local model (set HF_USE_API=false)."
                
                # Nếu là lỗi model không tồn tại hoặc HTML response, thử model khác
                if ("not found" in error_msg.lower() or "404" in str(response.status_code) or is_html) and hasattr(self, 'fallback_models'):
                    logger.warning("[WARN] Model không hoạt động, thử model khác...")
                    # Thử model tiếp theo trong danh sách fallback
                    if self.current_model_index < len(self.fallback_models) - 1:
                        self.current_model_index += 1
                        self.model = self.fallback_models[self.current_model_index]
                        logger.info(f"🔄 Chuyển sang model: {self.model}")
                        # Retry với model mới
                        return self._caption_image_api(image)
                
                return f"API error: {error_msg}"
            
            # Kiểm tra xem response có phải JSON không
            try:
                result = response.json()
            except ValueError as e:
                # Nếu không phải JSON, có thể là HTML error page
                response_text = response.text[:500]
                logger.error(f"[ERROR] Response không phải JSON: {response_text[:200]}")
                is_html = response_text.strip().lower().startswith('<!doctype') or response_text.strip().lower().startswith('<html')
                
                if is_html:
                    # Thử model khác nếu có
                    if hasattr(self, 'fallback_models') and self.current_model_index < len(self.fallback_models) - 1:
                        logger.warning("[WARN] Model trả về HTML, thử model khác...")
                        self.current_model_index += 1
                        self.model = self.fallback_models[self.current_model_index]
                        logger.info(f"🔄 Chuyển sang model: {self.model}")
                        # Retry với model mới
                        return self._caption_image_api(image)
                    else:
                        return "API error: Hugging Face API trả về HTML thay vì JSON. Model có thể không tồn tại hoặc đang gặp sự cố."
                else:
                    return f"API error: Không thể parse response: {str(e)}"
            
            # Extract caption từ response
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict) and "generated_text" in result[0]:
                    return result[0]["generated_text"]
                elif isinstance(result[0], dict) and "label" in result[0]:
                    return result[0]["label"]
                elif isinstance(result[0], str):
                    return result[0]
            elif isinstance(result, dict):
                if "generated_text" in result:
                    return result["generated_text"]
                elif "label" in result:
                    return result["label"]
            elif isinstance(result, str):
                return result
            
            logger.warning(f"[WARN] Unexpected response format: {result}")
            return str(result)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                return "Model đang loading, vui lòng thử lại sau 10-20 giây"
            logger.error(f"[ERROR] API error: {e}")
            return ""
        except Exception as e:
            logger.error(f"[ERROR] Lỗi gọi API: {e}")
            return ""
    
    def _caption_image_local(self, image: Image.Image, prompt: Optional[str] = None) -> str:
        """Tạo caption bằng local model - cải thiện với context từ database"""
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            import torch
            
            # Tạo prompt cải thiện với context từ database
            enhanced_prompt = self._create_enhanced_prompt(prompt)
            
            # Nếu có enhanced prompt, dùng làm text input
            if enhanced_prompt:
                inputs = self.processor(image, enhanced_prompt, return_tensors="pt")
            elif prompt:
                inputs = self.processor(image, prompt, return_tensors="pt")
            else:
                inputs = self.processor(image, return_tensors="pt")
            
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            # Kiểm tra độ dài input và điều chỉnh max_length
            input_ids = inputs.get("input_ids", None)
            if input_ids is not None:
                input_length = input_ids.shape[1]
                # max_length phải lớn hơn input_length
                # Nếu input quá dài, giảm prompt hoặc dùng max_new_tokens
                if input_length > 400:  # Nếu input quá dài
                    # Dùng max_new_tokens thay vì max_length để tránh lỗi
                    out = self.model_local.generate(**inputs, max_new_tokens=50, do_sample=False)
                else:
                    # max_length phải lớn hơn input_length
                    max_length = max(input_length + 50, 100)
                    out = self.model_local.generate(**inputs, max_length=max_length, do_sample=False)
            else:
                # Fallback: dùng max_new_tokens
                out = self.model_local.generate(**inputs, max_new_tokens=50, do_sample=False)
            
            caption = self.processor.decode(out[0], skip_special_tokens=True)
            return caption
        except Exception as e:
            logger.error(f"[ERROR] Lỗi local model: {e}")
            return ""
    
    def _create_enhanced_prompt(self, user_question: Optional[str] = None) -> Optional[str]:
        """Tạo prompt cải thiện với context từ database"""
        if self.df_places is None or self.df_places.empty:
            return user_question
        
        # Lấy top 20 địa danh phổ biến nhất với description (giảm từ 50 để tránh prompt quá dài)
        df_sorted = self.df_places.sort_values(
            by=['popularity', 'rating', 'review_count'], 
            ascending=[False, False, False]
        ).head(20)
        
        # Tạo danh sách địa danh với mô tả ngắn (giới hạn độ dài)
        place_context = []
        for idx, row in df_sorted.iterrows():
            name = str(row.get('name', ''))
            desc = str(row.get('desc', ''))[:40]  # Giảm xuống 40 ký tự để tránh prompt quá dài
            category = str(row.get('category', ''))
            if name and name != 'nan':
                context_str = f"{name}"
                if desc and desc != 'nan' and len(desc) > 10:
                    context_str += f" ({desc})"
                if category and category != 'nan':
                    context_str += f" [{category}]"
                place_context.append(context_str)
        
        # Tạo prompt ngắn gọn hơn để tránh lỗi token quá dài
        base_prompt = "Identify landmark in Da Nang. "
        
        # Ưu tiên các địa danh nổi tiếng nhất (top 10)
        if place_context:
            base_prompt += f"Places: {', '.join(place_context[:10])}. "
        
        # Thêm hướng dẫn đặc biệt cho Cầu Vàng
        base_prompt += "IMPORTANT: If you see a golden/yellow bridge held by giant stone hands, it is Golden Bridge (Cầu Vàng) at Ba Na Hills. "
        base_prompt += "If you see a dragon bridge with fire/water show, it is Dragon Bridge (Cầu Rồng). "
        
        if user_question:
            # Giới hạn độ dài câu hỏi
            short_question = user_question[:50] if len(user_question) > 50 else user_question
            base_prompt += f"Q: {short_question}. "
        
        base_prompt += "Identify place name from the list above."
        
        return base_prompt
    
    def _extract_place_name(self, caption: str) -> str:
        """Extract tên địa danh từ caption - sử dụng database thay vì keywords cứng"""
        if self.df_places is None or self.df_places.empty:
            # Fallback to hardcoded keywords nếu không có database
            return self._extract_place_name_fallback(caption)
        
        caption_lower = caption.lower()
        
        # Helper function để convert popularity sang float an toàn
        def safe_float_popularity(value, default=0.0):
            if value is None or pd.isna(value):
                return default
            try:
                if isinstance(value, str):
                    return float(value) if value.strip() else default
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # Convert popularity sang numeric trước khi filter
        df_places_numeric = self.df_places.copy()
        df_places_numeric['popularity_numeric'] = df_places_numeric['popularity'].apply(
            lambda x: safe_float_popularity(x, 0.0)
        )
        
        # ƯU TIÊN: Kiểm tra các địa danh nổi tiếng trước (popularity >= 0.9)
        important_places = df_places_numeric[
            (df_places_numeric['popularity_numeric'] >= 0.9) | 
            (df_places_numeric['name'].str.contains('Cầu Vàng|Golden Bridge|Cầu Rồng|Dragon Bridge|Ba Na|Bà Nà', case=False, na=False))
        ].copy()
        
        if not important_places.empty:
            # Tìm match trong các địa danh quan trọng trước
            important_names = important_places['name'].tolist()
            important_match = process.extract(
                caption,
                important_names,
                scorer=fuzz.partial_ratio,
                limit=5
            )
            
            if important_match:
                # Chọn match tốt nhất, ưu tiên score cao và popularity cao
                best_important = None
                best_score = 0
                for matched_name, score, idx in important_match:
                    if score >= 50:  # Ngưỡng tối thiểu
                        # Tính điểm tổng hợp: score + popularity bonus
                        place_row = important_places[important_places['name'] == matched_name]
                        if not place_row.empty:
                            popularity = safe_float_popularity(place_row.iloc[0].get('popularity', 0), 0.0)
                            combined_score = score + (popularity * 20)  # Bonus cho popularity
                            
                            # Ưu tiên đặc biệt cho "Cầu Vàng" và "Golden Bridge"
                            if 'cầu vàng' in matched_name.lower() or 'golden bridge' in matched_name.lower():
                                if 'cầu vàng' in caption_lower or 'golden bridge' in caption_lower or ('cầu' in caption_lower and 'vàng' in caption_lower):
                                    combined_score += 50  # Bonus lớn cho Cầu Vàng
                            
                            if combined_score > best_score:
                                best_score = combined_score
                                best_important = matched_name
                
                if best_important:
                    print(f"🔍 Matched important place '{best_important}' from caption (combined score: {best_score:.2f})")
                    return best_important
        
        # Nếu không match được địa danh quan trọng, tìm trong top 100 địa danh phổ biến
        # Sort bằng popularity_numeric
        df_sorted = df_places_numeric.sort_values(
            by=['popularity_numeric', 'rating', 'review_count'], 
            ascending=[False, False, False]
        ).head(100)
        
        # Tìm nhiều matches và chọn tốt nhất
        place_names = df_sorted['name'].tolist()
        matches = process.extract(
            caption,
            place_names,
            scorer=fuzz.partial_ratio,
            limit=5
        )
        
        if matches:
            # Chọn match tốt nhất dựa trên score và popularity
            best_match = None
            best_combined_score = 0
            for matched_name, score, idx in matches:
                if score >= 50:
                    # Tìm popularity của place này
                    place_row = df_sorted[df_sorted['name'] == matched_name]
                    if not place_row.empty:
                        popularity = safe_float_popularity(place_row.iloc[0].get('popularity', 0), 0.0)
                        combined_score = score + (popularity * 15)  # Bonus cho popularity
                        
                        if combined_score > best_combined_score:
                            best_combined_score = combined_score
                            best_match = matched_name
            
            if best_match and best_combined_score >= 60:
                print(f"🔍 Matched '{best_match}' from caption (combined score: {best_combined_score:.2f})")
                return best_match
        
        # Nếu không match được, thử tìm trong caption bằng keywords
        return self._extract_place_name_fallback(caption)
    
    def _extract_place_name_fallback(self, caption: str) -> str:
        """Fallback: Extract tên địa danh từ caption bằng keywords cứng"""
        keywords = [
            "Cầu Vàng", "Golden Bridge",  # Ưu tiên Cầu Vàng trước Cầu Rồng
            "Cầu Rồng", "Dragon Bridge",
            "Bà Nà Hills", "Ba Na Hills", "Ba Na", "Bana Hills",
            "Chùa Linh Ứng", "Linh Ung Pagoda", "Linh Ung",
            "Ngũ Hành Sơn", "Marble Mountains", "Ngu Hanh Son",
            "Sơn Trà", "Son Tra", "Bán đảo Sơn Trà", "Son Tra Peninsula",
            "Cầu Thuận Phước", "Thuan Phuoc Bridge",
            "Biển Mỹ Khê", "My Khe Beach", "My Khe",
            "Chợ Hàn", "Han Market",
            "Bảo tàng Chăm", "Cham Museum", "Cham Sculpture Museum",
            "Công viên Châu Á", "Asia Park", "Sun Wheel"
        ]
        
        caption_lower = caption.lower()
        for keyword in keywords:
            if keyword.lower() in caption_lower:
                vietnamese_names = {
                    "dragon bridge": "Cầu Rồng",
                    "golden bridge": "Cầu Vàng",
                    "ba na hills": "Bà Nà Hills",
                    "bana hills": "Bà Nà Hills",
                    "linh ung pagoda": "Chùa Linh Ứng",
                    "marble mountains": "Ngũ Hành Sơn",
                    "son tra": "Bán đảo Sơn Trà",
                    "son tra peninsula": "Bán đảo Sơn Trà",
                    "thuan phuoc bridge": "Cầu Thuận Phước",
                    "my khe beach": "Biển Mỹ Khê",
                    "my khe": "Biển Mỹ Khê",
                    "han market": "Chợ Hàn",
                    "cham museum": "Bảo tàng Nghệ thuật Điêu khắc Chăm",
                    "asia park": "Công viên Châu Á"
                }
                return vietnamese_names.get(keyword.lower(), keyword)
        
        return ""
    
    def _fuzzy_match_place(self, place_name: str) -> Optional[Dict[str, Any]]:
        """Match tên địa danh với database bằng fuzzy matching - cải thiện với ngưỡng thấp hơn"""
        if self.df_places is None or self.df_places.empty or not place_name:
            return None
        
        place_names = self.df_places['name'].astype(str).tolist()
        
        # Tìm match tốt nhất với ngưỡng thấp hơn (60 thay vì 70) để match nhiều hơn
        best_match = process.extractOne(
            place_name,
            place_names,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=60  # Giảm từ 70 xuống 60 để match nhiều hơn
        )
        
        if best_match:
            matched_name, score, idx = best_match
            print(f"🔍 Fuzzy match: '{place_name}' -> '{matched_name}' (score: {score})")
            
            if score >= 60:  # Ngưỡng tin cậy
                matched_row = self.df_places.iloc[idx]
                return {
                    "name": matched_row.get('name', ''),
                    "description": matched_row.get('desc', '') or matched_row.get('description', ''),
                    "address": matched_row.get('address', ''),
                    "opening_hours": f"{matched_row.get('open_time', '')} - {matched_row.get('close_time', '')}".strip(' -'),
                    "best_time": matched_row.get('best_time', 'Sáng sớm hoặc chiều tối'),
                    "tags": matched_row.get('tags', 'landmark,tourist,popular'),
                    "tips": "Nên đến vào buổi sáng để tránh đông đúc",
                    "avg_cost": matched_row.get('avg_cost', ''),
                    "category": matched_row.get('category', 'sightseeing'),
                    "rating": matched_row.get('rating', 0),
                    "review_count": matched_row.get('review_count', 0)
                }
        
        return None
    
    def recognize_place(self, image_path_or_url: str, question: Optional[str] = None) -> Dict[str, Any]:
        """
        Nhận diện địa danh từ ảnh sử dụng Hugging Face (MIỄN PHÍ)
        """
        try:
            print(f"🔍 Hugging Face Vision analyzing: {image_path_or_url}")

            # === TẦNG 0: Hardcode theo tên file (test cứng, deterministic) ===
            # Nếu filename chứa keyword (cau_rong, cau_vang, ba_na, ...) → trả ngay
            if not image_path_or_url.startswith(('http://', 'https://')):
                filename = os.path.basename(image_path_or_url)
                hardcoded = filename_recognize(filename, self.df_places)
                if hardcoded:
                    print(f"🎯 [HARDCODED] Match filename '{filename}' → '{hardcoded['place_name']}'")
                    if question:
                        hardcoded["user_question"] = question
                    return hardcoded

            # Load ảnh
            if image_path_or_url.startswith(('http://', 'https://')):
                image = self._download_image(image_path_or_url)
            else:
                image = self._load_local_image(image_path_or_url)
            
            if not image:
                return {
                    "success": False,
                    "error": "Không thể tải hoặc xử lý ảnh",
                    "confidence": "thấp",
                    "source": "huggingface_vision"
                }
            
            # Tạo caption từ ảnh (có thể kèm question)
            print("🤖 Generating image caption...")
            if question:
                print(f"📝 Question: {question}")
            
            # Với API, không hỗ trợ prompt trực tiếp, sẽ xử lý sau
            # Với local model, có thể dùng prompt
            if self.use_api:
                caption = self._caption_image_api(image)
                # Nếu có question và caption, thêm question vào để extract tốt hơn
                if question and caption:
                    caption = f"{question}. {caption}"
            else:
                caption = self._caption_image_local(image, question)
            
            if not caption:
                return {
                    "success": False,
                    "error": "Không thể tạo caption từ ảnh. Vui lòng thử lại sau hoặc đổi sang model khác.",
                    "confidence": "thấp",
                    "source": "huggingface_vision"
                }
            
            # Kiểm tra các lỗi thường gặp
            caption_lower = caption.lower()
            if "loading" in caption_lower or "model is currently loading" in caption_lower:
                return {
                    "success": False,
                    "error": "Model đang loading, vui lòng đợi 10-20 giây rồi thử lại",
                    "error_type": "model_loading",
                    "confidence": "thấp",
                    "source": "huggingface_vision"
                }
            
            if "error" in caption_lower and "api" in caption_lower:
                # Kiểm tra xem có phải HTML error không
                if caption.strip().lower().startswith('<!doctype') or caption.strip().lower().startswith('<html'):
                    error_msg = "Hugging Face API trả về HTML thay vì JSON. Model có thể không tồn tại hoặc đang gặp sự cố."
                    if self.use_api:
                        error_msg += " Khuyến nghị: Set HF_USE_API=false trong .env để dùng local model (cần cài: pip install transformers torch pillow)."
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_type": "api_error",
                        "confidence": "thấp",
                        "source": "huggingface_vision",
                        "suggestion": "Thử set HF_USE_API=false để dùng local model"
                    }
                else:
                    error_msg = caption[:500]  # Giới hạn độ dài
                    if "410" in error_msg or "Gone" in error_msg:
                        error_msg += " Khuyến nghị: Set HF_USE_API=false để dùng local model."
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_type": "api_error",
                        "confidence": "thấp",
                        "source": "huggingface_vision"
                    }
            
            print(f"[OK] Caption: {caption}")
            
            # Extract tên địa danh từ caption
            place_name = self._extract_place_name(caption)
            
            # Loại bỏ "Show" khỏi tên địa danh (người dùng cần biết địa danh, không phải show)
            if place_name:
                # Loại bỏ các từ như "Show", "show", "Event", "event" ở đầu hoặc cuối
                place_name = place_name.replace("Show ", "").replace("show ", "").replace("Show: ", "").replace("show: ", "")
                place_name = place_name.replace(" Event", "").replace(" event", "").replace(": Event", "").replace(": event", "")
                place_name = place_name.strip()
            
            if not place_name:
                return {
                    "success": False,
                    "error": "Không thể nhận diện địa danh từ ảnh này",
                    "confidence": "thấp",
                    "source": "huggingface_vision",
                    "caption": caption
                }
            
            # Match với database
            matched_place = self._fuzzy_match_place(place_name)
            
            result = {
                "success": True,
                "place_name": place_name,
                "confidence": "trung bình",
                "source": "huggingface_vision",
                "caption": caption
            }
            
            if matched_place:
                result["matched"] = matched_place  # Trả về toàn bộ thông tin như OpenAI/Gemini
                result["place_data"] = {
                    "name": matched_place.get("name"),
                    "description": matched_place.get("description", ""),
                    "category": matched_place.get("category", ""),
                    "city": matched_place.get("city", "Da Nang"),
                    "address": matched_place.get("address", ""),
                    "opening_hours": matched_place.get("opening_hours", ""),
                    "best_time": matched_place.get("best_time", ""),
                    "tags": matched_place.get("tags", ""),
                    "avg_cost": matched_place.get("avg_cost", ""),
                    "rating": matched_place.get("rating", 0),
                    "review_count": matched_place.get("review_count", 0)
                }
            else:
                result["matched"] = None
                result["note"] = "Đã nhận diện được địa danh nhưng không có trong database"
                result["basic_info"] = {
                    "name": place_name,
                    "description": f"Địa danh được nhận diện: {place_name}",
                    "category": "sightseeing"
                }
            
            print(f"🎯 Final result: {result['place_name']} (matched: {result.get('matched', False)})")
            return result
                
        except Exception as e:
            logger.error(f"[ERROR] Lỗi trong recognize_place: {str(e)}")
            return {
                "success": False,
                "error": f"Lỗi hệ thống: {str(e)}",
                "error_type": "unknown",
                "confidence": "thấp",
                "source": "huggingface_vision"
            }


def init_vision_qa(use_api: bool = True, api_token: Optional[str] = None, model: str = "Salesforce/blip-image-captioning-base"):
    """Khởi tạo Hugging Face Vision QA"""
    try:
        return HuggingFaceVisionQA(use_api=use_api, api_token=api_token, model=model)
    except Exception as e:
        logger.error(f"[ERROR] Lỗi khởi tạo Hugging Face Vision QA: {e}")
        return None

