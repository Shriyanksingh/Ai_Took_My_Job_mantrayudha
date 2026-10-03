@echo off
setlocal
if not exist .venv\Scripts\python.exe (
  echo Creating virtual environment...
  py -m venv .venv
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
endlocal
