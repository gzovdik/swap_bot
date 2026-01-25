# -*- coding: utf-8 -*-
"""
Геймификация: уровни, достижения, реферальная программа (Идея #6)
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models_orm import User, Swap, Ad, Rating
from app.config import settings


class GamificationService:
    """Сервис геймификации"""

    # Достижения
    ACHIEVEMENTS = {
        "first_swap": {
            "name_ru": "Первый обмен",
            "name_en": "First Swap",
            "description_ru": "Совершите первый обмен",
            "emoji": "🎉",
            "points": 10
        },
        "swap_master_3": {
            "name_ru": "Обменщик",
            "emoji": "🔥",
            "points": 25,
            "requirement": lambda user: user.successful_swaps >= 3
        },
        "swap_master_10": {
            "name_ru": "Профи обменов",
            "emoji": "⭐",
            "points": 50,
            "requirement": lambda user: user.successful_swaps >= 10
        },
        "swap_master_50": {
            "name_ru": "Мастер обменов",
            "emoji": "👑",
            "points": 200,
            "requirement": lambda user: user.successful_swaps >= 50
        },
        "popular_ad": {
            "name_ru": "Популярный",
            "emoji": "👁",
            "description_ru": "100 просмотров объявления",
            "points": 25
        },
        "verified": {
            "name_ru": "Верифицирован",
            "emoji": "✅",
            "description_ru": "Подтвердите телефон",
            "points": 30
        },
        "five_star": {
            "name_ru": "5 звёзд",
            "emoji": "⭐",
            "description_ru": "Получите рейтинг 5.0 с 10+ отзывами",
            "points": 50
        },
        "helpful": {
            "name_ru": "Полезный",
            "emoji": "💚",
            "description_ru": "Помогите 5 пользователям",
            "points": 20
        },
        "referral_5": {
            "name_ru": "Амбассадор",
            "emoji": "🎯",
            "description_ru": "Пригласите 5 друзей",
            "points": 100
        },
        "early_adopter": {
            "name_ru": "Первопроходец",
            "emoji": "🚀",
            "description_ru": "Один из первых 100 пользователей",
            "points": 50
        },
    }

    async def check_and_award_achievements(
            self,
            user: User,
            session: AsyncSession
    ) -> List[Dict]:
        """Проверка и выдача достижений"""

        if not user.achievements:
            user.achievements = {}

        new_achievements = []

        # Проверяем каждое достижение
        for achievement_id, achievement_data in self.ACHIEVEMENTS.items():
            # Если уже есть, пропускаем
            if achievement_id in user.achievements:
                continue

            # Проверяем условие
            if await self._check_achievement_requirement(
                    achievement_id,
                    user,
                    session
            ):
                # Выдаём достижение
                user.achievements[achievement_id] = {
                    "unlocked_at": datetime.utcnow().isoformat(),
                    "points": achievement_data["points"]
                }

                # Добавляем очки опыта
                user.experience_points += achievement_data["points"]

                new_achievements.append({
                    "id": achievement_id,
                    **achievement_data
                })

        # Проверяем повышение уровня
        level_up = await self._check_level_up(user)

        await session.commit()

        return new_achievements, level_up

    async def _check_achievement_requirement(
            self,
            achievement_id: str,
            user: User,
            session: AsyncSession
    ) -> bool:
        """Проверка условия достижения"""

        # Первый обмен
        if achievement_id == "first_swap":
            return user.successful_swaps >= 1

        # Обменщик (3 обмена)
        elif achievement_id == "swap_master_3":
            return user.successful_swaps >= 3

        # Профи (10 обменов)
        elif achievement_id == "swap_master_10":
            return user.successful_swaps >= 10

        # Мастер (50 обменов)
        elif achievement_id == "swap_master_50":
            return user.successful_swaps >= 50

        # Популярное объявление
        elif achievement_id == "popular_ad":
            result = await session.execute(
                select(Ad).where(
                    and_(
                        Ad.user_id == user.id,
                        Ad.views >= 100
                    )
                )
            )
            return result.scalar_one_or_none() is not None

        # Верификация
        elif achievement_id == "verified":
            return user.phone_verified

        # 5 звёзд
        elif achievement_id == "five_star":
            result = await session.execute(
                select(func.count(Rating.id)).where(
                    Rating.to_user_id == user.id
                )
            )
            rating_count = result.scalar()
            return user.rating >= 5.0 and rating_count >= 10

        # Реферальная программа
        elif achievement_id == "referral_5":
            return user.referral_count >= 5

        # Первопроходец
        elif achievement_id == "early_adopter":
            result = await session.execute(
                select(func.count(User.id))
            )
            total_users = result.scalar()
            return total_users <= 100

        return False

    async def _check_level_up(self, user: User) -> Optional[Dict]:
        """Проверка повышения уровня"""

        # Таблица уровней (опыт → уровень)
        level_thresholds = {
            1: 0,
            2: 50,
            3: 150,
            4: 300,
            5: 500,
            6: 800,
            7: 1200,
            8: 1700,
            9: 2300,
            10: 3000,
        }

        current_level = user.level
        xp = user.experience_points

        # Находим новый уровень
        new_level = current_level
        for level, threshold in level_thresholds.items():
            if xp >= threshold:
                new_level = level

        if new_level > current_level:
            user.level = new_level

            return {
                "old_level": current_level,
                "new_level": new_level,
                "perks": self._get_level_perks(new_level)
            }

        return None

    def _get_level_perks(self, level: int) -> List[str]:
        """Получение привилегий уровня"""
        perks_map = {
            1: [],
            2: ["🎁 Бесплатное поднятие 1 раз в неделю"],
            3: ["🎁 2 бесплатных поднятия в неделю"],
            4: ["⭐ Значок верифицированного", "🎁 3 поднятия в неделю"],
            5: ["👑 VIP значок", "🎯 Приоритет в поиске", "🎁 5 поднятий"],
            6: ["💎 Премиум на месяц бесплатно"],
            7: ["🔥 Выделение объявлений цветом"],
            8: ["⚡ Безлимитные поднятия"],
            9: ["🎖 Статус легенды", "💰 Скидка 50% на все услуги"],
            10: ["👑 Пожизненный Premium", "🌟 Уникальный значок"],
        }

        return perks_map.get(level, [])

    async def process_referral(
            self,
            referrer_code: str,
            new_user_id: int,
            session: AsyncSession
    ) -> Tuple[bool, Optional[User]]:
        """Обработка реферальной ссылки"""

        # Находим пригласившего
        result = await session.execute(
            select(User).where(User.referral_code == referrer_code)
        )
        referrer = result.scalar_one_or_none()

        if not referrer:
            return False, None

        # Обновляем данные пригласившего
        referrer.referral_count += 1
        referrer.bonus_points += settings.REFERRAL_BONUS
        referrer.experience_points += settings.REFERRAL_BONUS

        # Обновляем данные нового пользователя
        result = await session.execute(
            select(User).where(User.id == new_user_id)
        )
        new_user = result.scalar_one_or_none()

        if new_user:
            new_user.referred_by_id = referrer.id
            new_user.bonus_points += settings.REFERRAL_BONUS

        await session.commit()

        return True, referrer

    async def get_user_stats(
            self,
            user: User,
            session: AsyncSession
    ) -> Dict:
        """Получение полной статистики пользователя"""

        # Считаем просмотры объявлений
        result = await session.execute(
            select(func.sum(Ad.views)).where(Ad.user_id == user.id)
        )
        total_views = result.scalar() or 0

        # Прогресс до следующего уровня
        next_level_xp = self._get_xp_for_next_level(user.level)
        current_level_xp = self._get_xp_for_level(user.level)

        progress = (
                (user.experience_points - current_level_xp) /
                (next_level_xp - current_level_xp) * 100
        )

        return {
            "level": user.level,
            "experience_points": user.experience_points,
            "next_level_xp": next_level_xp,
            "progress_to_next_level": round(progress, 1),
            "total_swaps": user.total_swaps,
            "successful_swaps": user.successful_swaps,
            "rating": user.rating,
            "total_views": total_views,
            "achievements": len(user.achievements or {}),
            "referrals": user.referral_count,
            "bonus_points": user.bonus_points,
            "perks": self._get_level_perks(user.level)
        }

    def _get_xp_for_level(self, level: int) -> int:
        """XP для текущего уровня"""
        xp_map = {
            1: 0, 2: 50, 3: 150, 4: 300, 5: 500,
            6: 800, 7: 1200, 8: 1700, 9: 2300, 10: 3000
        }
        return xp_map.get(level, 0)

    def _get_xp_for_next_level(self, level: int) -> int:
        """XP для следующего уровня"""
        return self._get_xp_for_level(level + 1) if level < 10 else 3000

    async def award_swap_completion(
            self,
            user: User,
            session: AsyncSession
    ) -> Dict:
        """Награда за завершение обмена"""

        base_xp = 20
        bonus_xp = 0

        # Бонус за рейтинг
        if user.rating >= 4.5:
            bonus_xp += 5

        # Бонус за серию обменов
        if user.successful_swaps > 0 and user.successful_swaps % 5 == 0:
            bonus_xp += 10

        total_xp = base_xp + bonus_xp
        user.experience_points += total_xp

        # Проверяем достижения
        new_achievements, level_up = await self.check_and_award_achievements(
            user, session
        )

        await session.commit()

        return {
            "xp_earned": total_xp,
            "new_achievements": new_achievements,
            "level_up": level_up
        }


# Singleton
gamification_service = GamificationService()