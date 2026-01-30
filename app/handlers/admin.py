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
    """Проверка является ли пользователь админом"""
    admin_ids = settings.ADMIN_IDS
    if isinstance(admin_ids, list):
        return user_id in admin_ids
    return False


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
    
    try:
        from app.database.models import UserModel, AdModel
        
        # Получаем статистику из БД
        # Простая реализация без подсчёта
        await message.answer(
            "📊 <b>Статистика</b>\n\n"
            "Для полной статистики включите аналитику в настройках.\n\n"
            "Доступные команды:\n"
            "/admin - админ-панель\n"
            "/stats - статистика"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка получения статистики: {e}")