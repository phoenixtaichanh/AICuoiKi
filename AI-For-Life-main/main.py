from fastapi import FastAPI, Query, HTTPException, File, UploadFile, Form, Request, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import uvicorn
import numpy as np
import pandas as pd
import os
import shutil
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.recommender import recommender
from src.qa import qa_system  # Ngày 3: Q&A system
from src.query_extractor import QueryExtractor
from src.plan_guard import PlanGuard
from src.explain_ability import ExplainAbility
from src.google_search import init_google_search, google_search_instance
from src.llm_processor import init_llm_processor, llm_processor_instance
from src.user_manager import (
    ensure_user_file, find_user_by_username, find_user_by_email,
    find_user_by_id, add_user, verify_password, create_session,
    find_session_by_token, delete_session, cleanup_expired_sessions,
    update_user_last_login
)

# Vision QA initialization - Hỗ trợ cả Gemini (miễn phí) và OpenAI
vision_qa_instance = None
VISION_MODE = "inactive"  # gemini, openai, hoặc inactive

class CustomJSONEncoder:
    def encode(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            if np.isnan(obj) or np.isinf(obj):
                return 0.0
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return ""
        elif isinstance(obj, dict):
            return {k: self.encode(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.encode(item) for item in obj]
        else:
            return obj

custom_encoder = CustomJSONEncoder()

# Lifespan event handler để thay thế @app.on_event (deprecated)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager để khởi tạo và cleanup khi app start/stop"""
    # Startup
    await startup_event()
    yield
    # Shutdown (nếu cần cleanup)

app = FastAPI(
    title="AI Travel Assistant API - OpenAI Version",
    description="Hệ thống recommendation và Q&A cho du lịch Đà Nẵng - Sử dụng OpenAI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware để frontend có thể gọi API
# Phải thêm trước các middleware khác
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origins (có thể restrict trong production)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],  # Cho phép tất cả methods
    allow_headers=["*"],  # Cho phép tất cả headers
    expose_headers=["*"],  # Expose tất cả headers
    max_age=3600,  # Cache preflight requests
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Khởi tạo VisionQA với OpenAI khi app start
async def startup_event():
    """Khởi tạo các hệ thống khi app bắt đầu - OPENAI ONLY"""
    global vision_qa_instance, VISION_MODE
    
    try:
        print("=" * 60)
        print("🚀 KHỞI TẠO HỆ THỐNG")
        print("=" * 60)
        
        # Khởi tạo Google Search API
        print("\n🔍 Khởi tạo Google Search API...")
        init_google_search()
        
        # Khởi tạo LLM Processor
        print("\n🤖 Khởi tạo LLM Processor...")
        llm_provider = os.getenv("LLM_PROVIDER", "openai")
        llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        init_llm_processor(llm_provider, llm_model)
        
        print("\n" + "=" * 60)
        print("🚀 KHỞI TẠO VISION QA")
        print("=" * 60)
        
        # Chọn provider: ưu tiên HuggingFace (hoàn toàn miễn phí), sau đó Gemini, cuối cùng OpenAI
        vision_provider = os.getenv("VISION_PROVIDER", "huggingface").lower()
        
        # Thử khởi tạo HuggingFace trước (HOÀN TOÀN MIỄN PHÍ, không có rate limit nghiêm ngặt)
        if vision_provider in ["huggingface", "hf", "auto"]:
            hf_use_api = os.getenv("HF_USE_API", "true").lower() == "true"
            hf_api_token = os.getenv("HUGGINGFACE_API_TOKEN")
            hf_model = os.getenv("HF_VISION_MODEL", "Salesforce/blip-image-captioning-base")
            
            print(f"🔍 DEBUG: HF_USE_API = {hf_use_api}")
            print(f"🔍 DEBUG: HF_MODEL = {hf_model}")
            
            print("🔧 Đang khởi tạo Hugging Face Vision QA (HOÀN TOÀN MIỄN PHÍ)...")
            try:
                from src.vision_qa_huggingface import init_vision_qa
                vision_qa_instance = init_vision_qa(use_api=hf_use_api, api_token=hf_api_token, model=hf_model)
                
                if vision_qa_instance:
                    VISION_MODE = "huggingface"
                    print("🎉 HUGGING FACE VISION QA KHỞI TẠO THÀNH CÔNG! (HOÀN TOÀN MIỄN PHÍ)")
                    print(f"[OK] Model: {hf_model}")
                    print(f"[OK] Use API: {hf_use_api}")
                    print(f"[OK] Vision instance: {vision_qa_instance is not None}")
                else:
                    raise Exception("Không thể khởi tạo Hugging Face Vision QA")
                    
            except ImportError as e:
                print(f"[ERROR] Lỗi import module Hugging Face: {e}")
                print("💡 Hãy chạy: pip install transformers torch pillow")
                vision_qa_instance = None
                
            except Exception as e:
                print(f"[ERROR] Lỗi khởi tạo Hugging Face: {e}")
                vision_qa_instance = None
        
        # Fallback sang Gemini nếu HuggingFace không có hoặc fail
        if vision_qa_instance is None and vision_provider in ["gemini", "auto"]:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            gemini_model = os.getenv("GEMINI_VISION_MODEL", "gemini-2.0-flash-exp")
            
            print(f"🔍 DEBUG: GEMINI_API_KEY = {'[OK] Có' if gemini_api_key else '[ERROR] Không'}")
            print(f"🔍 DEBUG: GEMINI_MODEL = {gemini_model}")
            
            if gemini_api_key:
                print("🔧 Đang khởi tạo Gemini Vision QA (MIỄN PHÍ)...")
                try:
                    from src.gemini_vision_qa import GeminiVisionQA
                    vision_qa_instance = GeminiVisionQA(api_key=gemini_api_key, model=gemini_model)
                    
                    if vision_qa_instance:
                        VISION_MODE = "gemini"
                        print("🎉 GEMINI VISION QA KHỞI TẠO THÀNH CÔNG! (MIỄN PHÍ)")
                        print(f"[OK] Model: {gemini_model}")
                        print(f"[OK] Vision instance: {vision_qa_instance is not None}")
                    else:
                        raise Exception("Không thể khởi tạo Gemini Vision QA")
                        
                except ImportError as e:
                    print(f"[ERROR] Lỗi import module Gemini: {e}")
                    print("💡 Hãy chạy: pip install google-generativeai")
                    vision_qa_instance = None
                    
                except Exception as e:
                    print(f"[ERROR] Lỗi khởi tạo Gemini: {e}")
                    vision_qa_instance = None
            else:
                print("[WARN] Không có Gemini API key - sẽ thử OpenAI")
        
        # Fallback sang OpenAI nếu Gemini không có hoặc fail
        if vision_qa_instance is None and vision_provider in ["openai", "auto"]:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            openai_model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
            
            print(f"\n🔍 DEBUG: OPENAI_API_KEY = {'[OK] Có' if openai_api_key else '[ERROR] Không'}")
            print(f"🔍 DEBUG: OPENAI_MODEL = {openai_model}")
            
            if openai_api_key and openai_api_key.startswith('sk-'):
                print("🔧 Đang khởi tạo OpenAI Vision QA...")
                try:
                    from src.vision_qa_openai import init_vision_qa
                    vision_qa_instance = init_vision_qa(openai_api_key)
                    
                    if vision_qa_instance:
                        VISION_MODE = "openai"
                        print("🎉 OPENAI VISION QA KHỞI TẠO THÀNH CÔNG!")
                        print(f"[OK] Model: {openai_model}")
                        print(f"[OK] Vision instance: {vision_qa_instance is not None}")
                    else:
                        raise Exception("Không thể khởi tạo OpenAI Vision QA")
                        
                except ImportError as e:
                    print(f"[ERROR] Lỗi import module OpenAI: {e}")
                    print("💡 Hãy chạy: pip install openai")
                    vision_qa_instance = None
                    VISION_MODE = "inactive"
                    
                except Exception as e:
                    print(f"[ERROR] Lỗi khởi tạo OpenAI: {e}")
                    vision_qa_instance = None
                    VISION_MODE = "inactive"
            else:
                if vision_provider == "openai":
                    print("[ERROR] Không có OpenAI API key hợp lệ")
                    print("💡 Kiểm tra file .env: OPENAI_API_KEY phải bắt đầu bằng 'sk-'")
                vision_qa_instance = None
        
        if vision_qa_instance is None:
            VISION_MODE = "inactive"
            print("[WARN] CẢNH BÁO: Không có Vision QA provider nào hoạt động!")
            print("💡 Khuyến nghị: Sử dụng Hugging Face (HOÀN TOÀN MIỄN PHÍ)")
            print("💡   - Không cần API key (có thể dùng Inference API free)")
            print("💡   - Hoặc set HF_USE_API=false để dùng local model")
            print("💡   - Cài đặt: pip install transformers torch pillow")
            print("💡 Hoặc thêm GEMINI_API_KEY vào .env (có rate limit)")
            print("💡 Hoặc thêm OPENAI_API_KEY nếu muốn dùng OpenAI (trả phí)")
        
        # Tạo thư mục tạm cho file upload
        os.makedirs("temp_uploads", exist_ok=True)
        os.makedirs("test_images", exist_ok=True)
        print("[OK] Thư mục temp_uploads và test_images đã được tạo")
        
        print("=" * 60)
        print(f"🎯 TRẠNG THÁI CUỐI CÙNG:")
        print(f"   • Vision Mode: {VISION_MODE}")
        print(f"   • Vision QA Active: {vision_qa_instance is not None}")
        if VISION_MODE == "huggingface":
            print(f"   • Hugging Face Model: {os.getenv('HF_VISION_MODEL', 'Salesforce/blip-image-captioning-base')}")
            print(f"   • Use API: {os.getenv('HF_USE_API', 'true')}")
        elif VISION_MODE == "gemini":
            print(f"   • Gemini Model: {os.getenv('GEMINI_VISION_MODEL', 'gemini-2.0-flash-exp')}")
        elif VISION_MODE == "openai":
            print(f"   • OpenAI Model: {os.getenv('OPENAI_VISION_MODEL', 'gpt-4o-mini')}")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] LỖI NGHIÊM TRỌNG trong startup: {str(e)}")
        vision_qa_instance = None
        VISION_MODE = "inactive"

def route_query(query: str) -> str:
    """
    Phân luồng query tự động: Q&A hoặc itinerary
    """
    query_lower = query.lower()
    
    # Danh sách keywords cho Q&A
    qa_keywords = [
        'là gì', 'ở đâu', 'mấy giờ', 'giờ mở', 'giờ đóng', 
        'giá bao nhiêu', 'giá vé', 'địa chỉ', 'có gì', 
        'thông tin', 'giới thiệu', 'là ai', 'bao nhiêu tiền'
    ]
    
    # Nếu có Q&A keywords → route sang Q&A system
    if any(keyword in query_lower for keyword in qa_keywords):
        return "qa"
    else:
        # Ngược lại → itinerary recommendation
        return "itinerary"


@app.get("/")
async def root():
    """Serve the web UI directly at root (so the launcher can open just /)"""
    ui_path = os.path.join(os.path.dirname(__file__), "ui.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    # Fallback: health check JSON
    return {
        "message": "AI Travel Assistant API",
        "version": "1.0.0",
        "status": "running",
        "vision_qa_status": "active" if vision_qa_instance is not None else "inactive",
        "vision_mode": VISION_MODE,
        "docs": "/docs",
    }


@app.get("/api/info")
async def api_info():
    """Health check endpoint (JSON)"""
    return {
        "message": "AI Travel Assistant API",
        "version": "1.0.0",
        "status": "running",
        "vision_qa_status": "active" if vision_qa_instance is not None else "inactive",
        "vision_mode": VISION_MODE,
        "docs": "/docs",
    }


@app.get("/ui", response_class=HTMLResponse)
async def serve_ui():
    """Serve the web UI"""
    ui_path = os.path.join(os.path.dirname(__file__), "ui.html")
    
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        raise HTTPException(status_code=404, detail="UI file not found")


@app.get("/favicon.ico")
async def favicon():
    """Handle favicon request to avoid 404 errors"""
    return JSONResponse(content={}, status_code=204)  # No Content


@app.get("/itinerary")
async def get_itinerary(
    q: str = Query(..., description="Query tìm kiếm"),
    city: Optional[str] = Query(None, description="Thành phố"),
    days: Optional[int] = Query(None, description="Số ngày"),
    budget_total: Optional[int] = Query(None, description="Tổng ngân sách"),
    top_k: int = Query(20, description="Số kết quả trả về"),
    include_explanation: bool = Query(False, description="Bao gồm giải thích"),
    validate_plan: bool = Query(True, description="Validate itinerary"),
    exclude_place_ids: Optional[str] = Query(None, description="Danh sách place IDs cần loại bỏ (comma-separated)"),
    exclude_food_ids: Optional[str] = Query(None, description="Danh sách food place IDs cần loại bỏ (comma-separated)")
):
    """
    Itinerary endpoint - Trả về lịch trình du lịch theo ngày
    Tự động extract budget, days, city từ query nếu không được cung cấp
    """
    try:
        # Extract thông tin từ query nếu chưa có
        extracted = QueryExtractor.extract_all(q)
        
        # Sử dụng giá trị được cung cấp hoặc extracted hoặc default
        final_city = city or extracted['city']
        final_days = days or extracted['days']
        
        # Nếu user cung cấp budget_total trực tiếp, dùng nó
        # Nếu không, dùng budget từ extracted (đã được tính toán đúng theo budget_type)
        if budget_total:
            final_budget = budget_total
        else:
            final_budget = extracted.get('budget', 3000000)  # Total budget
        
        # Đảm bảo days và budget có giá trị hợp lệ
        if final_days is None or final_days <= 0:
            final_days = 1
        if final_budget is None or final_budget <= 0:
            final_budget = 3000000  # Default 3 triệu
        
        # Extract travel_companion và budget_type từ query
        travel_companion = extracted.get('travel_companion', 'solo')
        budget_type = extracted.get('extracted', {}).get('budget_type', 'total')
        
        # Debug log để kiểm tra giá trị
        print(f"📊 DEBUG Itinerary Input:")
        print(f"   Query: {q}")
        print(f"   Days: {final_days}")
        print(f"   Budget Type: {budget_type}")  # "per_day" hoặc "total"
        print(f"   Budget Total: {final_budget:,} VND")
        print(f"   Budget/ngày: {final_budget // final_days:,} VND")
        print(f"   City: {final_city}")
        print(f"   Travel Companion: {travel_companion}")
        
        # Parse exclude_place_ids nếu có
        exclude_ids = None
        if exclude_place_ids:
            try:
                exclude_ids = [int(x.strip()) for x in exclude_place_ids.split(',') if x.strip().isdigit()]
                print(f"🚫 Excluding place IDs: {exclude_ids}")
            except:
                exclude_ids = None
        
        # Tính variation dựa trên số places đã exclude (để tạo lịch trình khác nhau)
        # Variation càng cao, lịch trình càng khác nhau
        variation = len(exclude_ids) if exclude_ids else 0
        # Nếu có exclude_ids, tăng variation để đảm bảo lịch trình khác nhau
        if variation > 0:
            variation = variation * 2  # Tăng variation để tạo sự đa dạng hơn
        
        # Sử dụng LLM để hiểu context tốt hơn (ví dụ: "đi bà nà" nghĩa là tập trung ở khu vực Bà Nà)
        llm_context = None
        if llm_processor_instance and llm_processor_instance.enabled:
            try:
                print("🤖 Đang sử dụng LLM để phân tích query...")
                llm_result = llm_processor_instance.process_query(q, context={"city": final_city, "days": final_days})
                if llm_result.get("success"):
                    llm_context = {
                        "preferences": llm_result.get("preferences", []),
                        "intent": llm_result.get("intent", "itinerary"),
                        "main_location": llm_result.get("main_location"),  # Địa điểm chính (ví dụ: "bà nà")
                    }
                    print(f"[OK] LLM context: {llm_context}")
            except Exception as e:
                print(f"[WARN] LLM processing error: {e}")
        
        # Sử dụng Google Search để lấy thông tin về khoảng cách và thời gian di chuyển
        google_info = None
        if google_search_instance and google_search_instance.enabled:
            try:
                # Tìm kiếm thông tin về địa điểm chính nếu có
                if llm_context and llm_context.get("main_location"):
                    main_location = llm_context["main_location"]
                    print(f"🔍 Đang tìm kiếm thông tin về {main_location} từ Google...")
                    google_info = google_search_instance.search_place_info(main_location, final_city)
                    if google_info.get("success"):
                        print(f"[OK] Tìm thấy thông tin từ Google về {main_location}")
            except Exception as e:
                print(f"[WARN] Google Search error: {e}")
        
        # Parse exclude_food_ids từ query params
        exclude_food_ids_list = None
        if exclude_food_ids:  # exclude_food_ids là parameter của hàm
            try:
                exclude_food_ids_list = [int(x.strip()) for x in exclude_food_ids.split(',') if x.strip().isdigit()]
                print(f"🚫 Excluding food IDs: {exclude_food_ids_list}")
            except:
                exclude_food_ids_list = None
        
        # Gọi itinerary function để tạo lịch trình theo ngày
        result = recommender.itinerary(
            query_text=q,
            days=final_days,
            budget_total=final_budget,
            city=final_city,
            travel_companion=travel_companion,
            exclude_place_ids=exclude_ids,
            exclude_food_ids=exclude_food_ids_list,  # Thêm exclude_food_ids
            llm_context=llm_context,
            google_info=google_info,
            variation=variation
        )
        
        # Debug log kết quả
        print(f"📊 DEBUG Itinerary Output:")
        print(f"   Per day budget: {result.get('per_day_budget', 0):,} VND")
        print(f"   Total cost estimate: {result.get('total_cost_estimate', 0):,} VND")
        print(f"   Days: {result.get('days', 0)}")
        
        # Validate plan nếu được yêu cầu
        if validate_plan:
            try:
                validation = PlanGuard.validate_itinerary(result)
                result['validation'] = validation
            except Exception as e:
                print(f"[WARN] Warning: Plan validation failed: {e}")
                # Không fail nếu validation lỗi, chỉ log warning
        
        # Thêm explanation nếu được yêu cầu
        if include_explanation and result.get('itinerary'):
            try:
                explanation = ExplainAbility.explain_full_itinerary(result, q)
                result['explanation'] = explanation
            except Exception as e:
                print(f"[WARN] Warning: Explanation failed: {e}")
                # Không fail nếu explanation lỗi
        
        # Thêm thông tin extracted
        result['extracted_info'] = {
            'travel_companion': extracted.get('travel_companion', 'solo'),
            'budget_extracted': extracted.get('extracted', {}).get('budget_found', False),
            'days_extracted': extracted.get('extracted', {}).get('days_found', False),
            'city_extracted': extracted.get('extracted', {}).get('city_found', False)
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Error in /itinerary endpoint:")
        print(error_trace)
        
        # Trả về lỗi chi tiết để debug
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "error_type": type(e).__name__,
                "message": f"Lỗi khi tạo lịch trình: {str(e)}",
                "query": q,
                "hint": "Kiểm tra console server để xem traceback chi tiết"
            }
        )


@app.get("/ask")
async def ask_question(q: str = Query(..., description="Câu hỏi về địa điểm")):
    """
    Q&A endpoint - Trả lời câu hỏi về thông tin địa điểm
    """
    try:
        result = qa_system.answer_question(q)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Lỗi xử lý câu hỏi: {str(e)}"
        )


# ==================== OPENAI VISION Q&A ENDPOINTS ====================

@app.post("/ask_photo")
async def ask_photo(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None, description="Câu hỏi về ảnh (ví dụ: đây là nơi nào, địa chỉ đây là đâu)")
):
    """
    Vision Q&A endpoint - Nhận diện địa danh từ ảnh upload
    Hỗ trợ cả HuggingFace (miễn phí), Gemini và OpenAI
    Có thể gửi kèm câu hỏi về ảnh
    """
    print("=" * 60)
    print("📸 /ask_photo endpoint được gọi")
    print(f"   File name: {file.filename}")
    print(f"   Content type: {file.content_type}")
    print(f"   Question: {question}")
    print(f"   Vision mode: {VISION_MODE}")
    print(f"   Vision QA instance: {vision_qa_instance is not None}")
    
    try:
        # Validate file type
        print("🔍 Validating file type...")
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="File phải là ảnh (JPEG, PNG, etc.)"
            )
        
        if vision_qa_instance is None:
            print("[ERROR] ERROR: Vision QA instance is None!")
            raise HTTPException(
                status_code=500, 
                detail=f"Vision QA chưa được khởi tạo. Kiểm tra API key ({VISION_MODE})."
            )
        
        # Tạo thư mục temp_uploads nếu chưa có
        os.makedirs("temp_uploads", exist_ok=True)
        print("📁 temp_uploads directory ready")
        
        # Lưu file tạm
        file_path = f"temp_uploads/{file.filename}"
        print(f"💾 Saving file to: {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = os.path.getsize(file_path)
        print(f"[OK] File saved successfully. Size: {file_size:,} bytes")
        
        provider_names = {
            "huggingface": "Hugging Face",
            "gemini": "Gemini",
            "openai": "OpenAI"
        }
        provider_name = provider_names.get(VISION_MODE, VISION_MODE)
        print(f"🔍 Processing image: {file_path} với {provider_name} Vision")
        if question:
            print(f"📝 Question: {question}")
        
        # Gọi Vision QA với question nếu có
        print(f"🤖 Calling vision_qa_instance.recognize_place...")
        if hasattr(vision_qa_instance, 'recognize_place'):
            # Kiểm tra xem method có nhận question parameter không
            import inspect
            sig = inspect.signature(vision_qa_instance.recognize_place)
            print(f"   Method signature: {sig}")
            if 'question' in sig.parameters:
                print(f"   Calling with question parameter...")
                result = vision_qa_instance.recognize_place(file_path, question=question)
            else:
                print(f"   Calling without question parameter...")
                result = vision_qa_instance.recognize_place(file_path)
        else:
            print(f"   [WARN] vision_qa_instance không có method recognize_place!")
            result = vision_qa_instance.recognize_place(file_path)
        
        print(f"[OK] Vision QA result: success={result.get('success')}, place_name={result.get('place_name')}")
        
        # Tạo response tối ưu - loại bỏ các field không cần thiết để tránh lỗi Content-Length
        response_data = {
            "success": result.get("success", False),
            "place_name": result.get("place_name", ""),
            "confidence": result.get("confidence", "thấp"),
            "vision_mode": VISION_MODE,
            "ai_provider": VISION_MODE
        }
        
        # Thêm question nếu có
        if question:
            response_data["question"] = question
        
        # Helper functions để xử lý NaN values (định nghĩa trước khi sử dụng)
        def safe_str(value, default=""):
            """Chuyển đổi value thành string, xử lý NaN và None"""
            if value is None:
                return default
            # Kiểm tra NaN (float NaN không bằng chính nó)
            if isinstance(value, float) and value != value:
                return default
            # Kiểm tra pandas NaN
            try:
                import pandas as pd
                if pd.isna(value):
                    return default
            except:
                pass
            return str(value) if value else default
        
        def safe_float(value, default=0.0):
            """Chuyển đổi value thành float, xử lý NaN và None"""
            if value is None:
                return default
            # Kiểm tra NaN
            if isinstance(value, float) and value != value:
                return default
            try:
                import pandas as pd
                if pd.isna(value):
                    return default
                if hasattr(value, 'item'):  # numpy/pandas scalar
                    return float(value.item())
            except:
                pass
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        def safe_int(value, default=0):
            """Chuyển đổi value thành int, xử lý NaN và None"""
            if value is None:
                return default
            # Kiểm tra NaN
            if isinstance(value, float) and value != value:
                return default
            try:
                import pandas as pd
                if pd.isna(value):
                    return default
                if hasattr(value, 'item'):  # numpy/pandas scalar
                    return int(value.item())
            except:
                pass
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return default
        
        # Thêm matched place data nếu có (nhưng giới hạn kích thước)
        if result.get("matched"):
            matched = result.get("matched")
            if isinstance(matched, dict):
                # Xử lý description - có thể là NaN
                desc = matched.get("description") or matched.get("desc") or ""
                desc_str = safe_str(desc, "")
                
                # Chỉ lấy các field cần thiết, giới hạn độ dài text
                response_data["matched"] = {
                    "name": safe_str(matched.get("name", "")),
                    "description": desc_str[:500] if desc_str else "",  # Giới hạn 500 chars
                    "address": safe_str(matched.get("address", "")),
                    "category": safe_str(matched.get("category", "")),
                    "rating": safe_float(matched.get("rating", 0), 0.0),
                    "avg_cost": safe_int(matched.get("avg_cost", 0), 0),
                    "opening_hours": safe_str(matched.get("opening_hours", "")),
                    "best_time": safe_str(matched.get("best_time", ""))
                }
            else:
                response_data["matched"] = matched
        
        # Thêm place_data nếu có
        if result.get("place_data"):
            place_data = result.get("place_data")
            if isinstance(place_data, dict):
                # Sử dụng lại helper functions đã định nghĩa ở trên
                desc_place = place_data.get("description") or place_data.get("desc") or ""
                desc_place_str = safe_str(desc_place, "")
                
                response_data["place_data"] = {
                    "name": safe_str(place_data.get("name", "")),
                    "description": desc_place_str[:500] if desc_place_str else "",  # Giới hạn 500 chars
                    "address": safe_str(place_data.get("address", "")),
                    "category": safe_str(place_data.get("category", "")),
                    "rating": safe_float(place_data.get("rating", 0), 0.0),
                    "avg_cost": safe_int(place_data.get("avg_cost", 0), 0)
                }
        
        # Thêm basic_info nếu có
        if result.get("basic_info"):
            response_data["basic_info"] = result.get("basic_info")
        
        # Thêm reasoning nếu có (giới hạn độ dài)
        if result.get("reasoning"):
            response_data["reasoning"] = str(result.get("reasoning"))[:200]  # Giới hạn 200 chars
        
        # Thêm error nếu có
        if result.get("error"):
            response_data["error"] = result.get("error")
        if result.get("error_type"):
            response_data["error_type"] = result.get("error_type")
        if result.get("error_detail"):
            response_data["error_detail"] = result.get("error_detail")
        
        # Thêm note nếu có
        if result.get("note"):
            response_data["note"] = result.get("note")
        
        # LOẠI BỎ các field lớn không cần thiết:
        # - caption (có thể rất dài)
        # - openai_response, gemini_response (chứa toàn bộ API response)
        # - source (không cần thiết cho frontend)
        
        # Xóa file tạm
        try:
            os.remove(file_path)
        except:
            pass
        
        # Trả về response đã được tối ưu
        # Encode response để đảm bảo tất cả các giá trị đều có thể serialize
        try:
            encoded_result = custom_encoder.encode(response_data)
        except Exception as encode_error:
            print(f"[WARN] Lỗi encode response: {encode_error}")
            import traceback
            traceback.print_exc()
            encoded_result = response_data
        
        # Serialize thành JSON string trước để đảm bảo encoding đúng
        # Sau đó trả về dict để FastAPI tự xử lý (tránh lỗi Content-Length)
        try:
            # Test serialize để đảm bảo không có lỗi
            json_str = json.dumps(encoded_result, ensure_ascii=False, default=str)
            json_size = len(json_str.encode('utf-8'))
            print(f"📊 Response size: {json_size:,} bytes ({json_size/1024:.2f} KB)")
            
            # Nếu response quá lớn (>1MB), cảnh báo
            if json_size > 1024 * 1024:
                print(f"[WARN] WARNING: Response quá lớn ({json_size/1024/1024:.2f} MB)!")
            
            # Nếu serialize thành công, return dict
            return encoded_result
        except (TypeError, ValueError) as json_error:
            print(f"[WARN] Lỗi JSON serialization: {json_error}")
            import traceback
            traceback.print_exc()
            # Nếu có lỗi, loại bỏ các field có vấn đề
            safe_result = {}
            for k, v in encoded_result.items():
                try:
                    json.dumps(v, ensure_ascii=False, default=str)
                    safe_result[k] = v
                except:
                    print(f"[WARN] Field '{k}' không thể serialize, chuyển sang string")
                    safe_result[k] = str(v)[:100]  # Giới hạn 100 chars nếu không serialize được
            return safe_result
        
    except HTTPException:
        raise
    except Exception as e:
        # Cleanup file nếu có lỗi
        try:
            if 'file_path' in locals():
                os.remove(file_path)
        except:
            pass
        
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Error in /ask_photo endpoint:")
        print(error_trace)
        
        # Trả về error message chi tiết hơn
        error_detail = str(e)
        if "API error" in error_detail or "api" in error_detail.lower():
            error_detail = f"Lỗi API: {error_detail}. Kiểm tra console server để xem chi tiết."
        elif "timeout" in error_detail.lower():
            error_detail = f"Timeout khi xử lý ảnh. Vui lòng thử lại sau."
        elif "connection" in error_detail.lower():
            error_detail = f"Không thể kết nối đến Vision API. Kiểm tra kết nối mạng."
        
        raise HTTPException(
            status_code=500, 
            detail=error_detail
        )


@app.post("/ask_photo_url")
async def ask_photo_url(image_url: str = Form(..., description="URL của ảnh")):
    """
    OpenAI Vision Q&A endpoint - Nhận diện địa danh từ URL ảnh
    """
    try:
        if vision_qa_instance is None:
            raise HTTPException(
                status_code=500, 
                detail="OpenAI Vision QA chưa được khởi tạo. Kiểm tra API key."
            )
        
        # Validate URL
        if not image_url.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=400,
                detail="URL phải bắt đầu với http:// hoặc https://"
            )
        
        print(f"🔍 Processing image URL với OpenAI Vision: {image_url}")
        
        result = vision_qa_instance.recognize_place(image_url)
        result["vision_mode"] = VISION_MODE
        result["ai_provider"] = "openai"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Lỗi xử lý URL ảnh: {str(e)}"
        )


@app.get("/smart_query")
async def smart_query(
    q: str = Query(..., description="Query thông minh - tự động phân luồng"),
    city: str = Query("Da Nang", description="Thành phố"),
    use_llm: bool = Query(True, description="Sử dụng LLM để xử lý query"),
    use_google_search: bool = Query(False, description="Tìm kiếm thông tin bổ sung từ Google")
):
    """
    Smart query endpoint - Tự động phân luồng Q&A hoặc itinerary
    Có thể sử dụng LLM và Google Search để cải thiện kết quả
    """
    original_query = q
    enhanced_query = q
    
    # Sử dụng LLM để xử lý query nếu được bật
    llm_result = None
    if use_llm and llm_processor_instance and llm_processor_instance.enabled:
        try:
            llm_result = llm_processor_instance.process_query(q)
            if llm_result.get("success"):
                # Có thể sử dụng thông tin từ LLM để enhance query
                enhanced_query = llm_processor_instance.enhance_query(q)
        except Exception as e:
            print(f"[WARN] LLM processing error: {e}")
    
    # Tìm kiếm Google nếu được bật
    google_results = None
    if use_google_search and google_search_instance and google_search_instance.enabled:
        try:
            google_results = google_search_instance.search(q, num_results=3)
        except Exception as e:
            print(f"[WARN] Google Search error: {e}")
    
    query_type = route_query(q)
    
    if query_type == "qa":
        # Route to Q&A system
        qa_result = qa_system.answer_question(q)
        
        # Thêm thông tin từ Google Search nếu có
        if google_results:
            qa_result["google_search_results"] = google_results[:2]  # Top 2 results
        
        return {
            "query": q,
            "enhanced_query": enhanced_query,
            "query_type": "qa",
            "result": qa_result,
            "llm_processed": llm_result is not None,
            "google_search_used": google_results is not None
        }
    else:
        # Route to itinerary system
        # Sử dụng thông tin từ LLM nếu có
        if llm_result and llm_result.get("success"):
            extracted_info = llm_result
            city = extracted_info.get("city") or city
        else:
            # Fallback to QueryExtractor
            extracted = QueryExtractor.extract_all(q)
            city = extracted.get("city") or city
        
        results = recommender.recommend(
            query=enhanced_query,
            city=city,
            top_k=10,
            diversity_threshold=0.90
        )
        
        return {
            "query": q,
            "enhanced_query": enhanced_query,
            "query_type": "itinerary", 
            "results": results,
            "count": len(results),
            "llm_processed": llm_result is not None,
            "google_search_used": google_results is not None,
            "llm_info": llm_result if llm_result else None
        }


@app.get("/search")
async def search_google(
    q: str = Query(..., description="Query tìm kiếm trên Google"),
    num_results: int = Query(5, ge=1, le=10, description="Số kết quả")
):
    """
    Google Search endpoint - Tìm kiếm thông tin từ Google
    """
    if not google_search_instance or not google_search_instance.enabled:
        raise HTTPException(
            status_code=503,
            detail="Google Search API chưa được cấu hình. Set GOOGLE_SEARCH_API_KEY và GOOGLE_SEARCH_ENGINE_ID trong .env"
        )
    
    results = google_search_instance.search(q, num_results=num_results)
    
    return {
        "query": q,
        "results": results,
        "count": len(results)
    }


@app.get("/search_place")
async def search_place_info(
    place_name: str = Query(..., description="Tên địa điểm"),
    city: str = Query("Da Nang", description="Thành phố")
):
    """
    Tìm kiếm thông tin về địa điểm từ Google
    """
    if not google_search_instance or not google_search_instance.enabled:
        raise HTTPException(
            status_code=503,
            detail="Google Search API chưa được cấu hình"
        )
    
    result = google_search_instance.search_place_info(place_name, city)
    return result


@app.get("/place_details")
async def get_place_details(
    place_name: str = Query(..., description="Tên địa danh"),
    detail_type: str = Query("all", description="Loại thông tin: all, history, highlights, features, cultural, tips")
):
    """
    Lấy thông tin chi tiết về địa danh (lịch sử, điểm nổi bật, v.v.)
    """
    from src.place_details import PlaceDetailsManager
    
    details_manager = PlaceDetailsManager()
    
    if detail_type == "all":
        details = details_manager.get_full_info(place_name)
    elif detail_type == "history":
        history = details_manager.get_history(place_name)
        details = {"place_name": place_name, "history": history}
    elif detail_type == "highlights":
        highlights = details_manager.get_highlights(place_name)
        details = {"place_name": place_name, "highlights": highlights}
    elif detail_type == "features":
        features = details_manager.get_features(place_name)
        details = {"place_name": place_name, "features": features}
    elif detail_type == "cultural":
        cultural = details_manager.get_cultural_significance(place_name)
        details = {"place_name": place_name, "cultural_significance": cultural}
    elif detail_type == "tips":
        tips = details_manager.get_tips(place_name)
        details = {"place_name": place_name, "tips": tips}
    else:
        details = details_manager.get_full_info(place_name)
    
    if not details or not any(details.values()):
        return {
            "success": False,
            "message": f"Không tìm thấy thông tin chi tiết về '{place_name}'",
            "suggestion": "Chạy script crawl_place_details.py để crawl thông tin chi tiết"
        }
    
    return {
        "success": True,
        "place_name": place_name,
        "detail_type": detail_type,
        "details": details
    }


@app.get("/llm_process")
async def llm_process_query(
    q: str = Query(..., description="Query cần xử lý với LLM")
):
    """
    Xử lý query với LLM
    """
    if not llm_processor_instance or not llm_processor_instance.enabled:
        raise HTTPException(
            status_code=503,
            detail="LLM Processor chưa được cấu hình. Set OPENAI_API_KEY hoặc GEMINI_API_KEY trong .env"
        )
    
    result = llm_processor_instance.process_query(q)
    return result


@app.get("/_debug/preview")
async def debug_preview(
    q: str = Query(..., description="Query debug"),
    city: str = Query("Da Nang", description="Thành phố")
):
    """
    Debug endpoint - Xem query embedding và top results
    """
    query_embedding = recommender.encode_query(q)
    
    results = recommender.recommend(
        query=q,
        city=city,
        top_k=10,
        diversity_threshold=1.0
    )
    
    return {
        "query": q,
        "query_embedding_norm": float(np.linalg.norm(query_embedding)),
        "top_10_results": results
    }


@app.get("/_debug/qa")
async def debug_qa(q: str = Query(..., description="QA debug query")):
    """
    Debug endpoint cho Q&A system
    """
    result = qa_system.answer_question(q)
    return {
        "question": q,
        "result": result
    }


@app.get("/_debug/vision_status")
async def debug_vision_status():
    """
    Debug endpoint cho OpenAI Vision QA system
    """
    status = {
        "vision_qa_initialized": vision_qa_instance is not None,
        "openai_api_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "openai_model": os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini"),
        "temp_uploads_exists": os.path.exists("temp_uploads"),
        "test_images_exists": os.path.exists("test_images"),
        "vision_mode": VISION_MODE,
        "ai_provider": "openai"
    }
    
    if vision_qa_instance:
        status["places_loaded"] = hasattr(vision_qa_instance, 'df_places') and vision_qa_instance.df_places is not None
        if hasattr(vision_qa_instance, 'df_places') and vision_qa_instance.df_places is not None:
            status["places_count"] = len(vision_qa_instance.df_places)
        
        status["has_recognize_place"] = hasattr(vision_qa_instance, 'recognize_place')
    
    # Liệt kê các file trong thư mục test_images
    if os.path.exists("test_images"):
        test_images = [f for f in os.listdir("test_images") if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        status["test_images_files"] = test_images
    
    return status


@app.get("/test_connection")
async def test_connection():
    """Test endpoint để kiểm tra kết nối OpenAI"""
    openai_status = "active" if vision_qa_instance is not None else "inactive"
    
    return {
        "status": "ok",
        "message": "Server đang chạy với OpenAI",
        "ai_provider": "openai",
        "openai_status": openai_status,
        "vision_mode": VISION_MODE,
        "timestamp": pd.Timestamp.now().isoformat()
    }


@app.get("/test_vision_local")
async def test_vision_local(question: Optional[str] = Query(None, description="Câu hỏi về ảnh (tùy chọn)")):
    """Test Vision QA với ảnh local trong thư mục test_images"""
    if vision_qa_instance is None:
        raise HTTPException(
            status_code=500, 
            detail=f"Vision QA chưa được khởi tạo (Mode: {VISION_MODE})"
        )
    
    # Kiểm tra thư mục test_images
    if not os.path.exists("test_images"):
        return {
            "success": False,
            "error": "Thư mục test_images không tồn tại"
        }
    
    # Tìm tất cả file ảnh trong thư mục test_images
    image_files = []
    for file in os.listdir("test_images"):
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            image_files.append(file)
    
    if not image_files:
        return {
            "success": False,
            "error": "Không tìm thấy file ảnh nào trong thư mục test_images",
            "solution": "Hãy đặt ảnh vào thư mục test_images với định dạng .jpg, .jpeg, .png"
        }
    
    results = {}
    
    for image_file in image_files:
        image_path = f"test_images/{image_file}"
        print(f"🧪 Testing với ảnh local: {image_file}")
        
        try:
            # Gọi với question nếu có
            if hasattr(vision_qa_instance, 'recognize_place'):
                import inspect
                sig = inspect.signature(vision_qa_instance.recognize_place)
                if 'question' in sig.parameters:
                    result = vision_qa_instance.recognize_place(image_path, question=question)
                else:
                    result = vision_qa_instance.recognize_place(image_path)
            else:
                result = vision_qa_instance.recognize_place(image_path)
            
            results[image_file] = {
                "file": image_file,
                "place_name": result.get("place_name", ""),
                "confidence": result.get("confidence", "thấp"),
                "success": result.get("success", False),
                "matched": result.get("matched", False),
                "error": result.get("error", ""),
                "reasoning": result.get("reasoning", ""),
                "source": result.get("source", VISION_MODE),
                "caption": result.get("caption", "")  # Cho Hugging Face
            }
        except Exception as e:
            results[image_file] = {
                "file": image_file,
                "error": str(e),
                "success": False
            }
    
    # Tính toán kết quả
    total_tests = len(results)
    successful = sum(1 for r in results.values() if r.get("success"))
    matched = sum(1 for r in results.values() if r.get("matched"))
    
    return {
        "test_results": results,
        "summary": {
            "total_tests": total_tests,
            "successful": successful,
            "failed": total_tests - successful,
            "matched_with_database": matched,
            "success_rate": f"{(successful/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "test_images_folder": "test_images",
            "images_found": image_files
        }
    }


@app.post("/test_upload_local")
async def test_upload_local(file: UploadFile = File(...)):
    """Test upload ảnh từ local để đảm bảo hoạt động"""
    if vision_qa_instance is None:
        raise HTTPException(status_code=500, detail="Vision QA chưa khởi tạo")
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="File phải là ảnh (JPEG, PNG, etc.)"
            )
        
        # Lưu file tạm
        file_path = f"temp_uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"🧪 Testing với ảnh upload: {file.filename}")
        
        # Gọi Vision QA
        result = vision_qa_instance.recognize_place(file_path)
        
        # Xóa file tạm
        try:
            os.remove(file_path)
        except:
            pass
        
        return {
            "filename": file.filename,
            "result": result
        }
        
    except Exception as e:
        # Cleanup
        try:
            if 'file_path' in locals():
                os.remove(file_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@app.get("/test_single_image")
async def test_single_image(
    filename: str = Query(..., description="Tên file ảnh trong test_images"),
    question: Optional[str] = Query(None, description="Câu hỏi về ảnh (tùy chọn)")
):
    """Test với 1 ảnh cụ thể trong thư mục test_images"""
    if vision_qa_instance is None:
        raise HTTPException(status_code=500, detail=f"Vision QA chưa khởi tạo (Mode: {VISION_MODE})")
    
    image_path = f"test_images/{filename}"
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"File {filename} không tồn tại trong test_images")
    
    try:
        # Gọi với question nếu có
        if hasattr(vision_qa_instance, 'recognize_place'):
            import inspect
            sig = inspect.signature(vision_qa_instance.recognize_place)
            if 'question' in sig.parameters:
                result = vision_qa_instance.recognize_place(image_path, question=question)
            else:
                result = vision_qa_instance.recognize_place(image_path)
        else:
            result = vision_qa_instance.recognize_place(image_path)
        
        return {
            "filename": filename,
            "question": question,
            "result": result,
            "vision_mode": VISION_MODE
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Error testing image {filename}:")
        print(error_trace)
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý ảnh: {str(e)}")


# ==================== Authentication Endpoints ====================

@app.post("/api/login")
async def login(request: Request):
    """Đăng nhập"""
    try:
        data = await request.json()
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        
        if not username:
            raise HTTPException(status_code=400, detail="Vui lòng nhập tên đăng nhập")
        
        if not password:
            raise HTTPException(status_code=400, detail="Vui lòng nhập mật khẩu")
        
        # Tìm user
        user = find_user_by_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")
        
        # Kiểm tra tài khoản
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa")
        
        # Verify password
        if not verify_password(password, user.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")
        
        # Tạo session
        session_token = create_session(user["id"])
        update_user_last_login(user["id"])
        
        # Trả về thông tin user (không bao gồm password)
        user_info = {k: v for k, v in user.items() if k != "password_hash"}
        
        return {
            "success": True,
            "message": "Đăng nhập thành công",
            "data": {
                "user": user_info,
                "session_token": session_token
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Có lỗi xảy ra khi đăng nhập: {str(e)}")


@app.post("/api/register")
async def register(request: Request):
    """Đăng ký"""
    try:
        data = await request.json()
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        confirm_password = data.get("confirm_password", "").strip()
        email = data.get("email", "").strip() or None
        full_name = data.get("full_name", "").strip() or None
        
        # Validate
        if not username:
            raise HTTPException(status_code=400, detail="Tên đăng nhập không được để trống")
        
        if len(username) < 3 or len(username) > 50:
            raise HTTPException(status_code=400, detail="Tên đăng nhập phải từ 3-50 ký tự")
        
        if not username.replace("_", "").isalnum():
            raise HTTPException(status_code=400, detail="Tên đăng nhập chỉ cho phép chữ cái, số và dấu gạch dưới")
        
        if not password:
            raise HTTPException(status_code=400, detail="Mật khẩu không được để trống")
        
        if len(password) < 4:
            raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 4 ký tự")
        
        if password != confirm_password:
            raise HTTPException(status_code=400, detail="Mật khẩu xác nhận không khớp")
        
        if email and "@" not in email:
            raise HTTPException(status_code=400, detail="Email không hợp lệ")
        
        # Kiểm tra username đã tồn tại chưa
        if find_user_by_username(username):
            raise HTTPException(status_code=400, detail="Tên đăng nhập đã được sử dụng")
        
        # Kiểm tra email đã tồn tại chưa (nếu có)
        if email and find_user_by_email(email):
            raise HTTPException(status_code=400, detail="Email đã được sử dụng")
        
        # Tạo user mới
        new_user = add_user(username, password, email, full_name)
        
        # Tự động đăng nhập
        session_token = create_session(new_user["id"])
        
        # Trả về thông tin user (không bao gồm password)
        user_info = {k: v for k, v in new_user.items() if k != "password_hash"}
        
        return {
            "success": True,
            "message": "Đăng ký thành công",
            "data": {
                "user": user_info,
                "session_token": session_token
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Register error: {e}")
        raise HTTPException(status_code=500, detail=f"Có lỗi xảy ra khi đăng ký: {str(e)}")


@app.post("/api/logout")
async def logout(request: Request):
    """Đăng xuất"""
    try:
        data = await request.json()
        session_token = data.get("session_token", "")
        
        if session_token:
            delete_session(session_token)
        
        return {
            "success": True,
            "message": "Đã đăng xuất thành công"
        }
    except Exception as e:
        print(f"Logout error: {e}")
        return {
            "success": True,
            "message": "Đã đăng xuất"
        }


@app.get("/api/check_session")
async def check_session(session_token: str = Query(..., description="Session token")):
    """Kiểm tra session còn hợp lệ không"""
    try:
        cleanup_expired_sessions()
        
        session = find_session_by_token(session_token)
        if not session:
            raise HTTPException(status_code=401, detail="Session không hợp lệ hoặc đã hết hạn")
        
        user = find_user_by_id(session["user_id"])
        if not user:
            raise HTTPException(status_code=401, detail="User không tồn tại")
        
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa")
        
        # Trả về thông tin user (không bao gồm password)
        user_info = {k: v for k, v in user.items() if k != "password_hash"}
        
        return {
            "success": True,
            "message": "Session hợp lệ",
            "data": {
                "user": user_info,
                "session_token": session_token
            }
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Check session error: {e}")
        raise HTTPException(status_code=500, detail=f"Có lỗi xảy ra khi kiểm tra session: {str(e)}")


# ==================== TRAVEL PLANS ENDPOINTS ====================
# Predefined travel plans for Da Nang, Hoi An, Hue.
# 5 core plans + 3 adaptive plans per city = 24 plans total.

# IMPORTANT: Register simple endpoints FIRST so /simple-list, /simple-detail, /simple-match
# take precedence over the generic /api/travel-plans/{city} catch-all below.
from src.plans.simple_endpoint import register as register_simple_endpoints
register_simple_endpoints(app)

@app.get("/api/travel-plans")
async def list_travel_plans(city: Optional[str] = Query(None, description="Filter by city: danang, hoian, hue")):
    """
    List all predefined travel plans.
    Use ?city=danang to filter, otherwise returns all 24.
    """
    try:
        from src.plans.plan_engine import list_all_plans_for_ui
        plans = list_all_plans_for_ui()
        if city:
            city_norm = city.strip().lower()
            plans = [p for p in plans if p.get("city") == city_norm]
        return {
            "success": True,
            "count": len(plans),
            "city": city,
            "plans": plans
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error listing plans: {str(e)}")


@app.get("/api/travel-plans/{city}")
async def list_travel_plans_by_city(city: str):
    """List plans for a specific city. city: danang, hoian, hue."""
    try:
        from src.plans.plan_engine import list_all_plans_for_ui
        plans = list_all_plans_for_ui()
        city_norm = city.strip().lower()
        city_plans = [p for p in plans if p.get("city") == city_norm]
        if not city_plans:
            raise HTTPException(
                status_code=404,
                detail=f"City '{city}' không hỗ trợ. Chỉ hỗ trợ: danang, hoian, hue"
            )
        return {
            "success": True,
            "city": city_norm,
            "count": len(city_plans),
            "plans": city_plans,
            "core_plans": [p for p in city_plans if p.get("plan_type") == "core"],
            "adaptive_plans": [p for p in city_plans if p.get("plan_type") == "adaptive"],
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error listing plans: {str(e)}")


@app.post("/api/travel-plans/match")
async def match_travel_plans(request: Request):
    """
    Match user intent to a predefined travel plan.

    Request body:
    {
        "query": "Tôi muốn đi Đà Nẵng 3 ngày 2 đêm, budget 6 triệu",
        "city": "Da Nang",            // optional, override
        "days": 3,                     // optional, override
        "budget_total": 6000000,       // optional, override
        "travel_companion": "couple",  // optional
        "max_secondary": 2             // optional, default 2
    }

    Response: full plan response with primary + secondary plans + itinerary
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    query = body.get("query", "")
    city = body.get("city")
    days = body.get("days")
    budget_total = body.get("budget_total")
    travel_companion = body.get("travel_companion")
    max_secondary = body.get("max_secondary", 2)

    try:
        from src.plans.plan_engine import generate_plan_response
        result = generate_plan_response(
            query=query,
            city=city,
            days=days,
            budget_total=budget_total,
            travel_companion=travel_companion,
            max_secondary=max_secondary,
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error matching plan: {str(e)}")


@app.post("/api/travel-plans/generate")
async def generate_itinerary_from_plan(request: Request):
    """
    Generate a full day-by-day itinerary from a matched plan.
    Same input as /api/travel-plans/match.
    Internally: match plan → adapt to days/budget → rank places → build itinerary.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    query = body.get("query", "")
    city = body.get("city")
    days = body.get("days")
    budget_total = body.get("budget_total")
    travel_companion = body.get("travel_companion")
    max_secondary = body.get("max_secondary", 2)

    try:
        from src.plans.plan_engine import generate_plan_response
        result = generate_plan_response(
            query=query,
            city=city,
            days=days,
            budget_total=budget_total,
            travel_companion=travel_companion,
            max_secondary=max_secondary,
        )
        # 'result' already contains itinerary from build_itinerary_from_plan
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating itinerary: {str(e)}")


# ==================== SIMPLE MATCH (24 hard-coded plans) ====================
# Register the simple matcher endpoints (no-op since already registered above)
# Kept for backward compatibility; second registration will be ignored by FastAPI.
# from src.plans.simple_endpoint import register as register_simple_endpoints
# register_simple_endpoints(app)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true",
        log_level="info"
    )