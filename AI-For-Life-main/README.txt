================================================================================
  AI TRAVEL ASSISTANT (AI-For-Life)
  He thong goi y lich trinh du lich thong minh
================================================================================


1. GIOI THIEU
--------------------------------------------------------------------------------
AI Travel Assistant la mot ung dung web su dung tri tue nhan tao (AI) de ho
tro nguoi dung lap lich trinh du lich va tra loi cac cau hoi ve dia diem.

Cac tinh nang chinh:
  + Lap lich trinh du lich tu dong theo so thich, ngan sach, so ngay di.
  + Tra loi cau hoi (Q&A) ve thong tin cac dia diem du lich.
  + Vision Q&A: nhan dien dia danh tu anh upload va cung cap thong tin.
  + Goi y thong minh dua tren embedding, reranker va khoang cach dia ly.

Cong nghe su dung:
  - Embedding:    Sentence Transformers (E5 / BGE)
  - Reranking:    Cross-Encoder (BAAI/bge-reranker-v2-m3)
  - Tim kiem:     Cosine Similarity + Haversine distance
  - Vision AI:    Hugging Face (mac dinh, mien phi, chay local) / OpenAI / Gemini
  - LLM (tuy chon): OpenAI, Gemini
  - Backend:      FastAPI + Uvicorn
  - Giao dien:    ui.html (web UI tinh)


2. YEU CAU HE THONG
--------------------------------------------------------------------------------
  + He dieu hanh: Windows 10/11, macOS hoac Linux
  + Python:      3.10 tro len  (tai tai https://www.python.org/downloads/)
  + RAM:         toi thieu 8 GB (khuyen nghi 16 GB neu dung Vision Q&A local)
  + O dia:       ~2 GB trong cho code + thu vien + model


3. CAI DAT
--------------------------------------------------------------------------------
Cach nhanh nhat (khuyen nghi - Windows):

  Buoc 1. Cai Python 3.10+ va them vao PATH.

  Buoc 2. Mo thu muc du an:
             D:\AI-For-Life-main\AI-For-Life-main

  Buoc 3. Nhan doi chuot vao file  run_server.bat  de chay.
          File .bat se tu dong:
            - Tao moi truong ao (.venv) neu chua co
            - Cai dependencies tu requirements.txt
            - Tao file .env mac dinh neu chua co
            - Khoi dong server

----------------------------------------------------------------
Cach thu cong (chay bang tay, dung cho moi he dieu hanh):

  Buoc 1. Tao moi truong ao va kich hoat:

      # Windows (PowerShell / CMD)
      python -m venv .venv
      .venv\Scripts\activate

      # macOS / Linux
      python3 -m venv .venv
      source .venv/bin/activate

  Buoc 2. Cai dat dependencies:

      pip install --upgrade pip
      pip install -r requirements.txt

  Buoc 3. Cau hinh file .env

      File .env da co san trong thu muc goc. Noi dung mac dinh da du de
      chay he thong (Vision Q&A dung Hugging Face local, mien phi).

      Neu muon su dung cac tinh nang tuy chon, them vao .env:
          OPENAI_API_KEY=...        # neu muon doi sang OpenAI Vision/LLM
          GEMINI_API_KEY=...        # neu muon doi sang Gemini Vision
          GOOGLE_SEARCH_API_KEY=... # neu muon bat Google Search API
          GOOGLE_SEARCH_ENGINE_ID=...
          LLM_PROVIDER=openai       # openai | gemini
          LLM_MODEL=gpt-4o-mini

      Luu y: cac key tren la TUY CHON. He thong van chay binh thuong
      voi cac tinh nang co san neu khong co key.


4. CHAY UNG DUNG
--------------------------------------------------------------------------------
Sau khi cai dat xong, khoi dong server bang mot trong cac cach:

  Cach A:  nhan doi chuot  run_server.bat

  Cach B:  chay lenh trong thu muc du an (da kich hoat venv):

              python main.py

  Cach C:  dung uvicorn truc tiep:

              uvicorn main:app --host 0.0.0.0 --port 8000

Khi server chay thanh cong, mo trinh duyet va truy cap:

    Web UI (giao dien chinh) :   http://localhost:8000/ui
    Hoac mo file ui.html     :   ui.html  (trong thu muc du an)
    API documentation        :   http://localhost:8000/docs
    Health check             :   http://localhost:8000/

De dung server: nhan Ctrl + C trong cua so terminal.


5. KIEM TRA NHANH
--------------------------------------------------------------------------------
Health check:

    curl http://localhost:8000/

Test lap lich trinh:

    curl "http://localhost:8000/itinerary?q=tham quan bien&days=2&budget_total=3000000"

Test hoi dap:

    curl "http://localhost:8000/ask?q=Cau Rong o dau"


6. CAU TRUC THU MUC (tóm tat)
--------------------------------------------------------------------------------
  AI-For-Life-main/
    main.py              Server API chinh (FastAPI)
    ui.html              Giao dien web
    run.py               Bootstrap server
    run_server.bat       File khoi dong nhanh tren Windows
    requirements.txt     Danh sach thu vien can cai
    .env                 Bien moi truong (API keys)
    data/                Du lieu dia diem (CSV)
    models/              Embedding / model da tinh san
    src/                 Ma nguon xu ly (recommender, qa, vision, llm, ...)
    dist/                File .exe dong goi (neu co)
    test_images/         Anh mau de test Vision Q&A


7. XU LY SU CO THUONG GAP
--------------------------------------------------------------------------------
- Loi "Khong tim thay Python":
      Cai Python 3.10+ va dam bao da tick "Add Python to PATH" khi cai.

- Loi Vision Q&A khong chay:
      Mac dinh dung Hugging Face local, dam bao da cai torch, transformers,
      pillow (co trong requirements.txt). Hoac doi VISION_PROVIDER=openai
      / gemini trong .env.

- Port 8000 bi chiem:
      run_server.bat se tu dong chon port con trong (8001, 8002, ...).
      Hoac doi PORT trong file .env.

- Cai dat dependencies cham hoac loi mang:
      Kiem tra ket noi internet, neu can dung proxy:
          pip install -r requirements.txt --proxy http://host:port


8. LUU Y
--------------------------------------------------------------------------------
- File .env co chua API key, KHONG commit len git (da co trong .gitignore).
- Lan dau chay co the mat vai phut de tai model embedding ve thu muc
  models/ (neu chua co san).
- Du lieu dia diem da co san trong data/, khong can crawl lai neu khong
  co yeu cau cap nhat.


================================================================================
  Du an phat trien cho muc dich hoc tap va nghien cuu.
  Chuc ban su dung vui ve!
================================================================================
