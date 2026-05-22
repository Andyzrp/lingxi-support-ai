$env:PYTHONIOENCODING = "utf-8"
cd E:\code\Lingxi-Support-AI\backend
& "E:\code\Lingxi-Support-AI\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
