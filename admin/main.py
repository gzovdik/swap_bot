# -*- coding: utf-8 -*-
"""
Админ-панель (FastAPI). Запуск: uvicorn admin.main:app --host 0.0.0.0 --port 8000
"""
from pathlib import Path
import sys

# Корень проекта в path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI(title="SwapBot Admin")


@app.get("/")
async def root():
    return PlainTextResponse("SwapBot Admin API. Документация: /docs")


@app.get("/health")
async def health():
    return {"status": "ok"}
