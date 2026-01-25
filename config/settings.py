# -*- coding: utf-8 -*-
import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем переменные из .env (файл в корне проекта)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "bot.db")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env")
