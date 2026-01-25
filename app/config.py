# -*- coding: utf-8 -*-
"""
Полная конфигурация бота с поддержкой всех фич
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения"""

    # Telegram
    BOT_TOKEN: str = Field(..., env="BOT_TOKEN")
    ADMIN_IDS: list[int] = Field(default_factory=list, env="ADMIN_IDS")

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
    USE_AI_RECOMMENDATIONS: bool = Field(default=True, env="USE_AI_RECOMMENDATIONS")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")

    # SMS API (для верификации)
    SMS_API_KEY: Optional[str] = Field(default=None, env="SMS_API_KEY")
    SMS_PROVIDER: str = Field(default="twilio", env="SMS_PROVIDER")  # twilio, smsru, etc

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
    REFERRAL_BONUS: int = Field(default=10, env="REFERRAL_BONUS")  # бонусные баллы

    # Модерация
    AUTO_MODERATION: bool = Field(default=True, env="AUTO_MODERATION")
    MANUAL_MODERATION_REQUIRED: bool = Field(default=False, env="MANUAL_MODERATION_REQUIRED")

    # Аналитика
    ANALYTICS_ENABLED: bool = Field(default=True, env="ANALYTICS_ENABLED")

    # Локализация
    DEFAULT_LANGUAGE: str = Field(default="ru", env="DEFAULT_LANGUAGE")
    SUPPORTED_LANGUAGES: list[str] = Field(
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
    PREMIUM_PRICE: int = Field(default=199, env="PREMIUM_PRICE")  # в рублях
    AD_BOOST_PRICE: int = Field(default=49, env="AD_BOOST_PRICE")

    # GitHub (для помощи проекту)
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
        env_file = str(Path(__file__).resolve().parent.parent / ".env")
        env_file_encoding = "utf-8"


# Константы
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

    # Уровни пользователей (геймификация)
    USER_LEVELS = {
        1: {"name_ru": "Новичок", "name_en": "Beginner", "swaps_required": 0, "perks": []},
        2: {"name_ru": "Обменщик", "name_en": "Swapper", "swaps_required": 3, "perks": ["free_boost"]},
        3: {"name_ru": "Профи", "name_en": "Pro", "swaps_required": 10, "perks": ["free_boost", "priority_search"]},
        4: {"name_ru": "Эксперт", "name_en": "Expert", "swaps_required": 25,
            "perks": ["free_boost", "priority_search", "verified_badge"]},
        5: {"name_ru": "Мастер", "name_en": "Master", "swaps_required": 50, "perks": ["all_premium_features"]},
    }

    # Достижения
    ACHIEVEMENTS = {
        "first_swap": {"name_ru": "Первый обмен", "name_en": "First Swap", "emoji": "🎉", "points": 10},
        "10_swaps": {"name_ru": "10 обменов", "name_en": "10 Swaps", "emoji": "🔥", "points": 50},
        "100_views": {"name_ru": "100 просмотров", "name_en": "100 Views", "emoji": "👁", "points": 25},
        "verified": {"name_ru": "Верифицирован", "name_en": "Verified", "emoji": "✅", "points": 30},
        "helpful": {"name_ru": "Полезный", "name_en": "Helpful", "emoji": "💚", "points": 20},
    }

    # Радиус поиска
    SEARCH_RADIUS_OPTIONS = [1, 3, 5, 10, 25, 50, 100]

    # Сообщения
    MESSAGES = {
        "ru": {
            "welcome": "👋 Добро пожаловать в SwapBot!",
            "ad_created": "✅ Объявление создано!",
            "swap_proposed": "✅ Предложение обмена отправлено!",
            "error": "❌ Произошла ошибка",
            "no_ads": "😔 Больше нет объявлений",
        },
        "en": {
            "welcome": "👋 Welcome to SwapBot!",
            "ad_created": "✅ Ad created!",
            "swap_proposed": "✅ Swap proposal sent!",
            "error": "❌ An error occurred",
            "no_ads": "😔 No more ads",
        },
        "lv": {
            "welcome": "👋 Laipni lūdzam SwapBot!",
            "ad_created": "✅ Sludinājums izveidots!",
            "swap_proposed": "✅ Maiņas piedāvājums nosūtīts!",
            "error": "❌ Radās kļūda",
            "no_ads": "😔 Nav vairāk sludinājumu",
        }
    }

    # Для handlers/keyboards: плоские ключи и "title"
    MAX_TEXT_LEN = 1000
    MAX_NAME_LEN = 100
    MAX_TITLE_LEN = 150
    MAX_DESC_LEN = 500
    SWAP_STATUS_PENDING = "pending"

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
        ru = cls.MESSAGES["ru"]
        return {
            "welcome": "👋 <b>Добро пожаловать в SwapBot!</b>\n\n🔄 Площадка для обмена вещами.\n📍 Укажите местоположение для поиска рядом с вами.",
            "location_saved": "✅ Местоположение сохранено!",
            "ad_created": ru["ad_created"],
            "no_ads_found": ru["no_ads"],
            "swap_sent": ru["swap_proposed"],
            "error": ru["error"],
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
    p = settings.DB_PATH
    if p.startswith("/") or ":" in p:
        return p
    root = Path(__file__).resolve().parent.parent
    return str(root / p)


# Проверка обязательных настроек
def validate_settings():
    """Проверка критичных настроек"""
    if not settings.BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required!")

    if settings.PREMIUM_ENABLED and not settings.PAYMENT_PROVIDER_TOKEN:
        print("⚠️  WARNING: Premium enabled but PAYMENT_PROVIDER_TOKEN not set")

    if settings.USE_AI_RECOMMENDATIONS and not settings.OPENAI_API_KEY:
        print("⚠️  WARNING: AI recommendations enabled but OPENAI_API_KEY not set")

    if settings.AVITO_PARSER_ENABLED and not settings.AVITO_API_KEY:
        print("⚠️  WARNING: Avito parser enabled but AVITO_API_KEY not set")

    # Создаём директории
    settings.MEDIA_PATH.mkdir(exist_ok=True)

    print("✅ Configuration validated successfully")


if __name__ == "__main__":
    validate_settings()