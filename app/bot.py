# -*- coding: utf-8 -*-
"""
Точка входа бота. Запуск: python -m app.bot (из корня swap_bot).
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.database.db import init_db
from app.handlers import start, profile, ads, browse, chat, admin, payments


async def main() -> None:
    if not settings.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN не задан. Создайте .env в корне проекта и укажите BOT_TOKEN=...")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    await init_db()
    settings.MEDIA_PATH.mkdir(parents=True, exist_ok=True)

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(ads.router)
    dp.include_router(browse.router)
    dp.include_router(chat.router)
    dp.include_router(admin.router)
    dp.include_router(payments.router)

    logging.info("🤖 SwapBot запущен")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")
