# -*- coding: utf-8 -*-
"""
AI-рекомендации и умная система подбора (Идея #1)
Использует векторные эмбеддинги для семантического поиска
"""
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models_orm import Ad, User, Like, AdView
from app.config import settings


class AIRecommendationService:
    """Сервис AI-рекомендаций"""

    def __init__(self):
        if settings.USE_AI_RECOMMENDATIONS:
            # Используем лёгкую модель для эмбеддингов
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        else:
            self.model = None

    async def generate_embedding(self, text: str) -> List[float]:
        """Генерация векторного представления текста"""
        if not self.model:
            return []

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def create_ad_embedding(self, ad: Ad) -> Dict:
        """Создание эмбеддинга для объявления"""
        # Объединяем заголовок и описание
        text = f"{ad.title}. {ad.description}"

        embedding = await self.generate_embedding(text)

        # Автогенерация тегов
        tags = await self._extract_tags(text)

        return {
            "embedding": embedding,
            "tags": tags
        }

    async def _extract_tags(self, text: str) -> List[str]:
        """Извлечение ключевых слов из текста"""
        # Простая реализация (можно улучшить с помощью NLP)
        words = text.lower().split()

        # Исключаем стоп-слова
        stop_words = {"и", "в", "на", "с", "для", "как", "за", "по", "под"}
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]

        # Берём топ-10 самых длинных слов (грубая эвристика)
        keywords = sorted(set(keywords), key=len, reverse=True)[:10]

        return keywords

    async def get_similar_ads(
            self,
            ad_id: int,
            session: AsyncSession,
            limit: int = 10
    ) -> List[Ad]:
        """Поиск похожих объявлений по векторной близости"""

        # Получаем объявление
        result = await session.execute(
            select(Ad).where(Ad.id == ad_id)
        )
        target_ad = result.scalar_one_or_none()

        if not target_ad or not target_ad.embedding:
            return []

        target_embedding = np.array(target_ad.embedding.get("embedding", []))

        # Получаем все активные объявления той же категории
        result = await session.execute(
            select(Ad).where(
                and_(
                    Ad.category == target_ad.category,
                    Ad.status == "active",
                    Ad.id != ad_id
                )
            )
        )
        ads = result.scalars().all()

        # Вычисляем косинусное сходство
        similarities = []
        for ad in ads:
            if ad.embedding and ad.embedding.get("embedding"):
                ad_embedding = np.array(ad.embedding["embedding"])
                similarity = self._cosine_similarity(target_embedding, ad_embedding)
                similarities.append((ad, similarity))

        # Сортируем по сходству
        similarities.sort(key=lambda x: x[1], reverse=True)

        return [ad for ad, _ in similarities[:limit]]

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Вычисление косинусного сходства"""
        if len(vec1) == 0 or len(vec2) == 0:
            return 0.0

        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    async def get_personalized_recommendations(
            self,
            user_id: int,
            session: AsyncSession,
            limit: int = 20
    ) -> List[Ad]:
        """Персонализированные рекомендации на основе истории лайков"""

        # Получаем лайки пользователя
        result = await session.execute(
            select(Like).where(Like.user_id == user_id).limit(50)
        )
        likes = result.scalars().all()

        if not likes:
            # Если нет лайков, возвращаем популярные объявления
            return await self._get_popular_ads(session, limit)

        # Получаем объявления, которые лайкнул пользователь
        liked_ad_ids = [like.ad_id for like in likes]
        result = await session.execute(
            select(Ad).where(Ad.id.in_(liked_ad_ids))
        )
        liked_ads = result.scalars().all()

        # Усредняем эмбеддинги лайкнутых объявлений
        embeddings = []
        for ad in liked_ads:
            if ad.embedding and ad.embedding.get("embedding"):
                embeddings.append(np.array(ad.embedding["embedding"]))

        if not embeddings:
            return await self._get_popular_ads(session, limit)

        # Средний эмбеддинг = профиль интересов пользователя
        user_profile = np.mean(embeddings, axis=0)

        # Находим объявления, близкие к профилю
        result = await session.execute(
            select(Ad).where(
                and_(
                    Ad.status == "active",
                    Ad.id.notin_(liked_ad_ids)
                )
            ).limit(200)  # Ограничиваем для производительности
        )
        candidate_ads = result.scalars().all()

        # Вычисляем сходство с профилем пользователя
        recommendations = []
        for ad in candidate_ads:
            if ad.embedding and ad.embedding.get("embedding"):
                ad_embedding = np.array(ad.embedding["embedding"])
                similarity = self._cosine_similarity(user_profile, ad_embedding)
                recommendations.append((ad, similarity))

        # Сортируем по сходству
        recommendations.sort(key=lambda x: x[1], reverse=True)

        return [ad for ad, _ in recommendations[:limit]]

    async def _get_popular_ads(
            self,
            session: AsyncSession,
            limit: int = 20
    ) -> List[Ad]:
        """Получение популярных объявлений (fallback)"""
        result = await session.execute(
            select(Ad)
            .where(Ad.status == "active")
            .order_by(Ad.views.desc(), Ad.likes_count.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def update_ad_recommendations(
            self,
            ad: Ad,
            session: AsyncSession
    ):
        """Обновление эмбеддинга и рекомендаций для объявления"""
        embedding_data = await self.create_ad_embedding(ad)

        ad.embedding = embedding_data["embedding"]
        ad.tags = embedding_data["tags"]

        await session.commit()


# Singleton instance
ai_service = AIRecommendationService()