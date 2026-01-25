# -*- coding: utf-8 -*-
"""
Полная модель базы данных с поддержкой всех 22 фич
Используем SQLAlchemy для масштабируемости
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import (
    BigInteger, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, JSON, Enum as SQLEnum, Index, CheckConstraint,
    UniqueConstraint, func
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех моделей"""
    pass


# ==================== ENUMS ====================

class AdStatus(enum.Enum):
    """Статусы объявлений"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    MODERATION = "moderation"
    REJECTED = "rejected"


class SwapStatus(enum.Enum):
    """Статусы обменов"""
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    MEETING_SCHEDULED = "meeting_scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class UserRole(enum.Enum):
    """Роли пользователей"""
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class NotificationType(enum.Enum):
    """Типы уведомлений"""
    NEW_LIKE = "new_like"
    NEW_MESSAGE = "new_message"
    SWAP_ACCEPTED = "swap_accepted"
    MEETING_REMINDER = "meeting_reminder"
    ACHIEVEMENT = "achievement"
    SYSTEM = "system"


# ==================== MODELS ====================

class User(Base):
    """Модель пользователя (Идея #2: Система репутации)"""
    __tablename__ = "users"

    # Основные поля
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram ID
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), default="Пользователь")
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Местоположение
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Репутация и уровень (Идея #2, #6: Геймификация)
    rating: Mapped[float] = mapped_column(Float, default=5.0)
    total_swaps: Mapped[int] = mapped_column(Integer, default=0)
    successful_swaps: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    experience_points: Mapped[int] = mapped_column(Integer, default=0)

    # Верификация (Идея #2)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER)

    # Premium (Идея #10: Монетизация)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Настройки (Идея #13: Мультиязычность)
    language: Mapped[str] = mapped_column(String(5), default="ru")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=False)

    # Геймификация (Идея #6)
    achievements: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    badges: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Реферальная программа (Идея #6)
    referral_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    referred_by_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    referral_count: Mapped[int] = mapped_column(Integer, default=0)
    bonus_points: Mapped[int] = mapped_column(Integer, default=0)

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ads: Mapped[List["Ad"]] = relationship("Ad", back_populates="user", foreign_keys="Ad.user_id")
    sent_ratings: Mapped[List["Rating"]] = relationship("Rating", back_populates="from_user",
                                                        foreign_keys="Rating.from_user_id")
    received_ratings: Mapped[List["Rating"]] = relationship("Rating", back_populates="to_user",
                                                            foreign_keys="Rating.to_user_id")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="user")

    # Индексы
    __table_args__ = (
        Index("idx_user_username", "username"),
        Index("idx_user_rating", "rating"),
        Index("idx_user_level", "level"),
        Index("idx_user_location", "latitude", "longitude"),
    )


class Ad(Base):
    """Модель объявления (Идея #1, #3: Умный поиск)"""
    __tablename__ = "ads"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    # Контент
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Медиа (Идея #17: До 3 фото)
    photos: Mapped[Optional[dict]] = mapped_column(JSON,
                                                   default=dict)  # {"main": "file_id", "additional": ["id1", "id2"]}

    # Местоположение
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Статус
    status: Mapped[AdStatus] = mapped_column(SQLEnum(AdStatus), default=AdStatus.ACTIVE)
    moderation_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Статистика (Идея #8: Аналитика)
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    messages_count: Mapped[int] = mapped_column(Integer, default=0)

    # AI и поиск (Идея #1: AI рекомендации)
    embedding: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Векторное представление
    tags: Mapped[Optional[dict]] = mapped_column(JSON, default=list)  # Автогенерированные теги

    # Монетизация (Идея #10)
    is_boosted: Mapped[bool] = mapped_column(Boolean, default=False)
    boost_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_premium_ad: Mapped[bool] = mapped_column(Boolean, default=False)

    # Условия обмена (Идея #20: Обмен + доплата)
    allows_money_addition: Mapped[bool] = mapped_column(Boolean, default=False)
    max_money_addition: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Временный обмен (Идея #21)
    is_temporary_swap: Mapped[bool] = mapped_column(Boolean, default=False)
    swap_duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    boosted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delete_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="ads", foreign_keys=[user_id])
    likes: Mapped[List["Like"]] = relationship("Like", back_populates="ad")
    views_history: Mapped[List["AdView"]] = relationship("AdView", back_populates="ad")

    # Индексы
    __table_args__ = (
        Index("idx_ad_category", "category"),
        Index("idx_ad_status", "status"),
        Index("idx_ad_user", "user_id"),
        Index("idx_ad_location", "latitude", "longitude"),
        Index("idx_ad_created", "created_at"),
        Index("idx_ad_boosted", "is_boosted", "boost_until"),
    )


class Like(Base):
    """Модель лайков (упрощённая система обмена)"""
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    ad_id: Mapped[int] = mapped_column(Integer, ForeignKey("ads.id"), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Статус
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User")
    ad: Mapped["Ad"] = relationship("Ad", back_populates="likes")

    __table_args__ = (
        UniqueConstraint("user_id", "ad_id", name="uq_like_user_ad"),
        Index("idx_like_ad", "ad_id"),
        Index("idx_like_user", "user_id"),
    )


class Swap(Base):
    """Модель обмена (Идея #5: Система обменов)"""
    __tablename__ = "swaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Участники
    user1_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    user2_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    # Объявления
    ad1_id: Mapped[int] = mapped_column(Integer, ForeignKey("ads.id"), nullable=False)
    ad2_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ads.id"), nullable=True)

    # Статус
    status: Mapped[SwapStatus] = mapped_column(SQLEnum(SwapStatus), default=SwapStatus.PROPOSED)

    # Обмен + доплата (Идея #20)
    money_addition: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    who_pays_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)

    # Встреча (Идея #5)
    meeting_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    meeting_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    meeting_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    meeting_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Подтверждение
    user1_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    user2_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Временный обмен (Идея #21)
    is_temporary: Mapped[bool] = mapped_column(Boolean, default=False)
    return_by: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user1: Mapped["User"] = relationship("User", foreign_keys=[user1_id])
    user2: Mapped["User"] = relationship("User", foreign_keys=[user2_id])

    __table_args__ = (
        Index("idx_swap_users", "user1_id", "user2_id"),
        Index("idx_swap_status", "status"),
    )


class Chat(Base):
    """Модель чата (Идея #4: Встроенный чат)"""
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Участники
    user1_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    user2_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    # Контекст
    ad_id: Mapped[int] = mapped_column(Integer, ForeignKey("ads.id"), nullable=False)
    swap_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("swaps.id"), nullable=True)

    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Автоудаление (Идея #4)
    delete_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_message_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="chat")

    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", "ad_id", name="uq_chat_users_ad"),
        Index("idx_chat_users", "user1_id", "user2_id"),
    )


class ChatMessage(Base):
    """Сообщение в чате"""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    # Контент
    message: Mapped[str] = mapped_column(Text, nullable=False)
    media_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    media_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # photo, voice, document

    # Статус
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")

    __table_args__ = (
        Index("idx_message_chat", "chat_id"),
        Index("idx_message_created", "created_at"),
    )


class Rating(Base):
    """Модель рейтинга (Идея #2: Система репутации)"""
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    from_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    to_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    swap_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("swaps.id"), nullable=True)

    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    from_user: Mapped["User"] = relationship("User", foreign_keys=[from_user_id], back_populates="sent_ratings")
    to_user: Mapped["User"] = relationship("User", foreign_keys=[to_user_id], back_populates="received_ratings")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        UniqueConstraint("from_user_id", "to_user_id", "swap_id", name="uq_rating_users_swap"),
        Index("idx_rating_to_user", "to_user_id"),
    )


class Favorite(Base):
    """Избранные объявления (Идея #3)"""
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    ad_id: Mapped[int] = mapped_column(Integer, ForeignKey("ads.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="favorites")

    __table_args__ = (
        UniqueConstraint("user_id", "ad_id", name="uq_favorite_user_ad"),
        Index("idx_favorite_user", "user_id"),
    )


class AdView(Base):
    """История просмотров (Идея #8: Аналитика)"""
    __tablename__ = "ad_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad_id: Mapped[int] = mapped_column(Integer, ForeignKey("ads.id"), nullable=False)
    viewer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    ad: Mapped["Ad"] = relationship("Ad", back_populates="views_history")

    __table_args__ = (
        Index("idx_view_ad", "ad_id"),
        Index("idx_view_date", "created_at"),
    )


class SavedSearch(Base):
    """Сохранённые поиски (Идея #3)"""
    __tablename__ = "saved_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    filters: Mapped[dict] = mapped_column(JSON, nullable=False)  # Сохранённые фильтры

    notify_on_new: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_saved_search_user", "user_id"),
    )


class Notification(Base):
    """Уведомления (Идея #12)"""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Доп. данные

    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_notification_user", "user_id"),
        Index("idx_notification_unread", "user_id", "is_read"),
    )


class Report(Base):
    """Жалобы (Идея #9: Безопасность)"""
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    # Может быть жалоба на пользователя или объявление
    reported_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    reported_ad_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ads.id"), nullable=True)

    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Модерация
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    moderator_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_report_unprocessed", "is_processed"),
    )


class Payment(Base):
    """Платежи (Идея #10: Монетизация)"""
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    type: Mapped[str] = mapped_column(String(50), nullable=False)  # premium, boost, etc
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")

    # Telegram Payment API
    telegram_payment_charge_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_payment_charge_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, success, failed

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_payment_user", "user_id"),
        Index("idx_payment_status", "status"),
    )


class Analytics(Base):
    """Аналитика (Идея #8, #15: Админка)"""
    __tablename__ = "analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Метрики
    total_users: Mapped[int] = mapped_column(Integer, default=0)
    new_users: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)

    total_ads: Mapped[int] = mapped_column(Integer, default=0)
    new_ads: Mapped[int] = mapped_column(Integer, default=0)

    total_swaps: Mapped[int] = mapped_column(Integer, default=0)
    completed_swaps: Mapped[int] = mapped_column(Integer, default=0)

    total_revenue: Mapped[int] = mapped_column(Integer, default=0)

    # Детализация
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_analytics_date", "date"),
    )


# init_db для SQLAlchemy — в отдельном месте при использовании ORM.
# Бот использует app.database.db.init_db (aiosqlite).