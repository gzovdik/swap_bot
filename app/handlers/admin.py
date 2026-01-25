# -*- coding: utf-8 -*-
"""
Админ-команды (заглушка). Только для пользователей из ADMIN_IDS.
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id in (settings.ADMIN_IDS or [])


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа.")
        return
    await message.answer(
        "⚙️ <b>Админ-панель</b>\n\n"
        "Веб-панель: включите ADMIN_PANEL_ENABLED и запустите uvicorn admin.main:app. "
        "Пока доступны только команды бота."
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not _is_admin(message.from_user.id):
        return
    await message.answer("📊 Статистика: включите аналитику и БД для отчётов.")
