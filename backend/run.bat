@echo off
chcp 65001 >nul
cd /d E:\code\Lingxi-Support-AI\backend
call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --port 8000
