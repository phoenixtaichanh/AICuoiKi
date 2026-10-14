from __future__ import annotations

import math
import numpy as np
import pandas as pd
import joblib
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
from rapidfuzz import process, fuzz
from typing import List, Dict, Any, Optional
import time

from .etl import load_dataset, strip_accents, parse_closed_days
from .vectorizer import load_tfidf
from .textnorm import normalize_query


def haversine(lat1, lon1, lat2, lon2):
    """
    Khoảng cách đường tròn lớn (km). An toàn với float.
    """
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    except Exception:
        return 0.0
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon1 - lon2)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def within_open(r, minute_of_day: int, weekday: int) -> bool:
    """
    Kiểm tra giờ mở cửa + ngày nghỉ. Nếu thiếu dữ liệu → cho qua (True).
    """
    try:
        om = r.get("open_min")
        cm = r.get("close_min")
    except Exception:
        om = r["open_min"] if "open_min" in r else None
        cm = r["close_min"] if "close_min" in r else None

    # Thiếu giờ → coi như mở
    if pd.isna(om) or pd.isna(cm):
        return True

    # Convert sang int để so sánh
    try:
        om = int(float(om)) if om is not None else None
        cm = int(float(cm)) if cm is not None else None
    except (ValueError, TypeError):
        # Nếu không convert được → coi như mở
        return True

    # Kiểm tra lại sau khi convert
    if om is None or cm is None:
        return True

    cs = r.get("closed_set", set())
    if isinstance(cs, (list, tuple)):
        cs = set(cs)
    elif not isinstance(cs, set):
        cs = parse_closed_days(cs) if isinstance(cs, str) else set()

    if weekday in cs:
        return False
    return (om <= minute_of_day <= cm)


def pick(r: dict | None) -> dict | None:
    if not r:
        return None
    keep = [
        "id", "name", "city", "category", "address", "open_time", "close_time", "closed_days",
        "duration_min", "avg_cost", "price_level", "rating", "review_count", "best_time",
        "desc", "tags", "image_url", "lat", "lon", "nn_cos", "ce_score"  # Thêm ce_score
    ]
    result = {}
    for k in keep:
        if k in r:
            value = r[k]
            # Clean data for JSON serialization
            try:
                if isinstance(value, (np.integer, np.int64, np.int32)):
                    value = int(value)
                elif isinstance(value, (np.floating, np.float64, np.float32)):
                    if np.isnan(value) or np.isinf(value):
                        value = 0.0
                    else:
                        value = float(value)
                elif pd.isna(value):
                    value = None
                elif isinstance(value, set):
                    value = list(value)
                elif isinstance(value, float):
                    # Xử lý Python float có thể là NaN
                    if math.isnan(value) or math.isinf(value):
                        value = 0.0
                # Đảm bảo không có NaN/Inf trong kết quả (kiểm tra lại sau tất cả xử lý)
                if isinstance(value, (float, np.floating)):
                    try:
                        if math.isnan(value) or math.isinf(value):
                            value = 0.0
                    except (TypeError, ValueError):
                        value = 0.0
            except Exception:
                # Nếu có lỗi khi xử lý, đặt giá trị mặc định
                if k in ["lat", "lon", "avg_cost", "rating", "review_count", "duration_min", "nn_cos", "ce_score"]:
                    value = 0.0
                else:
                    value = None
            result[k] = value
    return result


def safe_dist(lat_a, lon_a, la, lo):
    """
    Khoảng cách an toàn: nếu thiếu toạ độ hoặc (0,0) thì không phạt (trả 0).
    """
    try:
        if la is None or lo is None:
            return 0.0
        la, lo = float(la), float(lo)
        if la == 0.0 and lo == 0.0:
            return 0.0
        if lat_a is None or lon_a is None:
            return 0.0
        return haversine(float(lat_a), float(lon_a), la, lo)
    except Exception:
        return 0.0


# Map city "lỏng" để người dùng gõ biến thể vẫn khớp
CITY_MAP = {
    # Đà Nẵng
    "dn": "da nang",
    "danang": "da nang",
    "đà nẵng": "da nang",
    "da nang": "da nang",
    # Hội An
    "hoian": "hoi an",
    "hội an": "hoi an",
    "hoi an": "hoi an",
    # Huế
    "hue": "hue",
    "huế": "hue",
}


class CrossEncoderReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        print(f"Loading Cross-encoder: {model_name}")
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.eval()
            print("[OK] Cross-encoder loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load cross-encoder: {e}")
            raise
        
    def rerank(self, query: str, documents: List[str], top_k: int = 50) -> List[float]:
        """Rerank documents based on query and return scores"""
        if not documents:
            return []
            
        try:
            # Tạo pairs query-document - FIX: đúng format cho BGE reranker
            pairs = []
            for doc in documents:
                # Format đúng cho BGE reranker v2: sử dụng template
                paired_text = f"Query: {query} Document: {doc}"
                pairs.append(paired_text)
            
            # Tokenize - FIX: chỉ 1 tham số max_length
            with torch.no_grad():
                inputs = self.tokenizer(pairs, padding=True, truncation=True, 
                                      return_tensors="pt", max_length=512)  # [OK] CHỈ 1 MAX_LENGTH
                outputs = self.model(**inputs)
                
                # FIX: Xử lý output cho BGE reranker
                # BGE reranker trả về logits trực tiếp
                scores = outputs.logits.squeeze().cpu().numpy()
                
                # Xử lý các trường hợp shape khác nhau
                if scores.ndim == 0:  # Scalar
                    scores = np.array([scores] * len(documents))
                elif scores.ndim == 1 and len(scores) == 1:  # Single element array
                    scores = np.array([scores[0]] * len(documents))
                elif len(scores) != len(documents):  # Shape không khớp
                    scores = np.ones(len(documents)) * 0.5
                
                # Chuẩn hóa scores về range [0, 1]
                if len(scores) > 0:
                    min_score = scores.min()
                    max_score = scores.max()
                    if max_score > min_score:
                        scores = (scores - min_score) / (max_score - min_score)
                    else:
                        scores = np.ones_like(scores) * 0.5  # Fallback
                
            print(f"Rerank scores range: {scores.min():.3f} - {scores.max():.3f}")
            return scores.tolist()
            
        except Exception as e:
            print(f"Reranking error: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: return decreasing scores
            return [max(0.1, 1.0 - (i * 0.1)) for i in range(len(documents))]


class Recommender:
    def __init__(
        self,
        csv_path: str = "data/itinerary_dataset.csv",
        model_name: str = "intfloat/multilingual-e5-base",
        embeds_path: str = "models/nn_embeds.npy",
        rerank_model: str = "BAAI/bge-reranker-v2-m3"
    ):
        # ƯU TIÊN CSV SẠCH; FALLBACK CSV GỐC
        try:
            self.df = pd.read_csv("data/itinerary_dataset.clean.csv")
            print("[OK] Loaded cleaned CSV dataset")
        except Exception:
            try:
                self.df = pd.read_csv("data/places.csv")
                print("[OK] Loaded places CSV dataset")
            except Exception:
                self.df = load_dataset(csv_path)
                print("[OK] Loaded original dataset")

        # Clean data - replace NaN values và convert numpy types
        self.df = self.df.fillna('')
        for col in self.df.columns:
            if self.df[col].dtype == np.int64:
                self.df[col] = self.df[col].astype('int64')
            elif self.df[col].dtype == np.float64:
                self.df[col] = self.df[col].astype('float64')

        # Đồng bộ index 0..N-1 cho khớp embeddings
        self.df = self.df.reset_index(drop=True)

        # Load Bi-encoder model
        print("Loading Bi-encoder model...")
        self.model = SentenceTransformer(model_name)
        
        # Load precomputed embeddings
        try:
            self.embeddings = np.load(embeds_path)
            print(f"Loaded embeddings: {self.embeddings.shape}")
        except FileNotFoundError:
            print("Warning: Precomputed embeddings not found. Please run build_nn.py first.")
            self.embeddings = None

        # Load Cross-encoder reranker
        try:
            self.reranker = CrossEncoderReranker(rerank_model)
            print("[OK] Cross-encoder reranker loaded")
        except Exception as e:
            print(f"[WARN] Cannot load cross-encoder: {e}. Continuing without reranking.")
            self.reranker = None

        # Chuẩn hoá closed_set
        def _norm_closed(v):
            if isinstance(v, set):
                return v
            if isinstance(v, (list, tuple)):
                out = set()
                for x in v:
                    try:
                        if pd.notna(x):
                            out.add(int(x))
                    except Exception:
                        pass
                return out
            if isinstance(v, str):
                return parse_closed_days(v)
            return set()

        if "closed_set" in self.df.columns:
            self.df["closed_set"] = self.df["closed_set"].apply(_norm_closed)
        else:
            self.df["closed_set"] = [set()] * len(self.df)

        print(f"Loaded {len(self.df)} places")

    def _clean_for_json(self, obj):
        """
        Clean data for JSON serialization
        Replace NaN, inf, numpy types với Python native types
        """
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            if np.isnan(obj) or np.isinf(obj):
                return 0.0
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_for_json(item) for item in obj]
        elif isinstance(obj, set):
            return list(obj)
        elif pd.isna(obj):
            return ""
        elif hasattr(obj, 'item'):  # For pandas scalar values
            try:
                return obj.item()
            except:
                return obj
        else:
            return obj

    def encode_query(self, query: str) -> np.ndarray:
        """Encode query to normalized embedding"""
        return self.model.encode([query], normalize_embeddings=True)[0]

    def calculate_nn_cos(self, query_embedding: np.ndarray, place_indices: List[int] = None) -> np.ndarray:
        """Calculate cosine similarity between query and places"""
        if self.embeddings is None:
            raise ValueError("Embeddings not loaded. Please run build_nn.py first.")
            
        max_index = self.embeddings.shape[0] - 1  # Max valid index
            
        if place_indices is None:
            targets = self.embeddings
        else:
            # Filter indices to ensure they're within bounds
            valid_indices = [idx for idx in place_indices if 0 <= idx <= max_index]
            if len(valid_indices) == 0:
                # Nếu không có index hợp lệ, return empty array
                return np.array([])
            targets = self.embeddings[valid_indices]
        
        # Cosine similarity = dot product for normalized vectors
        similarities = np.dot(targets, query_embedding)
        return similarities

    def diversity_filter(self, items: List[Dict], threshold: float = 0.90) -> List[Dict]:
        """Filter items to ensure diversity using cosine similarity"""
        if not items or len(items) <= 1:
            return items
        
        selected = [items[0]]
        selected_embeddings = [self.embeddings[items[0]['index']]]
        
        for item in items[1:]:
            item_embedding = self.embeddings[item['index']]
            
            # Check similarity with all selected items
            max_similarity = max(np.dot(item_embedding, sel_emb) for sel_emb in selected_embeddings)
            
            if max_similarity < threshold:
                selected.append(item)
                selected_embeddings.append(item_embedding)
                
        return selected

    def _city_filter(self, df: pd.DataFrame, city: str | None) -> pd.DataFrame:
        if not city:
            return df
        key = strip_accents(city).lower().strip()
        key = CITY_MAP.get(key, key)
        mask = df["city"].astype(str).str.lower().apply(strip_accents).str.contains(key, na=False)
        sub = df[mask]
        return sub if not sub.empty else df  # fallback

    def filter_places(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply hard filters"""
        filtered_df = df.copy()
        
        # Budget filter  
        if 'budget' in filters and filters['budget'] is not None:
            budget = filters['budget']
            filtered_df = filtered_df[filtered_df['avg_cost'] <= budget]
            
        # Time filter
        if 'current_time' in filters and filters['current_time'] is not None:
            # Có thể implement time-based filtering ở đây
            pass
            
        # Distance filter
        if 'max_distance' in filters and filters['max_distance'] is not None:
            # Có thể implement distance filtering ở đây
            pass
            
        return filtered_df

    def _create_document_text(self, place_data: pd.Series) -> str:
        """Tạo text document từ place data cho cross-encoder"""
        # SỬA: Sử dụng description thay vì desc để phù hợp dataset mới
        text_parts = [
            place_data.get('name', ''),
            place_data.get('description', place_data.get('desc', '')),  # Ưu tiên description
            place_data.get('category', ''),
            place_data.get('tags', ''),
            place_data.get('best_time', '')
        ]
        return " ".join([str(part) for part in text_parts if pd.notna(part) and str(part) != 'nan'])

    def recommend(self, query: str, city: str = "Da Nang", top_k: int = 200, 
                  filters: Dict[str, Any] = None, diversity_threshold: float = 0.90,
                  use_reranking: bool = True) -> List[Dict]:
        """Main recommendation function với cross-encoder reranking"""
        import time
        start_time = time.time()
        
        if filters is None:
            filters = {}
        
        # Filter by city first - case-insensitive và flexible matching
        if city:
            # Thử exact match trước
            city_df = self.df[self.df['city'].str.lower().str.strip() == city.lower().strip()]
        
            # Nếu không có, thử contains
            if len(city_df) == 0:
                city_df = self.df[self.df['city'].str.lower().str.contains(city.lower().strip(), na=False)]
            
            # Nếu vẫn không có, thử strip accents
            if len(city_df) == 0:
                from .etl import strip_accents
                city_key = strip_accents(city.lower().strip())
                city_df = self.df[self.df['city'].str.lower().apply(strip_accents).str.contains(city_key, na=False)]
        else:
            city_df = self.df.copy()
        
        print(f"📊 DEBUG: Sau khi filter city '{city}': {len(city_df)} places")
        
        if len(city_df) == 0:
            print(f"[WARN] Không có places cho city '{city}', thử không filter city...")
            city_df = self.df.copy()
        if len(city_df) == 0:
            return []
        
        # Apply hard filters
        filtered_df = self.filter_places(city_df, filters)
        filtered_indices = filtered_df.index.tolist()
        
        if len(filtered_indices) == 0:
            return []
        
        # Encode query
        query_embedding = self.encode_query(query)
        
        # Calculate similarities only for filtered items
        # Đảm bảo filtered_indices không vượt quá bounds của embeddings
        max_embedding_index = self.embeddings.shape[0] - 1 if self.embeddings is not None else len(self.df) - 1
        valid_filtered_indices = [idx for idx in filtered_indices if 0 <= idx <= max_embedding_index]
        
        if len(valid_filtered_indices) == 0:
            print(f"[WARN] WARNING: No valid indices after filtering. Max embedding index: {max_embedding_index}, Filtered indices range: {min(filtered_indices) if filtered_indices else 'N/A'} - {max(filtered_indices) if filtered_indices else 'N/A'}")
            return []
        
        similarities = self.calculate_nn_cos(query_embedding, valid_filtered_indices)
        
        # Keyword boosting: Tăng điểm cho các địa điểm có từ khóa trong query
        query_lower = query.lower()
        query_keywords = query_lower.split()
        
        # Create initial results với nn_cos
        results = []
        for idx, similarity in zip(valid_filtered_indices, similarities):
            place = self.df.iloc[idx]
            place_name = str(place.get('name', '')).lower()
            place_desc = str(place.get('description', place.get('desc', ''))).lower()
            place_category = str(place.get('category', '')).lower()
            place_tags = str(place.get('tags', '')).lower()
            
            # Boost similarity nếu có keyword match
            boosted_similarity = similarity
            for keyword in query_keywords:
                if len(keyword) >= 3:  # Chỉ boost keywords có ít nhất 3 ký tự
                    if keyword in place_name:
                        boosted_similarity += 0.3  # Boost cao nếu match trong tên
                    elif keyword in place_desc:
                        boosted_similarity += 0.15  # Boost trung bình nếu match trong mô tả
                    elif keyword in place_category or keyword in place_tags:
                        boosted_similarity += 0.1  # Boost nhẹ nếu match trong category/tags
            
            result_item = {
                'index': int(idx),  # Ensure integer
                'id': self._clean_for_json(place['id']),
                'name': self._clean_for_json(place['name']),
                'nn_cos': float(boosted_similarity),  # Sử dụng boosted similarity
                'category': self._clean_for_json(place.get('category', '')),
                'avg_cost': self._clean_for_json(place.get('avg_cost', 0)),
                'rating': self._clean_for_json(place.get('rating', 0)),
                'opening_hours': f"{place.get('open_time', '')} - {place.get('close_time', '')}".strip(' -'),
                'address': self._clean_for_json(place.get('address', '')),
                'lat': self._clean_for_json(place.get('lat')),
                'lon': self._clean_for_json(place.get('lon')),
                'open_min': self._clean_for_json(place.get('open_min')),
                'close_min': self._clean_for_json(place.get('close_min')),
                'closed_set': list(place.get('closed_set', set()))  # Convert set to list
            }
            results.append(result_item)
        
        # Sort by nn_cos (descending)
        results.sort(key=lambda x: x['nn_cos'], reverse=True)
        
        # Apply diversity filter
        if diversity_threshold < 1.0:
            results = self.diversity_filter(results[:top_k*2], diversity_threshold)
        else:
            results = results[:top_k]
        
        # Cross-encoder reranking
        if use_reranking and self.reranker and len(results) > 1:
            rerank_start = time.time()
            
            # Lấy top-K candidates cho reranking (giữ hiệu năng)
            rerank_candidates = min(50, len(results))
            candidates_for_rerank = results[:rerank_candidates]
            
            # Tạo documents cho reranking
            documents = []
            candidate_indices = []
            for candidate in candidates_for_rerank:
                place_data = self.df.iloc[candidate['index']]
                doc_text = self._create_document_text(place_data)
                documents.append(doc_text)
                candidate_indices.append(candidate['index'])
            
            # Rerank với cross-encoder
            try:
                ce_scores = self.reranker.rerank(query, documents, top_k=rerank_candidates)
                
                # Cập nhật ce_score cho các candidates
                for i, score in enumerate(ce_scores):
                    if i < len(candidates_for_rerank):
                        candidates_for_rerank[i]['ce_score'] = float(score)
                
                # Sort lại theo ce_score (descending)
                candidates_for_rerank.sort(key=lambda x: x.get('ce_score', 0), reverse=True)
                
                # Kết hợp kết quả: reranked candidates + remaining results
                reranked_indices = {candidate['index'] for candidate in candidates_for_rerank}
                remaining_results = [r for r in results[rerank_candidates:] if r['index'] not in reranked_indices]
                
                final_results = candidates_for_rerank + remaining_results
                
                print(f"Reranking took {time.time() - rerank_start:.2f}s")
                
            except Exception as e:
                print(f"Reranking failed: {e}. Using bi-encoder results.")
                final_results = results[:top_k]
        else:
            final_results = results[:top_k]
            # Gán ce_score = nn_cos nếu không có reranking
            for result in final_results:
                result['ce_score'] = result['nn_cos']
        
        # Đảm bảo final score là ce_score và clean all data
        cleaned_results = []
        for result in final_results:
            cleaned_result = {}
            for key, value in result.items():
                cleaned_result[key] = self._clean_for_json(value)
            cleaned_result['final_score'] = cleaned_result.get('ce_score', cleaned_result.get('nn_cos', 0))
            cleaned_results.append(cleaned_result)
        
        print(f"Recommendation took {time.time() - start_time:.2f}s, found {len(cleaned_results)} results")
        return cleaned_results

    def _optimize_slot_selection(self, candidates: pd.DataFrame, minute_of_day: int, 
                               weekday: int, per_day_budget: float, anchor_lat: float, 
                               anchor_lon: float, category: str) -> pd.DataFrame:
        """
        Tối ưu chọn item cho từng slot dựa trên multiple factors
        """
        if candidates.empty:
            return candidates
            
        optimized = candidates.copy()
        
        # 1. Opening hours priority
        optimized['time_match'] = optimized.apply(
            lambda r: 1.0 if within_open(r, minute_of_day, weekday) else 0.3, axis=1
        )
        
        # 2. Budget optimization - ưu tiên các item rẻ hơn hoặc gần budget nhất
        if category == 'hotel':
            target_cost = per_day_budget * 0.5  # 50% ngân sách cho khách sạn (giảm từ 55%)
            # Ưu tiên các hotel rẻ hơn hoặc gần target_cost nhất, nhưng không vượt quá
            optimized['budget_match'] = optimized.apply(
                lambda r: 1.0 if r['avg_cost'] <= target_cost 
                else max(0, 1 - (r['avg_cost'] - target_cost) / max(1, target_cost)),
                axis=1
            )
        elif category == 'food':
            target_cost = per_day_budget * 0.25  # 25% ngân sách cho food
            optimized['budget_match'] = optimized.apply(
                lambda r: 1.0 if r['avg_cost'] <= target_cost 
                else max(0, 1 - (r['avg_cost'] - target_cost) / max(1, target_cost)),
                axis=1
            )
        elif category == 'event':
            target_cost = per_day_budget * 0.15  # 15% ngân sách cho event
            optimized['budget_match'] = optimized.apply(
                lambda r: 1.0 if r['avg_cost'] <= target_cost 
                else max(0, 1 - (r['avg_cost'] - target_cost) / max(1, target_cost)),
                axis=1
            )
        else:
            optimized['budget_match'] = 1.0  # Sightseeing thường miễn phí
        
        # 3. Distance penalty
        optimized['distance'] = optimized.apply(
            lambda r: safe_dist(anchor_lat, anchor_lon, r['lat'], r['lon']), axis=1
        )
        max_dist = optimized['distance'].max() if not optimized['distance'].isna().all() else 1
        optimized['distance_score'] = 1 - (optimized['distance'] / max(1, max_dist))
        
        # 4. Kết hợp tất cả factors - tăng trọng số budget_match
        optimized['slot_score'] = (
            0.5 * optimized.get('ce_score', optimized.get('nn_cos', 0)) +
            0.15 * optimized['time_match'] +
            0.25 * optimized['budget_match'] +  # Tăng trọng số budget
            0.1 * optimized['distance_score']
        )
        
        return optimized.sort_values('slot_score', ascending=False)

    def itinerary(self, query_text: str, days: int, budget_total: int, city: str | None = None, travel_companion: str = "solo", exclude_place_ids: list = None, exclude_food_ids: list = None, llm_context: dict = None, google_info: dict = None, variation: int = 0):
        """Itinerary function với cross-encoder reranking và slot optimization
        
        Args:
            query_text: Query text từ user
            days: Số ngày
            budget_total: Tổng ngân sách
            city: Thành phố
            travel_companion: Loại bạn đồng hành (solo, couple, family, friends, group)
            exclude_place_ids: Danh sách place IDs cần loại bỏ (để tạo lịch trình khác)
            llm_context: Context từ LLM (preferences, main_location, etc.)
            google_info: Thông tin từ Google Search về địa điểm chính
            variation: Số variation để tạo lịch trình khác nhau (0 = lần đầu, 1+ = các lần sau)
        """
        if exclude_place_ids is None:
            exclude_place_ids = []
        if exclude_food_ids is None:
            exclude_food_ids = []
        if llm_context is None:
            llm_context = {}
        if google_info is None:
            google_info = {}
        
        # Tính số người và số phòng từ travel_companion
        def get_num_people(companion: str) -> int:
            """Tính số người từ travel_companion"""
            if companion.startswith("group_"):
                try:
                    return int(companion.split("_")[1])
                except:
                    return 2
            companion_map = {
                "solo": 1,
                "couple": 2,
                "family": 4,  # Giả sử gia đình = 2 người lớn + 2 trẻ em
                "friends": 2,  # Giả sử nhóm bạn = 2 người
                "group": 3,  # Mặc định nhóm = 3 người
            }
            return companion_map.get(companion, 1)
        
        def calculate_rooms(num_people: int) -> int:
            """
            Tính số phòng cần thiết
            Logic: 1 phòng = 2 người (phòng đôi), làm tròn lên
            - 1 người = 1 phòng (phòng đơn)
            - 2 người = 1 phòng (phòng đôi)
            - 3 người = 2 phòng (1 phòng đôi + 1 phòng đơn)
            - 4 người = 2 phòng (2 phòng đôi)
            """
            import math
            return max(1, math.ceil(num_people / 2))
        
        num_people = get_num_people(travel_companion)
        num_rooms = calculate_rooms(num_people)
        
        print(f"👥 Số người: {num_people}, Số phòng: {num_rooms}")
        
        # Get recommendations với reranking
        per_day_budget = max(0, budget_total) // max(1, days)
        
        # Thử filter budget, nhưng nếu không có kết quả thì bỏ filter
        recommendations = self.recommend(
            query=query_text,
            city=city,
            top_k=200,  # Tăng top_k để có nhiều lựa chọn hơn
            filters={'budget': per_day_budget * 2} if budget_total else None,  # Cho phép budget gấp đôi để có nhiều lựa chọn
            diversity_threshold=0.85,  # Giảm threshold để có nhiều đa dạng hơn
            use_reranking=True  # Bật reranking
        )
        
        print(f"📊 DEBUG: Nhận được {len(recommendations)} recommendations")
        
        # Nếu không có recommendations, thử lại không filter budget
        if not recommendations:
            print("[WARN] Không có recommendations với budget filter, thử lại không filter...")
            recommendations = self.recommend(
                query=query_text,
                city=city,
                top_k=200,
                filters=None,  # Bỏ filter budget
                diversity_threshold=0.85,
                use_reranking=True
            )
            print(f"📊 DEBUG: Sau khi bỏ filter, nhận được {len(recommendations)} recommendations")
        
        if not recommendations:
            print("[ERROR] Vẫn không có recommendations, trả về itinerary rỗng")
            return {
                "days": days,
                "per_day_budget": int(per_day_budget),
                "total_cost_estimate": 0,
                "itinerary": [],
            }
        
        # Convert recommendations back to dataframe và clean data
        rec_data = []
        for rec in recommendations:
            cleaned_rec = {k: self._clean_for_json(v) for k, v in rec.items()}
            # Đảm bảo có id (nếu không có thì tạo từ index)
            if 'id' not in cleaned_rec or not cleaned_rec.get('id'):
                cleaned_rec['id'] = cleaned_rec.get('index', len(rec_data))
            rec_data.append(cleaned_rec)
        
        rec_df = pd.DataFrame(rec_data)
        
        # Exclude các places đã dùng nếu có
        if exclude_place_ids:
            print(f"🚫 Excluding {len(exclude_place_ids)} places đã dùng: {exclude_place_ids[:5]}...")
            # Convert exclude_place_ids sang cùng format với id trong rec_df
            exclude_ids_set = set(str(pid) for pid in exclude_place_ids)
            original_count = len(rec_df)
            rec_df = rec_df[~rec_df['id'].astype(str).isin(exclude_ids_set)].copy()
            print(f"📊 Sau khi exclude: {len(rec_df)}/{original_count} places còn lại")
        
        # Sử dụng LLM context để filter/boost places liên quan đến main_location
        if llm_context and llm_context.get("main_location"):
            main_location = llm_context["main_location"].lower()
            print(f"🎯 LLM xác định địa điểm chính: {main_location}")
            
            # Tìm places liên quan đến main_location (trong name, desc, tags, address)
            location_keywords = {
                "bà nà": ["bà nà", "ba na", "bana hills", "sun world ba na"],
                "ngũ hành sơn": ["ngũ hành sơn", "marble mountains", "ngu hanh son"],
                "sơn trà": ["sơn trà", "son tra", "bán đảo sơn trà"],
                "cầu rồng": ["cầu rồng", "dragon bridge"],
                "cầu vàng": ["cầu vàng", "golden bridge"],
                "mỹ khê": ["mỹ khê", "my khe", "bãi biển mỹ khê"],
                "non nước": ["non nước", "bãi biển non nước"]
            }
            
            # Tìm keywords phù hợp
            relevant_keywords = []
            for loc, keywords in location_keywords.items():
                if loc in main_location or any(kw in main_location for kw in keywords):
                    relevant_keywords = keywords
                    break
            
            if relevant_keywords:
                # Boost places liên quan đến main_location
                def location_relevance_score(row):
                    score = 0
                    name = str(row.get("name", "")).lower()
                    desc = str(row.get("desc", "")).lower()
                    tags = str(row.get("tags", "")).lower()
                    address = str(row.get("address", "")).lower()
                    
                    for keyword in relevant_keywords:
                        if keyword in name:
                            score += 3
                        if keyword in desc:
                            score += 2
                        if keyword in tags:
                            score += 2
                        if keyword in address:
                            score += 1
                    
                    return score
                
                rec_df["location_relevance"] = rec_df.apply(location_relevance_score, axis=1)
                # Sắp xếp theo relevance (cao nhất trước)
                rec_df = rec_df.sort_values("location_relevance", ascending=False).reset_index(drop=True)
                print(f"[OK] Đã boost {len(rec_df[rec_df['location_relevance'] > 0])} places liên quan đến {main_location}")
        
        # Debug: Kiểm tra categories có trong recommendations
        if "category" in rec_df.columns:
            category_counts = rec_df["category"].value_counts()
            print(f"📊 DEBUG Categories trong recommendations: {category_counts.to_dict()}")
        else:
            print("[WARN] WARNING: Không có cột 'category' trong recommendations!")
            # Thêm category mặc định nếu thiếu
            rec_df["category"] = "sightseeing"
        
        # Đảm bảo có các cột cần thiết
        required_cols = ['id', 'name', 'category', 'avg_cost', 'lat', 'lon', 'rating']
        for col in required_cols:
            if col not in rec_df.columns:
                if col == 'id':
                    rec_df[col] = range(len(rec_df))
                elif col in ['avg_cost', 'rating']:
                    rec_df[col] = 0.0
                elif col in ['lat', 'lon']:
                    rec_df[col] = 0.0
                else:
                    rec_df[col] = ''
                print(f"[WARN] WARNING: Thêm cột '{col}' mặc định")
        
        # Convert lat và lon sang numeric để đảm bảo tính toán đúng
        if "lat" in rec_df.columns:
            rec_df["lat"] = pd.to_numeric(rec_df["lat"], errors='coerce').fillna(0.0)
        if "lon" in rec_df.columns:
            rec_df["lon"] = pd.to_numeric(rec_df["lon"], errors='coerce').fillna(0.0)
        
        # Đảm bảo avg_cost là numeric
        if "avg_cost" in rec_df.columns:
            rec_df["avg_cost"] = pd.to_numeric(rec_df["avg_cost"], errors='coerce').fillna(0.0)
        
        # Phân loại theo category - case-insensitive và flexible matching
        # Thử nhiều cách viết category, bao gồm cả beach → sightseeing
        category_map = {
            'sightseeing': ['sightseeing', 'sight-seeing', 'attraction', 'attractions', 'tourist', 'landmark', 'beach', 'beaches'],
            'food': ['food', 'restaurant', 'restaurants', 'dining', 'cafe', 'café', 'bar', 'bistro', 'eating'],
            'hotel': ['hotel', 'hotels', 'accommodation', 'lodging', 'resort', 'hostel', 'stay'],
            'event': ['event', 'events', 'entertainment', 'nightlife', 'activity', 'activities']
        }
        
        def match_category(cat, target_categories):
            if pd.isna(cat) or not cat:
                return False
            cat_lower = str(cat).lower().strip()
            return cat_lower in target_categories
        
        # Phân loại categories
        S = rec_df[rec_df["category"].apply(lambda x: match_category(x, category_map['sightseeing']))].copy()
        F = rec_df[rec_df["category"].apply(lambda x: match_category(x, category_map['food']))].copy()
        H = rec_df[rec_df["category"].apply(lambda x: match_category(x, category_map['hotel']))].copy()
        E = rec_df[rec_df["category"].apply(lambda x: match_category(x, category_map['event']))].copy()
        
        print(f"📊 DEBUG: S={len(S)}, F={len(F)}, H={len(H)}, E={len(E)}")
        
        # Nếu không có đủ category, thử dùng tất cả recommendations cho sightseeing
        if S.empty and not rec_df.empty:
            print("[WARN] Không có sightseeing, dùng tất cả recommendations...")
            S = rec_df.copy()
        
        # Nếu không có food/hotel/event, tạo fallback từ sightseeing hoặc tất cả
        if F.empty and not rec_df.empty:
            print("[WARN] Không có food, sẽ dùng sightseeing làm fallback...")
            # Có thể dùng sightseeing places như restaurants nếu có tags phù hợp
            F = rec_df[rec_df["tags"].astype(str).str.contains("restaurant|cafe|food|dining", case=False, na=False)].copy()
            if F.empty:
                F = rec_df.copy()  # Fallback: dùng tất cả nếu không có
                
        if H.empty and not rec_df.empty:
            print("[WARN] Không có hotel, sẽ dùng sightseeing làm fallback...")
            # Có thể dùng sightseeing places như resorts nếu có tags phù hợp
            if "tags" in rec_df.columns:
                H = rec_df[rec_df["tags"].astype(str).str.contains("hotel|resort|accommodation|stay", case=False, na=False)].copy()
            else:
                # Nếu không có cột tags, tìm theo category hoặc name
                H = rec_df[rec_df["category"].astype(str).str.contains("hotel|resort|accommodation", case=False, na=False)].copy()
            if H.empty:
                H = rec_df.copy()  # Fallback: dùng tất cả nếu không có
                
        if E.empty and not rec_df.empty:
            print("[WARN] Không có event, sẽ dùng sightseeing làm fallback...")
            # Có thể dùng sightseeing places như events nếu có tags phù hợp
            if "tags" in rec_df.columns:
                E = rec_df[rec_df["tags"].astype(str).str.contains("event|entertainment|nightlife|activity", case=False, na=False)].copy()
            else:
                # Nếu không có cột tags, tìm theo category hoặc name
                E = rec_df[rec_df["category"].astype(str).str.contains("event|entertainment", case=False, na=False)].copy()
            if E.empty:
                E = rec_df.copy()  # Fallback: dùng tất cả nếu không có

        per_day_budget = max(0, budget_total) // max(1, days)
        used = set()

        # Tâm toạ độ hợp lệ - Convert sang numeric và loại bỏ giá trị không hợp lệ
        try:
            # Convert lat và lon sang numeric, loại bỏ các giá trị không hợp lệ
            df_copy = self.df.copy()
            df_copy["lat"] = pd.to_numeric(df_copy["lat"], errors='coerce')
            df_copy["lon"] = pd.to_numeric(df_copy["lon"], errors='coerce')
            
            # Lọc các giá trị hợp lệ (không NaN, không 0, trong khoảng hợp lý)
            df_valid = df_copy[
                (df_copy["lat"].notna()) & 
                (df_copy["lon"].notna()) & 
                (df_copy["lat"] != 0.0) & 
                (df_copy["lon"] != 0.0) &
                (df_copy["lat"].between(-90, 90)) &  # Latitude hợp lệ
                (df_copy["lon"].between(-180, 180))  # Longitude hợp lệ
            ]
            
            if not df_valid.empty:
                center_lat = float(df_valid["lat"].median())
                center_lon = float(df_valid["lon"].median())
            else:
                center_lat, center_lon = 16.0471, 108.2068
        except Exception as e:
            # Fallback nếu có lỗi
            print(f"[WARN] Warning: Error calculating center coordinates: {e}")
            center_lat, center_lon = 16.0471, 108.2068

        # RNG seed theo query + variation để tạo lịch trình khác nhau
        base_seed = (abs(hash(query_text)) % (2**32 - 1)) or 42
        seed = (base_seed + variation * 1000 + abs(hash(str(exclude_place_ids))) % 1000) % (2**32 - 1)
        rng = np.random.default_rng(seed)
        print(f"🎲 RNG Seed: {seed} (base: {base_seed}, variation: {variation})")

        def pick(item):
            """Helper function để trả về item hoặc None"""
            return item if item else None

        def pick_topk_weighted(df_sorted: pd.DataFrame, k=3, score_col="slot_score", shuffle_top_k=True):
            if df_sorted is None or df_sorted.empty:
                return None
            # Tăng k để có nhiều lựa chọn hơn, đặc biệt khi có variation
            expanded_k = k + variation * 2
            sub = df_sorted.head(max(1, min(expanded_k, len(df_sorted))))
            
            # Shuffle top k candidates để tạo sự đa dạng (đặc biệt khi có variation)
            if shuffle_top_k and variation > 0:
                sub = sub.sample(frac=1, random_state=seed).reset_index(drop=True)
            
            sc = sub[score_col].fillna(0).to_numpy(dtype=float)
            
            # Loại bỏ NaN và Inf
            sc = np.nan_to_num(sc, nan=0.0, posinf=0.0, neginf=0.0)
            
            # Normalize scores
            sc = np.maximum(sc - sc.min() + 1e-6, 1e-6)
            
            # Kiểm tra và xử lý edge cases
            if np.any(np.isnan(sc)) or np.any(np.isinf(sc)) or np.sum(sc) == 0:
                sc = np.ones_like(sc)
            
            # Tính probabilities và normalize để đảm bảo tổng = 1
            sc_sum = np.sum(sc)
            if sc_sum == 0 or np.isnan(sc_sum) or np.isinf(sc_sum):
                probs = np.ones_like(sc) / len(sc)  # Uniform distribution
            else:
                probs = sc / sc_sum
            
            # Đảm bảo probabilities sum to 1 (fix floating point precision)
            probs = probs / np.sum(probs)
            
            # Kiểm tra lại để đảm bảo không có NaN hoặc Inf
            if np.any(np.isnan(probs)) or np.any(np.isinf(probs)):
                probs = np.ones_like(probs) / len(probs)
            
            idx = rng.choice(len(sub), p=probs)
            return sub.iloc[idx].to_dict()

        # Helper function để convert giá trị an toàn
        def safe_float(value, default=0):
            try:
                if value is None:
                    return default
                val = float(value)
                if np.isnan(val) or np.isinf(val):
                    return default
                return max(0, val)  # Đảm bảo không âm
            except (ValueError, TypeError):
                return default

        plan = []
        # Dùng chung used set cho tất cả các ngày (tránh trùng lặp)
        # NHƯNG cho phép dùng lại hotel nếu cần (vì có thể ở cùng 1 hotel nhiều ngày)
        used = set()
        used_hotels = set()  # Track hotels riêng để có thể dùng lại nếu cần
        # Khởi tạo used_food với exclude_food_ids nếu có (từ alternative itinerary)
        used_food = set(exclude_food_ids) if exclude_food_ids else set()  # Track food places đã dùng để tránh ăn cùng chỗ nhiều lần
        used_sightseeing = set()  # Track sightseeing places đã dùng
        
        if exclude_food_ids:
            print(f"🚫 Đã nhận exclude_food_ids: {exclude_food_ids}, khởi tạo used_food với {len(exclude_food_ids)} food places")
        
        # Helper function để kiểm tra khoảng cách địa lý giữa 2 places
        def is_too_far(place1, place2, max_distance_km=50):
            """Kiểm tra xem 2 places có quá xa nhau không (mặc định >50km)"""
            try:
                lat1 = safe_float(place1.get("lat"), 0)
                lon1 = safe_float(place1.get("lon"), 0)
                lat2 = safe_float(place2.get("lat"), 0)
                lon2 = safe_float(place2.get("lon"), 0)
                
                # Nếu thiếu tọa độ, không thể kiểm tra
                if lat1 == 0 or lon1 == 0 or lat2 == 0 or lon2 == 0:
                    return False
                
                distance = haversine(lat1, lon1, lat2, lon2)
                return distance > max_distance_km
            except:
                return False
        
        # Helper function để kiểm tra place có trùng với places đã chọn trong ngày không
        def is_duplicate_in_day(place, day_places):
            """Kiểm tra xem place có trùng với places đã chọn trong ngày không"""
            place_id = place.get("id")
            place_name = str(place.get("name", "")).lower()
            
            for existing_place in day_places:
                if existing_place.get("id") == place_id:
                    return True
                # Kiểm tra tên tương tự (fuzzy matching)
                existing_name = str(existing_place.get("name", "")).lower()
                if place_name and existing_name:
                    # Nếu tên giống nhau > 80%, coi như trùng
                    from rapidfuzz import fuzz
                    similarity = fuzz.ratio(place_name, existing_name)
                    if similarity > 80:
                        return True
            return False
        
        for d in range(days):
            wd = d % 7
            remaining_budget = per_day_budget  # Budget còn lại trong ngày

            # ===== Hotel selection với budget optimization =====
            hotel = None
            if not H.empty:
                # Cho phép dùng lại hotel nếu đã dùng ở ngày trước (ở cùng 1 hotel nhiều ngày)
                # Nhưng ưu tiên hotel mới
                hotel_candidates_new = H[~H["id"].isin(used_hotels)].copy()
                hotel_candidates_all = H.copy()  # Bao gồm cả hotel đã dùng
                
                # Ưu tiên hotel mới, nhưng nếu không có thì dùng lại hotel cũ
                hotel_candidates = hotel_candidates_new if not hotel_candidates_new.empty else hotel_candidates_all
                
                if not hotel_candidates.empty:
                    # Lọc hotel theo budget: không vượt quá 50% budget
                    max_hotel_budget = per_day_budget * 0.5
                    hotel_candidates_filtered = hotel_candidates[
                        pd.to_numeric(hotel_candidates['avg_cost'], errors='coerce').fillna(float('inf')) <= max_hotel_budget
                    ]
                    
                    # Nếu không có hotel trong budget, thử tăng lên 70% hoặc lấy hotel rẻ nhất
                    if hotel_candidates_filtered.empty:
                        print(f"[WARN] Không có hotel trong budget {max_hotel_budget:,.0f}, thử tăng lên 70%...")
                        max_hotel_budget = per_day_budget * 0.7
                        hotel_candidates_filtered = hotel_candidates[
                            pd.to_numeric(hotel_candidates['avg_cost'], errors='coerce').fillna(float('inf')) <= max_hotel_budget
                        ]
                    
                    # Nếu vẫn không có, lấy hotel rẻ nhất (không filter budget)
                    if hotel_candidates_filtered.empty:
                        print(f"[WARN] Vẫn không có hotel, lấy hotel rẻ nhất...")
                        hotel_candidates_filtered = hotel_candidates.sort_values('avg_cost', ascending=True).head(10)
                    
                    if not hotel_candidates_filtered.empty:
                        optimized_hotels = self._optimize_slot_selection(
                            hotel_candidates_filtered, 
                            minute_of_day=14 * 60,  # Check-in time
                            weekday=wd,
                            per_day_budget=per_day_budget,
                            anchor_lat=center_lat,
                            anchor_lon=center_lon,
                            category='hotel'
                        )
                        # Tăng k khi có variation để có nhiều lựa chọn hơn
                        hotel_k = 3 + variation
                        hotel = pick_topk_weighted(optimized_hotels, k=hotel_k, score_col="slot_score", shuffle_top_k=variation > 0)
                        if hotel:
                            hotel_cost = safe_float(hotel.get("avg_cost"), 0)
                            remaining_budget -= hotel_cost
                            print(f"[OK] Chọn hotel: {hotel.get('name', 'N/A')} - {hotel_cost:,.0f} VND")
                
            if hotel:
                used.add(hotel["id"])
                used_hotels.add(hotel["id"])  # Track riêng cho hotel
            else:
                print(f"[WARN] Ngày {d+1}: Không tìm được hotel phù hợp")
                # Debug: kiểm tra có hotel nào trong database không
                if not H.empty:
                    print(f"   Có {len(H)} hotels trong database")
                    print(f"   Budget/ngày: {per_day_budget:,.0f} VND")
                    print(f"   Hotels đã dùng: {len(used_hotels)}")
                    if len(used_hotels) > 0:
                        print(f"   Có thể đã dùng hết hotel phù hợp, thử dùng lại hotel từ ngày trước...")
                        # Thử dùng lại hotel từ ngày trước
                        if len(plan) > 0 and plan[-1].get("hotel"):
                            previous_hotel = plan[-1]["hotel"]
                            if previous_hotel:
                                hotel = previous_hotel
                                print(f"   [OK] Dùng lại hotel từ ngày trước: {hotel.get('name', 'N/A')}")

            # ===== Morning (09:00) với time optimization =====
            # Lấy lat/lon từ hotel một cách an toàn
            if hotel:
                try:
                    hotel_lat = float(hotel.get("lat", 0)) if hotel.get("lat") not in [None, "", 0] else center_lat
                    hotel_lon = float(hotel.get("lon", 0)) if hotel.get("lon") not in [None, "", 0] else center_lon
                    # Kiểm tra giá trị hợp lệ
                    if not (-90 <= hotel_lat <= 90) or not (-180 <= hotel_lon <= 180):
                        hotel_lat, hotel_lon = center_lat, center_lon
                    anchor_lat, anchor_lon = hotel_lat, hotel_lon
                except (ValueError, TypeError):
                    anchor_lat, anchor_lon = center_lat, center_lon
            else:
                anchor_lat, anchor_lon = center_lat, center_lon
            morning_time = 9 * 60
            
            morning = None
            day_places = []  # Track places đã chọn trong ngày để kiểm tra trùng lặp
            
            if not S.empty:
                # Ưu tiên sightseeing places chưa dùng trong các ngày trước
                morning_candidates = S[~S["id"].isin(used_sightseeing)].copy()
                # Nếu đã dùng hết, mới cho phép dùng lại
                if morning_candidates.empty:
                    print(f"[WARN] Ngày {d+1} Sáng: Đã dùng hết sightseeing places mới, cho phép dùng lại...")
                    morning_candidates = S[~S["id"].isin(used)].copy()
                if not morning_candidates.empty:
                    optimized_morning = self._optimize_slot_selection(
                        morning_candidates,
                        minute_of_day=morning_time,
                        weekday=wd,
                        per_day_budget=per_day_budget,
                        anchor_lat=anchor_lat,
                        anchor_lon=anchor_lon,
                        category='sightseeing'
                    )
                    # Shuffle để tạo sự đa dạng khi có variation
                    if variation > 0 and len(optimized_morning) > 1:
                        optimized_morning = optimized_morning.sample(frac=1, random_state=seed).reset_index(drop=True)
                    
                    # Chọn place không trùng và không quá xa
                    # Tăng số lượng candidates để xem xét khi có variation
                    max_candidates = min(10 + variation * 2, len(optimized_morning))
                    for idx in range(max_candidates):
                        candidate = optimized_morning.iloc[idx].to_dict()
                        if not is_duplicate_in_day(candidate, day_places):
                            morning = candidate
                            break
                
            if morning:
                used.add(morning["id"])
                used_sightseeing.add(morning["id"])  # Track sightseeing places đã dùng
                day_places.append(morning)

            # ===== Lunch (12:00) với time optimization =====
            lunch_time = 12 * 60
            anchor_lat = (morning or {}).get("lat", anchor_lat)
            anchor_lon = (morning or {}).get("lon", anchor_lon)
            
            lunch = None
            if not F.empty:
                # Đảm bảo ID là int để so sánh chính xác
                F_ids = pd.to_numeric(F["id"], errors='coerce').astype('Int64')
                # Convert used_food to set of ints - đảm bảo type consistency
                used_food_ids = set()
                for x in used_food:
                    try:
                        if pd.notna(x):
                            used_food_ids.add(int(x))
                    except (ValueError, TypeError):
                        pass
                
                print(f"🔍 Ngày {d+1} Trưa: used_food={used_food}, used_food_ids={used_food_ids}")
                
                # Loại bỏ food places đã dùng trong các ngày trước (tránh ăn cùng chỗ)
                lunch_candidates = F[~F_ids.isin(used_food_ids)].copy()
                
                # KIỂM TRA AN TOÀN: Đảm bảo không có candidate nào có ID trong used_food_ids
                if not lunch_candidates.empty and used_food_ids:
                    lunch_candidates_ids = pd.to_numeric(lunch_candidates["id"], errors='coerce').astype('Int64')
                    still_has_used = lunch_candidates_ids.isin(used_food_ids).any()
                    if still_has_used:
                        print(f"  [WARN] CẢNH BÁO: Vẫn còn candidates có ID trong used_food_ids! Đang loại bỏ thủ công...")
                        lunch_candidates = lunch_candidates[~lunch_candidates_ids.isin(used_food_ids)].copy()
                
                print(f"🔍 Ngày {d+1} Trưa: Tổng food places: {len(F)}, Đã loại bỏ {len(used_food_ids)} food places đã dùng (IDs: {sorted(used_food_ids)}), còn {len(lunch_candidates)} candidates")
                
                # Debug: Hiển thị các food places đã bị loại bỏ
                if used_food_ids:
                    excluded_places = F[F_ids.isin(used_food_ids)]
                    if not excluded_places.empty:
                        excluded_names = excluded_places['name'].tolist()
                        print(f"  🚫 Đã loại bỏ {len(excluded_names)} places: {excluded_names[:5]}{'...' if len(excluded_names) > 5 else ''}")
                # Nếu đã dùng hết, mới cho phép dùng lại (nhưng ưu tiên places chưa dùng)
                if lunch_candidates.empty:
                    print(f"[WARN] Ngày {d+1} Trưa: Đã dùng hết food places mới, cho phép dùng lại...")
                    lunch_candidates = F[~F["id"].isin(used)].copy()
                if not lunch_candidates.empty:
                    # Lọc food theo budget (tối đa 50% budget - tăng từ 25% để có nhiều lựa chọn hơn)
                    max_food_budget = per_day_budget * 0.5
                    lunch_candidates_filtered = lunch_candidates[
                        pd.to_numeric(lunch_candidates['avg_cost'], errors='coerce').fillna(float('inf')) <= max_food_budget
                    ]
                    
                    # Nếu không có trong budget, thử tăng lên 100% hoặc bỏ filter
                    if lunch_candidates_filtered.empty:
                        print(f"[WARN] Ngày {d+1} Trưa: Không có food trong budget {max_food_budget:,.0f}, thử bỏ filter...")
                        lunch_candidates_filtered = lunch_candidates
                    
                    if not lunch_candidates_filtered.empty:
                        optimized_lunch = self._optimize_slot_selection(
                            lunch_candidates_filtered,
                            minute_of_day=lunch_time,
                            weekday=wd,
                            per_day_budget=per_day_budget,
                            anchor_lat=anchor_lat,
                            anchor_lon=anchor_lon,
                            category='food'
                        )
                        # LUÔN shuffle để tạo sự đa dạng giữa các ngày (không chỉ khi variation > 0)
                        if len(optimized_lunch) > 1:
                            # Dùng seed khác nhau cho mỗi ngày để đảm bảo khác nhau
                            # Thêm hash của used_food_ids để đảm bảo seed khác nhau khi đã dùng places khác nhau
                            used_food_hash = hash(frozenset(used_food_ids)) if used_food_ids else 0
                            shuffle_seed = (seed + d * 1000 + used_food_hash) % (2**31 - 1)  # Đảm bảo seed hợp lệ
                            optimized_lunch = optimized_lunch.sample(frac=1, random_state=shuffle_seed).reset_index(drop=True)
                            print(f"🔍 Ngày {d+1} Trưa: Shuffled với seed={shuffle_seed}, used_food_hash={used_food_hash}")
                        
                        # Tăng số lượng candidates được xem xét - xem xét nhiều hơn để có sự đa dạng
                        max_candidates = min(20 + variation * 5, len(optimized_lunch))
                        print(f"🔍 Ngày {d+1} Trưa: Đang xem xét {max_candidates}/{len(optimized_lunch)} candidates, used_food_ids={sorted(used_food_ids)}")
                        candidates_checked = 0
                        for idx in range(max_candidates):
                            candidate = optimized_lunch.iloc[idx].to_dict()
                            candidate_id = int(pd.to_numeric(candidate.get("id"), errors='coerce')) if pd.notna(candidate.get("id")) else None
                            candidate_name = candidate.get("name", "N/A")
                            candidates_checked += 1
                            
                            # Kiểm tra không trùng trong ngày VÀ không trùng với food places đã dùng
                            if candidate_id is not None and candidate_id in used_food_ids:
                                print(f"  [SKIP] [{idx+1}/{max_candidates}] Bỏ qua {candidate_name} (id={candidate_id}) - đã dùng")
                                continue
                            if not is_duplicate_in_day(candidate, day_places):
                                lunch = candidate
                                print(f"  [OK] [{idx+1}/{max_candidates}] Chọn {candidate_name} (id={candidate_id}) sau {candidates_checked} lần kiểm tra")
                                break
                            else:
                                print(f"  [SKIP] [{idx+1}/{max_candidates}] Bỏ qua {candidate_name} (id={candidate_id}) - trùng trong ngày")
                        
                        if not lunch:
                            print(f"  [WARN] Không tìm được lunch sau {candidates_checked} lần kiểm tra")
                        if lunch:
                            lunch_cost = safe_float(lunch.get("avg_cost"), 0)
                            remaining_budget -= lunch_cost
                else:
                    # Nếu đã dùng hết, thử dùng lại (nhưng vẫn ưu tiên places chưa dùng)
                    print(f"[WARN] Ngày {d+1} Trưa: Đã dùng hết candidates mới, thử dùng lại...")
                    F_ids = pd.to_numeric(F["id"], errors='coerce').astype('Int64')
                    used_ids = {int(x) for x in used if pd.notna(x)}
                    lunch_candidates = F[~F_ids.isin(used_ids)].copy()
                    if lunch_candidates.empty:
                        lunch_candidates = F.copy()
                    if not lunch_candidates.empty:
                        optimized_lunch = self._optimize_slot_selection(
                            lunch_candidates,
                            minute_of_day=lunch_time,
                            weekday=wd,
                            per_day_budget=per_day_budget,
                            anchor_lat=anchor_lat,
                            anchor_lon=anchor_lon,
                            category='food'
                        )
                        # LUÔN shuffle để tạo sự đa dạng giữa các ngày
                        if len(optimized_lunch) > 1:
                            shuffle_seed = seed + d * 100 + 1  # Thêm d (day index) vào seed
                            optimized_lunch = optimized_lunch.sample(frac=1, random_state=shuffle_seed).reset_index(drop=True)
                        
                        # Tăng số lượng candidates được xem xét
                        max_candidates = min(15 + variation * 3, len(optimized_lunch))
                        print(f"🔍 Ngày {d+1} Trưa (fallback): Đang xem xét {max_candidates} candidates, used_food_ids={used_food_ids}")
                        for idx in range(max_candidates):
                            candidate = optimized_lunch.iloc[idx].to_dict()
                            candidate_id = int(pd.to_numeric(candidate.get("id"), errors='coerce')) if pd.notna(candidate.get("id")) else None
                            candidate_name = candidate.get("name", "N/A")
                            # Kiểm tra không trùng trong ngày VÀ không trùng với food places đã dùng
                            if candidate_id is not None and candidate_id in used_food_ids:
                                print(f"  [SKIP] Bỏ qua {candidate_name} (id={candidate_id}) - đã dùng")
                                continue
                            if not is_duplicate_in_day(candidate, day_places):
                                lunch = candidate
                                print(f"  [OK] Chọn {candidate_name} (id={candidate_id})")
                                break
                            else:
                                print(f"  [SKIP] Bỏ qua {candidate_name} (id={candidate_id}) - trùng trong ngày")
                
            if lunch:
                lunch_id = int(pd.to_numeric(lunch.get("id"), errors='coerce')) if pd.notna(lunch.get("id")) else None
                if lunch_id is not None:
                    used.add(lunch_id)
                    used_food.add(lunch_id)  # Track food places đã dùng
                    day_places.append(lunch)
                    # Verify that it was added correctly
                    if lunch_id in used_food:
                        print(f"[OK] Ngày {d+1} Trưa: {lunch.get('name', 'N/A')} (id={lunch_id}) - Đã thêm vào used_food thành công. used_food hiện tại: {sorted(used_food)}")
                    else:
                        print(f"[ERROR] Ngày {d+1} Trưa: LỖI! Không thể thêm {lunch_id} vào used_food!")
                else:
                    print(f"[WARN] Ngày {d+1} Trưa: Không thể lấy ID từ lunch: {lunch.get('id')}")
            else:
                print(f"[WARN] Ngày {d+1} Trưa: Không tìm được")

            # ===== Afternoon (15:00) với time optimization =====
            afternoon_time = 15 * 60
            anchor_lat = (lunch or {}).get("lat", anchor_lat)
            anchor_lon = (lunch or {}).get("lon", anchor_lon)
            
            afternoon = None
            if not S.empty:
                # Ưu tiên sightseeing places chưa dùng trong các ngày trước
                afternoon_candidates = S[~S["id"].isin(used_sightseeing)].copy()
                # Nếu đã dùng hết, mới cho phép dùng lại
                if afternoon_candidates.empty:
                    print(f"[WARN] Ngày {d+1} Chiều: Đã dùng hết sightseeing places mới, cho phép dùng lại...")
                    afternoon_candidates = S[~S["id"].isin(used)].copy()
                if not afternoon_candidates.empty:
                    optimized_afternoon = self._optimize_slot_selection(
                        afternoon_candidates,
                        minute_of_day=afternoon_time,
                        weekday=wd,
                        per_day_budget=per_day_budget,
                        anchor_lat=anchor_lat,
                        anchor_lon=anchor_lon,
                        category='sightseeing'
                    )
                    # Shuffle để tạo sự đa dạng khi có variation
                    if variation > 0 and len(optimized_afternoon) > 1:
                        optimized_afternoon = optimized_afternoon.sample(frac=1, random_state=seed + 2).reset_index(drop=True)
                    
                    # Chọn place không trùng và không quá xa với places đã chọn trong ngày
                    max_candidates = min(10 + variation * 2, len(optimized_afternoon))
                    for idx in range(max_candidates):
                        candidate = optimized_afternoon.iloc[idx].to_dict()
                        # Kiểm tra trùng lặp
                        if is_duplicate_in_day(candidate, day_places):
                            continue
                        # Kiểm tra khoảng cách với morning place (nếu có) - không quá 50km
                        if morning and is_too_far(candidate, morning, max_distance_km=50):
                            print(f"[WARN] {candidate.get('name')} quá xa {morning.get('name')}, bỏ qua...")
                            continue
                        afternoon = candidate
                        break
                else:
                    # Nếu đã dùng hết, thử dùng lại
                    print(f"[WARN] Ngày {d+1} Chiều: Đã dùng hết candidates, thử dùng lại...")
                    afternoon_candidates = S.copy()
                if not afternoon_candidates.empty and not afternoon:
                    optimized_afternoon = self._optimize_slot_selection(
                        afternoon_candidates,
                        minute_of_day=afternoon_time,
                        weekday=wd,
                        per_day_budget=per_day_budget,
                        anchor_lat=anchor_lat,
                        anchor_lon=anchor_lon,
                        category='sightseeing'
                    )
                    # Shuffle để tạo sự đa dạng khi có variation
                    if variation > 0 and len(optimized_afternoon) > 1:
                        optimized_afternoon = optimized_afternoon.sample(frac=1, random_state=seed + 2).reset_index(drop=True)
                    
                    # Chọn place không trùng
                    max_candidates = min(10 + variation * 2, len(optimized_afternoon))
                    for idx in range(max_candidates):
                        candidate = optimized_afternoon.iloc[idx].to_dict()
                        if not is_duplicate_in_day(candidate, day_places):
                            afternoon = candidate
                            break
                
            if afternoon:
                used.add(afternoon["id"])
                used_sightseeing.add(afternoon["id"])  # Track sightseeing places đã dùng
                day_places.append(afternoon)
                print(f"[OK] Ngày {d+1} Chiều: {afternoon.get('name', 'N/A')}")
            else:
                print(f"[WARN] Ngày {d+1} Chiều: Không tìm được")

            # ===== Evening (19:00) với time optimization =====
            evening_time = 19 * 60
            anchor_lat_e = (afternoon or {}).get("lat", anchor_lat)
            anchor_lon_e = (afternoon or {}).get("lon", anchor_lon)
            
            evening = None
            if not E.empty:
                evening_candidates = E[~E["id"].isin(used)].copy()
                if not evening_candidates.empty:
                    # Lọc evening theo budget (tối đa 15% budget)
                    max_evening_budget = per_day_budget * 0.15
                    evening_candidates = evening_candidates[
                        pd.to_numeric(evening_candidates['avg_cost'], errors='coerce').fillna(float('inf')) <= max_evening_budget
                    ]
                    
                    if not evening_candidates.empty:
                        optimized_evening = self._optimize_slot_selection(
                            evening_candidates,
                            minute_of_day=evening_time,
                            weekday=wd,
                            per_day_budget=per_day_budget,
                            anchor_lat=anchor_lat_e,
                            anchor_lon=anchor_lon_e,
                            category='event'
                        )
                        evening = pick_topk_weighted(optimized_evening, k=3, score_col="slot_score")
                        if evening:
                            evening_cost = safe_float(evening.get("avg_cost"), 0)
                            remaining_budget -= evening_cost
                
            if evening:
                used.add(evening["id"])

            # Kiểm tra và điều chỉnh nếu vượt budget
            def adjust_if_over_budget(place_dict, max_cost):
                """Điều chỉnh place nếu vượt quá max_cost - tìm option rẻ hơn"""
                if not place_dict:
                    return place_dict
                place_cost = safe_float(place_dict.get("avg_cost"), 0)
                if place_cost > max_cost:
                    # Tìm option rẻ hơn trong cùng category
                    category = place_dict.get("category", "")
                    place_id = place_dict.get("id")
                    
                    if category == "hotel" and not H.empty:
                        cheaper = H[(H["id"] != place_id) & 
                                   (pd.to_numeric(H['avg_cost'], errors='coerce') <= max_cost)]
                        if not cheaper.empty:
                            cheaper = cheaper.sort_values('avg_cost', ascending=True)
                            return cheaper.iloc[0].to_dict()
                    elif category == "food" and not F.empty:
                        cheaper = F[(F["id"] != place_id) & 
                                   (pd.to_numeric(F['avg_cost'], errors='coerce') <= max_cost)]
                        if not cheaper.empty:
                            cheaper = cheaper.sort_values('avg_cost', ascending=True)
                            return cheaper.iloc[0].to_dict()
                    elif category == "event" and not E.empty:
                        cheaper = E[(E["id"] != place_id) & 
                                   (pd.to_numeric(E['avg_cost'], errors='coerce') <= max_cost)]
                        if not cheaper.empty:
                            cheaper = cheaper.sort_values('avg_cost', ascending=True)
                            return cheaper.iloc[0].to_dict()
                    
                    # Nếu không tìm được option rẻ hơn, giữ nguyên nhưng log warning
                    print(f"[WARN] Không tìm được option rẻ hơn cho {category}, giữ nguyên")
                
                return place_dict
            
            # Tính chi phí từng phần và điều chỉnh nếu vượt budget
            # Lấy từ dict đã được pick (đã clean)
            morning_picked = pick(morning) if morning else None
            lunch_picked = pick(lunch) if lunch else None
            afternoon_picked = pick(afternoon) if afternoon else None
            evening_picked = pick(evening) if evening else None
            hotel_picked = pick(hotel) if hotel else None
            
            # Tính tổng chi phí tạm thời
            temp_total = (
                safe_float((morning_picked or {}).get("avg_cost"), 0) +
                safe_float((lunch_picked or {}).get("avg_cost"), 0) +
                safe_float((afternoon_picked or {}).get("avg_cost"), 0) +
                safe_float((evening_picked or {}).get("avg_cost"), 0) +
                safe_float((hotel_picked or {}).get("avg_cost"), 0)
            )
            
            # Nếu vượt budget, điều chỉnh các item có chi phí cao nhất
            if temp_total > per_day_budget:
                print(f"[WARN] Chi phí tạm thời ({temp_total:,.0f}) vượt budget ({per_day_budget:,.0f}), đang điều chỉnh...")
                
                # Sắp xếp theo chi phí và điều chỉnh từ cao xuống thấp
                items = [
                    ("hotel", hotel_picked, per_day_budget * 0.6),
                    ("lunch", lunch_picked, per_day_budget * 0.3),
                    ("evening", evening_picked, per_day_budget * 0.2),
                ]
                
                for item_name, item_dict, max_cost in items:
                    if item_dict:
                        adjusted = adjust_if_over_budget(item_dict, max_cost)
                        if item_name == "hotel":
                            hotel_picked = adjusted
                        elif item_name == "lunch":
                            lunch_picked = adjusted
                        elif item_name == "evening":
                            evening_picked = adjusted
                        
                        # Tính lại tổng
                        temp_total = (
                            safe_float((morning_picked or {}).get("avg_cost"), 0) +
                            safe_float((lunch_picked or {}).get("avg_cost"), 0) +
                            safe_float((afternoon_picked or {}).get("avg_cost"), 0) +
                            safe_float((evening_picked or {}).get("avg_cost"), 0) +
                            safe_float((hotel_picked or {}).get("avg_cost"), 0)
                        )
                        
                        if temp_total <= per_day_budget:
                            break
            
            morning_cost = safe_float((morning_picked or {}).get("avg_cost"), 0)
            lunch_cost = safe_float((lunch_picked or {}).get("avg_cost"), 0)
            afternoon_cost = safe_float((afternoon_picked or {}).get("avg_cost"), 0)
            evening_cost = safe_float((evening_picked or {}).get("avg_cost"), 0)
            hotel_cost = safe_float((hotel_picked or {}).get("avg_cost"), 0)
            
            day_cost = morning_cost + lunch_cost + afternoon_cost + evening_cost + hotel_cost
            
            # Đảm bảo không vượt quá budget (cho phép sai số nhỏ do làm tròn)
            if day_cost > per_day_budget * 1.01:  # Cho phép 1% sai số
                print(f"[WARN] Chi phí ngày {d+1} ({day_cost:,.0f}) vượt budget ({per_day_budget:,.0f}), đang điều chỉnh...")
                
                # Tính tỷ lệ cần giảm
                reduction_ratio = per_day_budget / day_cost
                
                # Điều chỉnh các item có chi phí (không điều chỉnh sightseeing miễn phí)
                if hotel_picked and hotel_cost > 0:
                    new_hotel_cost = hotel_cost * reduction_ratio
                    # Tìm hotel rẻ hơn
                    cheaper_hotels = H[(H["id"] != hotel_picked.get("id")) & 
                                      (pd.to_numeric(H['avg_cost'], errors='coerce') <= new_hotel_cost)]
                    if not cheaper_hotels.empty:
                        cheaper_hotels = cheaper_hotels.sort_values('avg_cost', ascending=True)
                        hotel_picked = cheaper_hotels.iloc[0].to_dict()
                        hotel_cost = safe_float(hotel_picked.get("avg_cost"), 0)
                
                if lunch_picked and lunch_cost > 0:
                    new_lunch_cost = lunch_cost * reduction_ratio
                    cheaper_food = F[(F["id"] != lunch_picked.get("id")) & 
                                    (pd.to_numeric(F['avg_cost'], errors='coerce') <= new_lunch_cost)]
                    if not cheaper_food.empty:
                        cheaper_food = cheaper_food.sort_values('avg_cost', ascending=True)
                        lunch_picked = cheaper_food.iloc[0].to_dict()
                        lunch_cost = safe_float(lunch_picked.get("avg_cost"), 0)
                
                if evening_picked and evening_cost > 0:
                    new_evening_cost = evening_cost * reduction_ratio
                    cheaper_events = E[(E["id"] != evening_picked.get("id")) & 
                                      (pd.to_numeric(E['avg_cost'], errors='coerce') <= new_evening_cost)]
                    if not cheaper_events.empty:
                        cheaper_events = cheaper_events.sort_values('avg_cost', ascending=True)
                        evening_picked = cheaper_events.iloc[0].to_dict()
                        evening_cost = safe_float(evening_picked.get("avg_cost"), 0)
                
                # Tính lại tổng
                day_cost = morning_cost + lunch_cost + afternoon_cost + evening_cost + hotel_cost
                
                if day_cost > per_day_budget:
                    print(f"[WARN] Vẫn vượt budget sau điều chỉnh, cắt giảm thêm...")
                    # Cắt giảm thêm bằng cách loại bỏ evening nếu có
                    if evening_picked and evening_cost > 0:
                        evening_picked = None
                        evening_cost = 0
                        day_cost = morning_cost + lunch_cost + afternoon_cost + hotel_cost
            
            # Debug log CHI TIẾT cho mọi trường hợp để phát hiện lỗi
            print(f"📊 DEBUG Chi phí ngày {d+1}: Sáng={morning_cost:,.0f}, Trưa={lunch_cost:,.0f}, Chiều={afternoon_cost:,.0f}, Tối={evening_cost:,.0f}, KS={hotel_cost:,.0f}, Tổng={day_cost:,.0f}, Budget={per_day_budget:,.0f}")
            
            # Kiểm tra nếu có giá trị bất thường
            if day_cost > per_day_budget * 1.01 or day_cost < 0:
                print(f"[WARN] CẢNH BÁO: Chi phí ngày {d+1} vẫn bất thường sau điều chỉnh!")
                if morning_picked:
                    print(f"   Sáng raw: {morning_picked.get('avg_cost')}")
                if lunch_picked:
                    print(f"   Trưa raw: {lunch_picked.get('avg_cost')}")
                if afternoon_picked:
                    print(f"   Chiều raw: {afternoon_picked.get('avg_cost')}")
                if evening_picked:
                    print(f"   Tối raw: {evening_picked.get('avg_cost')}")
                if hotel_picked:
                    print(f"   KS raw: {hotel_picked.get('avg_cost')}")

            # Tính tiền khách sạn theo số phòng và số ngày
            hotel_cost_per_room_per_day = hotel_cost if hotel_picked else 0
            # Tính chi phí hotel cho 1 ngày (theo số phòng)
            hotel_cost_per_day = hotel_cost_per_room_per_day * num_rooms
            # Tổng tiền khách sạn cho tất cả ngày
            hotel_total_all_days = hotel_cost_per_room_per_day * num_rooms * days
            
            # day_cost chỉ tính chi phí 1 ngày (bao gồm hotel cho 1 ngày)
            # Nhưng cần điều chỉnh: thay vì chỉ tính hotel_cost (1 phòng), tính hotel_cost_per_day (số phòng)
            day_cost_adjusted = (
                morning_cost + 
                lunch_cost + 
                afternoon_cost + 
                evening_cost + 
                hotel_cost_per_day  # Tính theo số phòng
            )
            
            plan.append({
                "day": d + 1,
                "morning": morning_picked,
                "lunch": lunch_picked,
                "afternoon": afternoon_picked,
                "evening": evening_picked,
                "hotel": hotel_picked,
                "day_cost_estimate": int(day_cost_adjusted),  # Chi phí 1 ngày (đã tính số phòng)
                "over_budget": day_cost_adjusted > per_day_budget * 1.01,  # Chỉ đánh dấu nếu thực sự vượt quá 1%
                # Thông tin khách sạn chi tiết
                "hotel_info": {
                    "cost_per_room_per_day": int(hotel_cost_per_room_per_day),
                    "num_rooms": num_rooms,
                    "num_people": num_people,
                    "total_hotel_cost": int(hotel_total_all_days) if d == 0 else None  # Chỉ tính 1 lần cho ngày đầu
                } if hotel_picked else None
            })

        # Tính tổng chi phí: tổng các ngày (đã tính hotel cho mỗi ngày) - hotel trùng lặp + hotel tổng
        # Vì mỗi ngày đã tính hotel_cost_per_day, nên tổng = sum(day_cost) - hotel_cost_per_day * (days-1) + hotel_total_all_days
        # Hoặc đơn giản hơn: sum(day_cost) - (hotel_cost_per_day * days) + hotel_total_all_days
        # Nhưng thực ra nếu mỗi ngày đã tính đúng hotel_cost_per_day thì tổng đã đúng rồi
        
        # Tính tổng tiền khách sạn cho toàn bộ chuyến đi
        hotel_total_all_days = 0
        hotel_cost_per_day = 0
        if plan and plan[0].get("hotel_info"):
            hotel_info = plan[0]["hotel_info"]
            cost_per_room = hotel_info.get("cost_per_room_per_day", 0)
            num_rooms = hotel_info.get("num_rooms", 1)
            hotel_cost_per_day = cost_per_room * num_rooms
            hotel_total_all_days = cost_per_room * num_rooms * days
        
        # Tính tổng chi phí: tổng các ngày (mỗi ngày đã tính hotel cho 1 ngày)
        # Nhưng hotel thực tế chỉ trả 1 lần cho tất cả ngày, nên cần điều chỉnh
        total_day_costs = sum(x["day_cost_estimate"] for x in plan)
        # Trừ đi hotel đã tính trong các ngày (vì tính nhiều lần) và cộng lại tổng hotel
        total = total_day_costs - (hotel_cost_per_day * (days - 1)) if days > 1 else total_day_costs
        
        # Tính lại over_budget dựa trên total budget, không phải per_day_budget
        # Nếu tổng chi phí vượt quá total budget thì đánh dấu
        total_over_budget = total > budget_total * 1.01  # Cho phép vượt 1%
        
        # Cập nhật lại over_budget cho từng ngày dựa trên tổng budget
        # Nếu tổng không vượt budget, thì không đánh dấu ngày nào vượt
        if not total_over_budget:
            for day_plan in plan:
                day_plan["over_budget"] = False
        else:
            # Nếu tổng vượt budget, đánh dấu các ngày có chi phí cao
            avg_day_cost = total / days if days > 0 else 0
            for day_plan in plan:
                # Đánh dấu nếu ngày đó vượt quá mức trung bình + 10%
                day_plan["over_budget"] = day_plan["day_cost_estimate"] > avg_day_cost * 1.1
        
        # Clean toàn bộ result để đảm bảo không có NaN/Inf
        result = {
            "days": int(days),
            "per_day_budget": int(per_day_budget),
            "total_budget": int(budget_total),  # Thêm total_budget vào result
            "total_cost_estimate": int(total),
            "over_budget_total": total_over_budget,  # Thêm flag tổng vượt budget
            "itinerary": plan,
            "travel_info": {
                "num_people": num_people,
                "num_rooms": num_rooms,
                "travel_companion": travel_companion
            },
            "hotel_summary": {
                "cost_per_room_per_day": int(plan[0]["hotel_info"]["cost_per_room_per_day"]) if plan and plan[0].get("hotel_info") else 0,
                "num_rooms": num_rooms,
                "num_people": num_people,
                "total_days": days,
                "total_hotel_cost": int(hotel_total_all_days)
            } if plan and plan[0].get("hotel_info") else None
        }
        
        # Clean toàn bộ result để loại bỏ NaN/Inf
        return self._clean_for_json(result)


# Singleton instance
recommender = Recommender()