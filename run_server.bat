@echo off
REM ===========================================================
REM  AI Travel Assistant - Server starter (Windows)
REM  Bam kep vao file nay de chay server
REM ===========================================================

cd /d "D:\AI-For-Life-main\AI-For-Life-main"

REM --- Force UTF-8 in this CMD window (fix Windows-1252 / mojibake) ---
chcp 65001 >nul

echo.
echo ============================================================
echo   AI Travel Assistant - Server
echo ============================================================
echo.

REM Kiem tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong tim thay Python. Hay cai Python 3.10+ va them vao PATH.
    echo        Tai tai: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Kiem tra venv
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Chua co venv, dang tao...
    python -m venv .venv
    if errorlevel 1 (
        echo [LOI] Tao venv that bai.
        pause
        exit /b 1
    )
)

REM Kiem tra .env
if not exist ".env" (
    echo [INFO] Tao file .env mac dinh...
    (
        echo HOST=0.0.0.0
        echo PORT=8000
        echo DEBUG=True
        echo LLM_PROVIDER=openai
        echo LLM_MODEL=gpt-4o-mini
        echo VISION_PROVIDER=huggingface
    ) > .env
)

REM Kiem tra dependencies (cach don gian: thu import)
.venv\Scripts\python.exe -c "import fastapi, uvicorn" 2>nul
if errorlevel 1 (
    echo [INFO] Chua cai dependencies, dang cai tu requirements.txt...
    echo        Co the mat 1-3 phut, vui long doi...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [LOI] Cai dat that bai. Kiem tra ket noi mang.
        pause
        exit /b 1
    )
    echo [OK] Cai dat xong.
)

REM ============================================================
REM   Kiem tra port 8000 - neu bi chiem thi doi port khac
REM ============================================================
set "SERVER_PORT=8000"

REM Lay gia tri PORT tu .env neu co
for /f "tokens=2 delims==" %%a in ('findstr /b /c:"PORT=" .env 2^>nul') do (
    set "SERVER_PORT=%%a"
)

echo.
echo [CHECK] Kiem tra port %SERVER_PORT%...

REM PowerShell de kiem tra port co dang LISTENING khong
REM Dung %%PS_PORT%% de tranh bat tu expand %%P%% thanh "P"
powershell -NoProfile -Command ^
    "$p=[int]'%SERVER_PORT%'; $listening=Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue; " ^
    "if ($listening) { " ^
    "    $proc=(Get-Process -Id $listening.OwningProcess -ErrorAction SilentlyContinue).ProcessName; " ^
    "    Write-Host 'WARN_PORT_OCCUPIED:' $p 'by PID:' $listening.OwningProcess '(' $proc ')'; " ^
    "} else { " ^
    "    Write-Host 'PORT_FREE:' $p; " ^
    "}" > "%TEMP%\port_check.txt" 2>nul

findstr /c:"WARN_PORT_OCCUPIED" "%TEMP%\port_check.txt" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo ============================================================
    echo   [CANH BAO] Port %SERVER_PORT% DA BI CHIEM boi process khac.
    echo   Co the server cu van dang chay, hoac mot chuong trinh khac
    echo   dang dung port nay.
    echo ============================================================
    echo.
    echo   Ban muon lam gi?
    echo     [1] Tu dong chon port khac (8001, 8002, ...)
    echo     [2] Thoat (de toi tat server cu truoc)
    echo.
    set /p "PORT_CHOICE=Nhap 1 hoac 2 (mac dinh 1): "
    if "%PORT_CHOICE%"=="2" (
        echo.
        echo   Hay tat server cu truoc, sau do chay lai file nay.
        echo.
        pause
        exit /b 1
    )
    REM Auto-pick next free port starting from 8001
    for /L %%i in (8001,1,8099) do (
        powershell -NoProfile -Command ^
            "$conn=Get-NetTCPConnection -LocalPort %%i -State Listen -ErrorAction SilentlyContinue; " ^
            "if (-not $conn) { Write-Host %%i }" > "%TEMP%\freeport.txt" 2>nul
        for /f %%j in ('type "%TEMP%\freeport.txt"') do (
            if not "%%j"=="" (
                set "SERVER_PORT=%%j"
                goto :portfound
            )
        )
    )
    :portfound
    echo.
    echo   [OK] Su dung port moi: %SERVER_PORT%
    echo.
)

REM ============================================================
REM   Khoi dong server
REM ============================================================
echo.
echo ============================================================
echo   Server dang khoi dong...
echo   URL: http://localhost:%SERVER_PORT%
echo   UI:  http://localhost:%SERVER_PORT%/ui
echo   Docs: http://localhost:%SERVER_PORT%/docs
echo   Nhan Ctrl+C de dung.
echo ============================================================
echo.

REM Override PORT env var cho uvicorn
set "PORT=%SERVER_PORT%"

REM Chay server (uvicorn.run nam trong main.py)
.venv\Scripts\python.exe main.py

echo.
echo Server da dung. Bam phim bat ky de thoat.
pause >nul