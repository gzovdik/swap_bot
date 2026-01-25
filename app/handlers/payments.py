# -*- coding: utf-8 -*-
"""
Монетизация (заглушка). Premium, буст объявлений через Telegram Payments.
"""
from aiogram import Router, F
from aiogram.types import Message

from app.config import settings

router = Router()


@router.message(F.text == "⭐ Premium")
async def premium_stub(message: Message):
    if not settings.PAYMENT_PROVIDER_TOKEN:
        await message.answer(
            "⭐ <b>Premium</b>\n\n"
            "Платежи не настроены. Укажите PAYMENT_PROVIDER_TOKEN в .env."
        )
        return
    await message.answer(
        "⭐ <b>Premium</b>\n\n"
        "Здесь будет оформление подписки (Telegram Payments)."
    )
