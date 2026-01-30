# -*- coding: utf-8 -*-
"""
Полная конфигурация бота с поддержкой всех фич
"""
import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения"""

    # Telegram
    BOT_TOKEN: str = Field(default="", env="BOT_TOKEN")
    ADMIN_IDS: str = Field(default="", env="ADMIN_IDS")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://swap_user:swap_pass@localhost:5432/swap_db",
        env="DATABASE_URL"
    )
    DB_PATH: str = Field(default="bot.db", env="DB_PATH")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Storage
    MEDIA_PATH: Path = Field(default=Path("media"))
    USE_S3: bool = Field(default=False, env="USE_S3")
    S3_BUCKET: Optional[str] = Field(default=None, env="S3_BUCKET")
    S3_REGION: Optional[str] = Field(default=None, env="S3_REGION")
    S3_ACCESS_KEY: Optional[str] = Field(default=None, env="S3_ACCESS_KEY")
    S3_SECRET_KEY: Optional[str] = Field(default=None, env="S3_SECRET_KEY")

    # AI & ML
    USE_AI_RECOMMENDATIONS: bool = Field(default=False, env="USE_AI_RECOMMENDATIONS")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")

    # SMS API (для верификации)
    SMS_API_KEY: Optional[str] = Field(default=None, env="SMS_API_KEY")
    SMS_PROVIDER: str = Field(default="twilio", env="SMS_PROVIDER")

    # Email
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    EMAIL_FROM: Optional[str] = Field(default=None, env="EMAIL_FROM")

    # Payments (Telegram)
    PAYMENT_PROVIDER_TOKEN: Optional[str] = Field(default=None, env="PAYMENT_PROVIDER_TOKEN")

    # Парсинг
    AVITO_PARSER_ENABLED: bool = Field(default=False, env="AVITO_PARSER_ENABLED")
    AVITO_API_KEY: Optional[str] = Field(default=None, env="AVITO_API_KEY")

    # Безопасность
    SECRET_KEY: str = Field(default="change-me-in-production", env="SECRET_KEY")
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    MAX_REQUESTS_PER_MINUTE: int = Field(default=20, env="MAX_REQUESTS_PER_MINUTE")

    # Геймификация
    GAMIFICATION_ENABLED: bool = Field(default=True, env="GAMIFICATION_ENABLED")
    REFERRAL_BONUS: int = Field(default=10, env="REFERRAL_BONUS")

    # Модерация
    AUTO_MODERATION: bool = Field(default=True, env="AUTO_MODERATION")
    MANUAL_MODERATION_REQUIRED: bool = Field(default=False, env="MANUAL_MODERATION_REQUIRED")

    # Аналитика
    ANALYTICS_ENABLED: bool = Field(default=True, env="ANALYTICS_ENABLED")

    # Локализация
    DEFAULT_LANGUAGE: str = Field(default="ru", env="DEFAULT_LANGUAGE")
    SUPPORTED_LANGUAGES: List[str] = Field(
        default_factory=lambda: ["ru", "en", "lv"],
        env="SUPPORTED_LANGUAGES"
    )

    # Бизнес-логика
    MAX_PHOTOS_PER_AD: int = Field(default=3, env="MAX_PHOTOS_PER_AD")
    AD_AUTO_DELETE_DAYS: int = Field(default=30, env="AD_AUTO_DELETE_DAYS")
    CHAT_DELETE_AFTER_SWAP_DAYS: int = Field(default=10, env="CHAT_DELETE_AFTER_SWAP_DAYS")
    DEFAULT_SEARCH_RADIUS_KM: int = Field(default=10, env="DEFAULT_SEARCH_RADIUS_KM")
    MAX_ACTIVE_ADS_PER_USER: int = Field(default=10, env="MAX_ACTIVE_ADS_PER_USER")

    # Монетизация
    PREMIUM_ENABLED: bool = Field(default=True, env="PREMIUM_ENABLED")
    PREMIUM_PRICE: int = Field(default=199, env="PREMIUM_PRICE")
    AD_BOOST_PRICE: int = Field(default=49, env="AD_BOOST_PRICE")

    # GitHub
    GITHUB_REPO: str = Field(
        default="https://github.com/yourusername/swap_bot",
        env="GITHUB_REPO"
    )

    # Админка
    ADMIN_PANEL_ENABLED: bool = Field(default=True, env="ADMIN_PANEL_ENABLED")
    ADMIN_PANEL_PORT: int = Field(default=8000, env="ADMIN_PANEL_PORT")

    # Celery
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        env="CELERY_BROKER_URL"
    )

    # Логирование
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[Path] = Field(default=None, env="LOG_FILE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Не падать если .env не найден
        extra = "ignore"


class Constants:
    """Бизнес-константы"""

    # Рейтинг
    DEFAULT_RATING = 5.0
    MIN_RATING = 1
    MAX_RATING = 5

    # Категории
    CATEGORIES = {
        "electronics": {
            "title_ru": "Электроника",
            "title_en": "Electronics",
            "title_lv": "Elektronika",
            "emoji": "📱",
            "requires_price": True,
            "description_ru": "Телефоны, планшеты, компьютеры",
            "description_en": "Phones, tablets, computers",
            "description_lv": "Tālruņi, planšetdatori, datori"
        },
        "clothing": {
            "title_ru": "Одежда и обувь",
            "title_en": "Clothing & Shoes",
            "title_lv": "Apģērbs un apavi",
            "emoji": "👕",
            "requires_price": True,
            "description_ru": "Мужская, женская, детская одежда",
            "description_en": "Men's, women's, children's clothing",
            "description_lv": "Vīriešu, sieviešu, bērnu apģērbs"
        },
        "home": {
            "title_ru": "Для дома",
            "title_en": "Home & Garden",
            "title_lv": "Mājai un dārzam",
            "emoji": "🏠",
            "requires_price": True,
            "description_ru": "Мебель, декор, бытовая техника",
            "description_en": "Furniture, decor, appliances",
            "description_lv": "Mēbeles, dekori, sadzīves tehnika"
        },
        "hobbies": {
            "title_ru": "Хобби и отдых",
            "title_en": "Hobbies & Leisure",
            "title_lv": "Vaļasprieki un atpūta",
            "emoji": "🎨",
            "requires_price": True,
            "description_ru": "Спорт, музыка, коллекционирование",
            "description_en": "Sports, music, collectibles",
            "description_lv": "Sports, mūzika, kolekcionēšana"
        },
        "free": {
            "title_ru": "Отдам даром",
            "title_en": "Free Stuff",
            "title_lv": "Atdodu velti",
            "emoji": "🎁",
            "requires_price": False,
            "description_ru": "Бесплатные товары",
            "description_en": "Free items",
            "description_lv": "Bezmaksas lietas"
        },
    }

    # Статусы объявлений
    AD_STATUS_ACTIVE = 1
    AD_STATUS_INACTIVE = 0
    AD_STATUS_DELETED = -1
    AD_STATUS_MODERATION = 2

    # Статусы обменов
    SWAP_STATUS_PROPOSED = "proposed"
    SWAP_STATUS_ACCEPTED = "accepted"
    SWAP_STATUS_MEETING_SCHEDULED = "meeting_scheduled"
    SWAP_STATUS_COMPLETED = "completed"
    SWAP_STATUS_CANCELLED = "cancelled"
    SWAP_STATUS_PENDING = "pending"

    # Лимиты
    MAX_TEXT_LEN = 1000
    MAX_NAME_LEN = 100
    MAX_TITLE_LEN = 150
    MAX_DESC_LEN = 500

    # Сообщения
    MESSAGES = {}
    CATEGORY_BUTTONS = {}
    TEXT_TO_CATEGORY = {}

    @classmethod
    def _categories_for_bot(cls):
        d = {}
        for k, v in cls.CATEGORIES.items():
            d[k] = {
                **v,
                "title": f"{v['emoji']} {v['title_ru']}",
                "description": v["description_ru"],
            }
        return d

    @classmethod
    def _messages_for_bot(cls):
        return {
            "welcome": "👋 <b>Добро пожаловать в SwapBot!</b>\n\n🔄 Площадка для обмена вещами.\n📍 Укажите местоположение для поиска рядом с вами.",
            "location_saved": "✅ Местоположение сохранено!",
            "ad_created": "✅ Объявление создано!",
            "no_ads_found": "😔 Больше нет объявлений",
            "swap_sent": "✅ Предложение обмена отправлено!",
            "error": "❌ Произошла ошибка",
        }


# Инициализация настроек
settings = Settings()
constants = Constants()

# Совместимость с handlers/keyboards
constants.CATEGORIES = constants._categories_for_bot()
constants.MESSAGES = constants._messages_for_bot()
constants.CATEGORY_BUTTONS = {k: v["title"] for k, v in constants.CATEGORIES.items()}
constants.TEXT_TO_CATEGORY = {v["title"]: k for k, v in constants.CATEGORIES.items()}


def get_db_path() -> str:
    """Получение пути к БД"""
    p = settings.DB_PATH
    if p.startswith("/") or ":" in p:
        return p
    root = Path(__file__).resolve().parent.parent
    return str(root / p)


# Парсинг ADMIN_IDS
def get_admin_ids() -> list:
    """Парсинг списка админов из строки"""
    if not settings.ADMIN_IDS:
        return []
    try:
        return [int(x.strip()) for x in settings.ADMIN_IDS.split(",") if x.strip()]
    except:
        return []


# Обновляем settings.ADMIN_IDS
settings.ADMIN_IDS = get_admin_ids()