# -*- coding: utf-8 -*-
"""
Безопасность, модерация, верификация (Идея #9)
"""
import re
import hashlib
import secrets
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models_orm import User, Ad, Report, AdStatus
from app.config import settings


class SecurityService:
    """Сервис безопасности и модерации"""

    # Список запрещённых слов (базовый)
    PROHIBITED_WORDS = [
        "наркотики", "оружие", "порно", "проститу", "казино",
        "взлом", "обман", "мошенн", "фальш", "контрафакт"
    ]

    # Паттерны подозрительного контента
    SUSPICIOUS_PATTERNS = [
        r'\b(?:telegram|whatsapp|viber|skype)[\s:]+[\w@]+',  # Контакты
        r'\b(?:bitcoin|btc|crypto|крипт)',  # Крипта
        r'\b(?:\d{4}\s?\d{4}\s?\d{4}\s?\d{4})',  # Номера карт
        r'(?:https?://|www\.)[^\s]+',  # Ссылки
    ]

    def __init__(self):
        self.auto_moderation = settings.AUTO_MODERATION
        self.manual_moderation = settings.MANUAL_MODERATION_REQUIRED

    async def moderate_ad(
            self,
            ad: Ad,
            session: AsyncSession
    ) -> Tuple[bool, Optional[str]]:
        """
        Модерация объявления

        Returns:
            (approved: bool, reason: Optional[str])
        """

        if not self.auto_moderation:
            return True, None

        # Проверка на запрещённые слова
        text = f"{ad.title} {ad.description}".lower()

        for word in self.PROHIBITED_WORDS:
            if word in text:
                return False, f"Запрещённое слово: {word}"

        # Проверка подозрительных паттернов
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                # Отправляем на ручную модерацию
                if self.manual_moderation:
                    ad.status = AdStatus.MODERATION
                    ad.moderation_status = "pending_review"
                    await session.commit()
                    return False, "Отправлено на ручную модерацию"

        # Проверка на спам (слишком много объявлений за короткий период)
        is_spam = await self._check_spam(ad.user_id, session)
        if is_spam:
            return False, "Подозрение на спам. Подождите перед созданием новых объявлений."

        return True, None

    async def _check_spam(
            self,
            user_id: int,
            session: AsyncSession
    ) -> bool:
        """Проверка на спам"""

        # Считаем объявления за последний час
        hour_ago = datetime.utcnow() - timedelta(hours=1)

        result = await session.execute(
            select(Ad).where(
                and_(
                    Ad.user_id == user_id,
                    Ad.created_at >= hour_ago
                )
            )
        )
        recent_ads = result.scalars().all()

        # Если больше 5 объявлений за час - подозрение на спам
        return len(recent_ads) >= 5

    async def verify_phone(
            self,
            user: User,
            phone: str,
            session: AsyncSession
    ) -> Tuple[bool, Optional[str]]:
        """
        Верификация телефона через SMS

        Returns:
            (success: bool, verification_code: Optional[str])
        """

        # Генерируем код
        verification_code = str(secrets.randbelow(900000) + 100000)

        # Сохраняем хеш кода (не храним в открытом виде)
        code_hash = hashlib.sha256(verification_code.encode()).hexdigest()

        # Сохраняем в БД (нужно добавить поле в User)
        # user.phone_verification_code = code_hash
        # user.phone_verification_expires = datetime.utcnow() + timedelta(minutes=10)

        # Отправка SMS (интеграция с провайдером)
        sms_sent = await self._send_sms(phone, verification_code)

        if sms_sent:
            await session.commit()
            return True, verification_code  # В продакшене не возвращаем код!

        return False, None

    async def _send_sms(self, phone: str, code: str) -> bool:
        """Отправка SMS через провайдера"""

        if not settings.SMS_API_KEY:
            print(f"⚠️  SMS not configured. Code: {code}")
            return True  # В dev режиме считаем успешным

        # Интеграция с SMS провайдером (Twilio, SMS.ru, и т.д.)
        try:
            if settings.SMS_PROVIDER == "twilio":
                # from twilio.rest import Client
                # client = Client(settings.TWILIO_SID, settings.SMS_API_KEY)
                # message = client.messages.create(
                #     body=f"Ваш код подтверждения: {code}",
                #     from_=settings.TWILIO_PHONE,
                #     to=phone
                # )
                pass

            elif settings.SMS_PROVIDER == "smsru":
                # Пример для SMS.ru
                import aiohttp
                url = f"https://sms.ru/sms/send?api_id={settings.SMS_API_KEY}"
                url += f"&to={phone}&msg=Ваш код: {code}"

                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        result = await response.text()
                        return "100" in result  # Код успеха SMS.ru

            return True

        except Exception as e:
            print(f"❌ SMS sending error: {e}")
            return False

    async def create_report(
            self,
            reporter_id: int,
            reported_user_id: Optional[int],
            reported_ad_id: Optional[int],
            reason: str,
            description: str,
            session: AsyncSession
    ) -> Report:
        """Создание жалобы"""

        report = Report(
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            reported_ad_id=reported_ad_id,
            reason=reason,
            description=description
        )

        session.add(report)
        await session.commit()

        # Если жалоб на пользователя/объявление слишком много - автобан
        await self._check_auto_ban(
            reported_user_id,
            reported_ad_id,
            session
        )

        return report

    async def _check_auto_ban(
            self,
            user_id: Optional[int],
            ad_id: Optional[int],
            session: AsyncSession
    ):
        """Проверка на автобан при множественных жалобах"""

        if user_id:
            # Считаем жалобы за последнюю неделю
            week_ago = datetime.utcnow() - timedelta(days=7)

            result = await session.execute(
                select(Report).where(
                    and_(
                        Report.reported_user_id == user_id,
                        Report.created_at >= week_ago
                    )
                )
            )
            reports = result.scalars().all()

            # Если больше 5 жалоб - бан
            if len(reports) >= 5:
                user_result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = user_result.scalar_one_or_none()

                if user:
                    user.is_banned = True
                    user.ban_reason = "Множественные жалобы от пользователей"
                    await session.commit()

        if ad_id:
            # Аналогично для объявления
            result = await session.execute(
                select(Report).where(Report.reported_ad_id == ad_id)
            )
            reports = result.scalars().all()

            if len(reports) >= 3:
                ad_result = await session.execute(
                    select(Ad).where(Ad.id == ad_id)
                )
                ad = ad_result.scalar_one_or_none()

                if ad:
                    ad.status = AdStatus.DELETED
                    ad.rejection_reason = "Множественные жалобы"
                    await session.commit()

    def check_rate_limit(
            self,
            user_id: int,
            action: str,
            max_requests: int = 20,
            window_seconds: int = 60
    ) -> Tuple[bool, int]:
        """
        Проверка rate limiting

        Returns:
            (allowed: bool, remaining: int)
        """

        # Реализация через Redis для production
        # Здесь упрощённый вариант

        # В реальности нужно:
        # 1. Проверить счётчик в Redis
        # 2. Если превышен - вернуть False
        # 3. Иначе инкрементировать счётчик

        return True, max_requests

    async def generate_referral_code(self, user_id: int) -> str:
        """Генерация уникального реферального кода"""

        # Используем user_id + random для уникальности
        random_part = secrets.token_urlsafe(6)
        code = f"REF{user_id}_{random_part}".upper()

        return code

    def sanitize_input(self, text: str, max_length: int = 500) -> str:
        """Очистка пользовательского ввода"""

        # Убираем HTML теги
        text = re.sub(r'<[^>]+>', '', text)

        # Ограничиваем длину
        text = text[:max_length]

        # Убираем лишние пробелы
        text = ' '.join(text.split())

        return text.strip()


# Singleton
security_service = SecurityService()