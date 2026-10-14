import pandas as pd
import numpy as np
from rapidfuzz import process, fuzz
from sentence_transformers import SentenceTransformer
import re
from typing import Dict, Any, Optional
import os
from .place_details import PlaceDetailsManager

class QASystem:
    def __init__(self, csv_path: str = "data/places.csv", qa_csv_path: str = "data/Q&A.csv"):
        self.df = self._load_data(csv_path)
        self.qa_df = None
        self._load_qa_data(qa_csv_path)
        self.model = None
        self.embeddings = None
        self._init_embedding_model()
        self.place_details = PlaceDetailsManager()
        print(f"🔄 Loading QA System...")
        print(f"   📁 Loaded data from {csv_path}")
        if self.qa_df is not None:
            print(f"   📁 Loaded Q&A data: {len(self.qa_df)} questions")
        print(f"   [OK] QA System ready with {len(self.df)} places")
    
    def _load_data(self, csv_path: str) -> pd.DataFrame:
        """Load và chuẩn bị dữ liệu"""
        try:
            df = pd.read_csv(csv_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {csv_path}")
        
        # Clean data
        df = df.fillna('')
        return df
    
    def _load_qa_data(self, qa_csv_path: str):
        """Load Q&A data từ Q&A.csv"""
        try:
            if os.path.exists(qa_csv_path):
                self.qa_df = pd.read_csv(qa_csv_path)
                self.qa_df = self.qa_df.fillna('')
                print(f"   [OK] Loaded Q&A data from {qa_csv_path}")
            else:
                print(f"   [WARN] Q&A.csv not found at {qa_csv_path}, using places.csv only")
        except Exception as e:
            print(f"   [WARN] Error loading Q&A.csv: {e}")
            self.qa_df = None
    
    def _init_embedding_model(self):
        """Khởi tạo embedding model cho semantic search"""
        try:
            self.model = SentenceTransformer("intfloat/multilingual-e5-base")
            # Load precomputed embeddings nếu có
            try:
                self.embeddings = np.load("models/nn_embeds.npy")
            except:
                print("[WARN] Precomputed embeddings not found, will compute on-demand")
        except Exception as e:
            print(f"[WARN] Could not load embedding model: {e}")
    
    def _normalize_text(self, text: str) -> str:
        """Chuẩn hóa text cho fuzzy matching"""
        text = str(text).lower().strip()
        # Remove accents và ký tự đặc biệt
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _fuzzy_match_name(self, question: str) -> Optional[Dict[str, Any]]:
        """Tìm địa điểm bằng fuzzy matching trên tên"""
        place_names = self.df['name'].astype(str).tolist()
        
        best_match = process.extractOne(
            question,
            place_names,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=60
        )
        
        if best_match:
            matched_name, score, idx = best_match
            if score >= 70:  # Ngưỡng cao cho fuzzy matching
                return self._get_place_info(idx)
        
        return None
    
    def _semantic_search(self, question: str, top_k: int = 3) -> Optional[Dict[str, Any]]:
        """Tìm địa điểm bằng semantic search"""
        if self.model is None or self.embeddings is None:
            return None
        
        try:
            # Encode query
            query_embedding = self.model.encode([question], normalize_embeddings=True)[0]
            
            # Tính similarity
            similarities = np.dot(self.embeddings, query_embedding)
            
            # Lấy top result
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]
            
            if best_score > 0.3:  # Ngưỡng cho semantic search
                return self._get_place_info(best_idx)
        
        except Exception as e:
            print(f"[WARN] Semantic search error: {e}")
        
        return None
    
    def _get_place_info(self, idx: int) -> Dict[str, Any]:
        """Lấy thông tin địa điểm theo index"""
        row = self.df.iloc[idx]
        
        # Format opening hours
        opening_hours = ""
        if row.get('open_time') and row.get('close_time'):
            opening_hours = f"{row['open_time']} - {row['close_time']}"
            if row.get('closed_days'):
                opening_hours += f" (closed: {row['closed_days']})"
        
        # Format price info
        price_info = ""
        if row.get('avg_cost') and float(row['avg_cost']) > 0:
            price_info = f"~{int(row['avg_cost']):,} VND"
        elif row.get('price_level'):
            price_info = row['price_level']
        
        return {
            "name": row['name'],
            "category": row.get('category', ''),
            "description": row.get('description', ''),
            "address": row.get('address', ''),
            "opening_hours": opening_hours,
            "price": price_info,
            "rating": float(row.get('rating', 0)),
            "best_time": row.get('best_time', ''),
            "tags": row.get('tags', ''),
            "duration": f"{row.get('duration_min', 60)} phút",
            "confidence": "cao",
            "source": "exact_match"
        }
    
    def _extract_question_type(self, question: str) -> str:
        """Phân loại câu hỏi"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['lịch sử', 'hình thành', 'ra đời', 'xây dựng', 'history', 'established']):
            return "history"
        elif any(word in question_lower for word in ['nổi bật', 'đặc biệt', 'nổi tiếng', 'highlights', 'special', 'famous']):
            return "highlights"
        elif any(word in question_lower for word in ['đặc điểm', 'kiến trúc', 'thiết kế', 'features', 'architecture']):
            return "features"
        elif any(word in question_lower for word in ['văn hóa', 'ý nghĩa', 'giá trị', 'cultural', 'significance']):
            return "cultural"
        elif any(word in question_lower for word in ['mẹo', 'lưu ý', 'nên', 'tips', 'advice']):
            return "tips"
        elif any(word in question_lower for word in ['ở đâu', 'địa chỉ', 'vị trí']):
            return "location"
        elif any(word in question_lower for word in ['mấy giờ', 'giờ mở', 'giờ đóng', 'đóng cửa']):
            return "opening_hours"
        elif any(word in question_lower for word in ['giá', 'bao nhiêu tiền', 'vé', 'chi phí']):
            return "price"
        elif any(word in question_lower for word in ['tốt nhất', 'nên đi', 'best time']):
            return "best_time"
        elif any(word in question_lower for word in ['là gì', 'giới thiệu', 'thông tin']):
            return "general_info"
        else:
            return "general_info"
    
    def _match_qa_database(self, question: str) -> Optional[Dict[str, Any]]:
        """Tìm câu trả lời trong Q&A database"""
        if self.qa_df is None or self.qa_df.empty:
            return None
        
        question_lower = question.lower()
        
        # Tìm trong keywords và question
        for idx, row in self.qa_df.iterrows():
            keywords = str(row.get('keywords', '')).lower()
            qa_question = str(row.get('question', '')).lower()
            
            # Check nếu question match với keywords hoặc question trong Q&A
            if any(keyword in question_lower for keyword in keywords.split(',')) or \
               any(word in question_lower for word in qa_question.split()):
                return {
                    'answer': row.get('answer', ''),
                    'place_name': row.get('place_name', ''),
                    'category': row.get('category', ''),
                    'source': 'Q&A.csv'
                }
        
        return None
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Trả lời câu hỏi về địa điểm
        
        Args:
            question: Câu hỏi từ user
            
        Returns:
            Dict chứa thông tin trả lời
        """
        if not question or len(question.strip()) < 2:
            return {
                "success": False,
                "error": "Câu hỏi quá ngắn",
                "answer": "Vui lòng nhập câu hỏi cụ thể hơn."
            }
        
        print(f"🔍 QA System processing: {question}")
        
        # Thử tìm trong Q&A database trước
        qa_match = self._match_qa_database(question)
        if qa_match:
            return {
                "success": True,
                "question": question,
                "question_type": "qa_database",
                "answer": qa_match['answer'],
                "place_name": qa_match.get('place_name', ''),
                "source": "Q&A.csv",
                "confidence": "cao"
            }
        
        # Phân loại câu hỏi
        q_type = self._extract_question_type(question)
        
        # Thử fuzzy matching trước
        place_info = self._fuzzy_match_name(question)
        
        # Nếu không tìm thấy, thử semantic search
        if not place_info and self.model:
            place_info = self._semantic_search(question)
        
        if place_info:
            place_name = place_info.get('name', '')
            
            # Lấy thông tin chi tiết nếu có
            details = self.place_details.get_details(place_name) if place_name else None
            
            # Tạo câu trả lời dựa trên loại câu hỏi
            if q_type == "history":
                answer = self._format_history_answer(place_info, details)
            elif q_type == "highlights":
                answer = self._format_highlights_answer(place_info, details)
            elif q_type == "features":
                answer = self._format_features_answer(place_info, details)
            elif q_type == "cultural":
                answer = self._format_cultural_answer(place_info, details)
            elif q_type == "tips":
                answer = self._format_tips_answer(place_info, details)
            elif q_type == "location":
                answer = self._format_location_answer(place_info)
            elif q_type == "opening_hours":
                answer = self._format_opening_hours_answer(place_info)
            elif q_type == "price":
                answer = self._format_price_answer(place_info)
            elif q_type == "best_time":
                answer = self._format_best_time_answer(place_info)
            elif q_type == "general_info":
                answer = self._format_general_answer(place_info, details)
            else:
                answer = self._format_general_answer(place_info, details)
            
            result = {
                "success": True,
                "question": question,
                "question_type": q_type,
                "answer": answer,
                "place_info": place_info,
                "confidence": place_info.get("confidence", "cao")
            }
            
            # Thêm thông tin chi tiết nếu có
            if details:
                result["details"] = {
                    "has_history": bool(details.get('history')),
                    "has_highlights": bool(details.get('highlights')),
                    "has_features": bool(details.get('features')),
                    "has_cultural": bool(details.get('cultural_significance')),
                    "has_tips": bool(details.get('tips'))
                }
            
            return result
        else:
            return {
                "success": False,
                "error": "Không tìm thấy thông tin",
                "answer": f"Xin lỗi, tôi không tìm thấy thông tin về '{question}' trong cơ sở dữ liệu. Vui lòng thử với tên địa điểm cụ thể hơn.",
                "suggestion": "Thử với tên chính xác như: 'Cầu Rồng', 'Bà Nà Hills', 'Biển Mỹ Khê'"
            }
    
    def _format_general_answer(self, place_info: Dict, details: Optional[Dict] = None) -> str:
        """Định dạng câu trả lời chung"""
        parts = [
            f"**{place_info['name']}**",
            f"{place_info['description']}",
        ]
        
        # Thêm thông tin chi tiết nếu có
        if details:
            if details.get('full_description'):
                parts.append(f"\n{details['full_description']}")
        
        if place_info['address']:
            parts.append(f"📍 **Địa chỉ:** {place_info['address']}")
        
        if place_info['opening_hours']:
            parts.append(f"🕒 **Giờ mở cửa:** {place_info['opening_hours']}")
        
        if place_info['price']:
            parts.append(f"💰 **Chi phí:** {place_info['price']}")
        
        if place_info['best_time']:
            parts.append(f"⏰ **Thời gian tốt nhất:** {place_info['best_time']}")
        
        if place_info['rating'] > 0:
            parts.append(f"* **Đánh giá:** {place_info['rating']}/5")
        
        # Thêm highlights nếu có
        if details and details.get('highlights'):
            parts.append(f"\n✨ **Điểm nổi bật:**\n{details['highlights']}")
        
        return "\n\n".join(parts)
    
    def _format_history_answer(self, place_info: Dict, details: Optional[Dict] = None) -> str:
        """Định dạng câu trả lời về lịch sử"""
        parts = [f"**Lịch sử hình thành của {place_info['name']}**"]
        
        if details and details.get('history'):
            parts.append(details['history'])
        else:
            parts.append(f"Hiện tại chưa có thông tin chi tiết về lịch sử hình thành của {place_info['name']}.")
            parts.append(f"Mô tả chung: {place_info['description']}")
        
        return "\n\n".join(parts)
    
    def _format_highlights_answer(self, place_info: Dict, details: Optional[Dict] = None) -> str:
        """Định dạng câu trả lời về điểm nổi bật"""
        parts = [f"**Điểm nổi bật của {place_info['name']}**"]
        
        if details and details.get('highlights'):
            highlights = details['highlights'].split(';')
            for highlight in highlights:
                if highlight.strip():
                    parts.append(f"• {highlight.strip()}")
        else:
            parts.append(f"Điểm nổi bật: {place_info['description']}")
            if place_info.get('tags'):
                parts.append(f"Tags: {place_info['tags']}")
        
        return "\n\n".join(parts)
    
    def _format_features_answer(self, place_info: Dict, details: Optional[Dict] = None) -> str:
        """Định dạng câu trả lời về đặc điểm"""
        parts = [f"**Đặc điểm nổi bật của {place_info['name']}**"]
        
        if details and details.get('features'):
            features = details['features'].split(';')
            for feature in features:
                if feature.strip():
                    parts.append(f"• {feature.strip()}")
        else:
            parts.append(f"Đặc điểm: {place_info['description']}")
            if place_info.get('category'):
                parts.append(f"Loại: {place_info['category']}")
        
        return "\n\n".join(parts)
    
    def _format_cultural_answer(self, place_info: Dict, details: Optional[Dict] = None) -> str:
        """Định dạng câu trả lời về ý nghĩa văn hóa"""
        parts = [f"**Ý nghĩa văn hóa của {place_info['name']}**"]
        
        if details and details.get('cultural_significance'):
            parts.append(details['cultural_significance'])
        else:
            parts.append(f"Hiện tại chưa có thông tin chi tiết về ý nghĩa văn hóa của {place_info['name']}.")
            parts.append(f"Mô tả: {place_info['description']}")
        
        return "\n\n".join(parts)
    
    def _format_tips_answer(self, place_info: Dict, details: Optional[Dict] = None) -> str:
        """Định dạng câu trả lời về mẹo du lịch"""
        parts = [f"**Mẹo du lịch cho {place_info['name']}**"]
        
        if details and details.get('tips'):
            tips = details['tips'].split(';')
            for tip in tips:
                if tip.strip():
                    parts.append(f"💡 {tip.strip()}")
        else:
            parts.append(f"Thời gian tốt nhất: {place_info.get('best_time', 'Nên tham quan vào buổi sáng hoặc chiều tối')}")
            if place_info.get('duration'):
                parts.append(f"Thời gian tham quan: {place_info['duration']}")
        
        return "\n\n".join(parts)
    
    def _format_location_answer(self, place_info: Dict) -> str:
        """Định dạng câu trả lời về vị trí"""
        if place_info['address']:
            return f"**{place_info['name']}** nằm tại: {place_info['address']}"
        else:
            return f"**{place_info['name']}** - {place_info['description']}"
    
    def _format_opening_hours_answer(self, place_info: Dict) -> str:
        """Định dạng câu trả lời về giờ mở cửa"""
        if place_info['opening_hours']:
            return f"**{place_info['name']}** mở cửa: {place_info['opening_hours']}"
        else:
            return f"Thông tin giờ mở cửa của **{place_info['name']}** hiện không có sẵn."
    
    def _format_price_answer(self, place_info: Dict) -> str:
        """Định dạng câu trả lời về giá"""
        if place_info['price']:
            return f"**{place_info['name']}** có chi phí: {place_info['price']}"
        else:
            return f"Thông tin giá vé của **{place_info['name']}** hiện không có sẵn."
    
    def _format_best_time_answer(self, place_info: Dict) -> str:
        """Định dạng câu trả lời về thời gian tốt nhất"""
        if place_info['best_time']:
            return f"Thời gian tốt nhất để ghé thăm **{place_info['name']}** là: {place_info['best_time']}"
        else:
            return f"**{place_info['name']}** - {place_info['description']}"


# Global instance
qa_system = QASystem()