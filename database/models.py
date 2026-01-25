# -*- coding: utf-8 -*-
import aiosqlite
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from config.settings import DB_PATH
from config.constants import DEFAULT_RATING, AD_STATUS_ACTIVE


class UserModel:
    """Модель для работы с пользователями"""

    @staticmethod
    async def get_or_create(tg_id: int, username: str = None, name: str = "Пользователь") -> Dict[str, Any]:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT tg_id, username, name, phone, latitude, longitude, location_name, rating, total_swaps FROM users WHERE tg_id = ?",
                (tg_id,)
            )
            row = await cursor.fetchone()

            if row:
                return {
                    "tg_id": row[0],
                    "username": row[1],
                    "name": row[2],
                    "phone": row[3],
                    "latitude": row[4],
                    "longitude": row[5],
                    "location_name": row[6],
                    "rating": row[7],
                    "total_swaps": row[8]
                }

            await db.execute(
                "INSERT INTO users (tg_id, username, name) VALUES (?, ?, ?)",
                (tg_id, username, name)
            )
            await db.commit()

            return {
                "tg_id": tg_id,
                "username": username,
                "name": name,
                "phone": None,
                "latitude": None,
                "longitude": None,
                "location_name": None,
                "rating": DEFAULT_RATING,
                "total_swaps": 0
            }

    @staticmethod
    async def update_location(tg_id: int, latitude: float, longitude: float, location_name: str = ""):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET latitude = ?, longitude = ?, location_name = ?, last_active = CURRENT_TIMESTAMP WHERE tg_id = ?",
                (latitude, longitude, location_name, tg_id)
            )
            await db.commit()

    @staticmethod
    async def update_phone(tg_id: int, phone: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET phone = ?, last_active = CURRENT_TIMESTAMP WHERE tg_id = ?",
                (phone, tg_id)
            )
            await db.commit()

    @staticmethod
    async def update_field(tg_id: int, field: str, value: Any):
        if field not in ['name', 'phone', 'location_name']:
            return
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                f"UPDATE users SET {field} = ?, last_active = CURRENT_TIMESTAMP WHERE tg_id = ?",
                (value, tg_id)
            )
            await db.commit()

    @staticmethod
    async def get_profile(tg_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT tg_id, username, name, phone, latitude, longitude, location_name, rating, total_swaps, created_at FROM users WHERE tg_id = ?",
                (tg_id,)
            )
            row = await cursor.fetchone()

            if row:
                return {
                    "tg_id": row[0],
                    "username": row[1],
                    "name": row[2],
                    "phone": row[3],
                    "latitude": row[4],
                    "longitude": row[5],
                    "location_name": row[6],
                    "rating": row[7],
                    "total_swaps": row[8],
                    "created_at": row[9]
                }
            return None


class AdModel:
    """Модель для работы с объявлениями"""

    @staticmethod
    async def create(user_tg_id: int, category: str, title: str, description: str,
                     price: Optional[str], photo_file_id: Optional[str],
                     latitude: Optional[float] = None, longitude: Optional[float] = None,
                     location_name: Optional[str] = None) -> int:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("""
                                      INSERT INTO ads (user_tg_id, category, title, description, price, photo_file_id,
                                                       latitude, longitude, location_name, is_active)
                                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                      """, (user_tg_id, category, title, description, price, photo_file_id,
                                            latitude, longitude, location_name, AD_STATUS_ACTIVE))
            await db.commit()
            return cursor.lastrowid

    @staticmethod
    async def get_by_id(ad_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("""
                                      SELECT id,
                                             user_tg_id,
                                             category,
                                             title,
                                             description,
                                             price,
                                             photo_file_id,
                                             latitude,
                                             longitude,
                                             location_name,
                                             views,
                                             is_active,
                                             created_at
                                      FROM ads
                                      WHERE id = ?
                                      """, (ad_id,))
            row = await cursor.fetchone()

            if row:
                return {
                    "id": row[0],
                    "user_tg_id": row[1],
                    "category": row[2],
                    "title": row[3],
                    "description": row[4],
                    "price": row[5],
                    "photo_file_id": row[6],
                    "latitude": row[7],
                    "longitude": row[8],
                    "location_name": row[9],
                    "views": row[10],
                    "is_active": row[11],
                    "created_at": row[12]
                }
            return None

    @staticmethod
    async def get_user_ads(user_tg_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        query = """
                SELECT id, category, title, description, price, photo_file_id,
                       views, is_active, created_at
                FROM ads
                WHERE user_tg_id = ?
                """
        params = [user_tg_id]

        if active_only:
            query += " AND is_active = 1"

        query += " ORDER BY created_at DESC"

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "category": row[1],
                    "title": row[2],
                    "description": row[3],
                    "price": row[4],
                    "photo_file_id": row[5],
                    "views": row[6],
                    "is_active": row[7],
                    "created_at": row[8]
                }
                for row in rows
            ]

    @staticmethod
    async def get_next_ad(category: str, viewer_tg_id: int, last_ad_id: int = 0,
                          user_lat: Optional[float] = None, user_lon: Optional[float] = None,
                          max_distance_km: int = 100) -> Optional[Dict[str, Any]]:
        """Получить следующее объявление с учётом геолокации"""
        async with aiosqlite.connect(DB_PATH) as db:
            if user_lat and user_lon:
                query = """
                        SELECT id, user_tg_id, title, description, price, photo_file_id,
                               latitude, longitude, location_name, created_at,
                               (6371 * acos(cos(radians(?)) * cos(radians(latitude)) *
                                            cos(radians(longitude) - radians(?)) + sin(radians(?)) *
                                                                                   sin(radians(latitude)))) AS distance
                        FROM ads
                        WHERE is_active = 1
                          AND category = ?
                          AND user_tg_id != ?
                          AND id > ?
                        HAVING distance <= ? OR latitude IS NULL
                        ORDER BY distance ASC, id ASC
                        LIMIT 1
                        """
                params = (user_lat, user_lon, user_lat, category, viewer_tg_id, last_ad_id, max_distance_km)
            else:
                query = """
                        SELECT id, user_tg_id, title, description, price, photo_file_id,
                               latitude, longitude, location_name, created_at
                        FROM ads
                        WHERE is_active = 1
                          AND category = ?
                          AND user_tg_id != ?
                          AND id > ?
                        ORDER BY id ASC
                        LIMIT 1
                        """
                params = (category, viewer_tg_id, last_ad_id)

            cursor = await db.execute(query, params)
            row = await cursor.fetchone()

            if row:
                result = {
                    "id": row[0],
                    "user_tg_id": row[1],
                    "title": row[2],
                    "description": row[3],
                    "price": row[4],
                    "photo_file_id": row[5],
                    "latitude": row[6],
                    "longitude": row[7],
                    "location_name": row[8],
                    "created_at": row[9]
                }
                if user_lat and user_lon and len(row) > 10:
                    result["distance"] = row[10]
                return result

            if last_ad_id > 0:
                return await AdModel.get_next_ad(category, viewer_tg_id, 0, user_lat, user_lon, max_distance_km)

            return None

    @staticmethod
    async def increment_views(ad_id: int, viewer_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE ads SET views = views + 1 WHERE id = ?", (ad_id,))
            await db.execute(
                "INSERT OR IGNORE INTO ad_views (ad_id, viewer_id) VALUES (?, ?)",
                (ad_id, viewer_id)
            )
            await db.commit()

    @staticmethod
    async def deactivate(ad_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE ads SET is_active = 0 WHERE id = ?", (ad_id,))
            await db.commit()

    @staticmethod
    async def activate(ad_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE ads SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (ad_id,))
            await db.commit()


class SwapModel:
    """Модель для работы с предложениями обмена"""

    @staticmethod
    async def create(liked_ad_id: int, proposer_ad_id: int,
                     proposer_user_id: int, target_user_id: int,
                     message: str = "") -> Tuple[bool, Optional[int]]:
        async with aiosqlite.connect(DB_PATH) as db:
            try:
                cursor = await db.execute("""
                                          INSERT INTO swap_proposals (liked_ad_id, proposer_ad_id, proposer_user_id,
                                                                      target_user_id, message)
                                          VALUES (?, ?, ?, ?, ?)
                                          """, (liked_ad_id, proposer_ad_id, proposer_user_id, target_user_id, message))
                await db.commit()
                return True, cursor.lastrowid
            except aiosqlite.IntegrityError:
                return False, None

    @staticmethod
    async def get_incoming(user_id: int, status: str = "pending") -> List[Dict[str, Any]]:
        """Получить входящие предложения"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("""
                                      SELECT sp.id,
                                             sp.liked_ad_id,
                                             sp.proposer_ad_id,
                                             sp.proposer_user_id,
                                             sp.status,
                                             sp.message,
                                             sp.proposed_at,
                                             a1.title as my_ad_title,
                                             a2.title as their_ad_title
                                      FROM swap_proposals sp
                                               JOIN ads a1 ON sp.liked_ad_id = a1.id
                                               JOIN ads a2 ON sp.proposer_ad_id = a2.id
                                      WHERE sp.target_user_id = ?
                                        AND sp.status = ?
                                      ORDER BY sp.proposed_at DESC
                                      """, (user_id, status))
            rows = await cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "liked_ad_id": row[1],
                    "proposer_ad_id": row[2],
                    "proposer_user_id": row[3],
                    "status": row[4],
                    "message": row[5],
                    "proposed_at": row[6],
                    "my_ad_title": row[7],
                    "their_ad_title": row[8]
                }
                for row in rows
            ]

    @staticmethod
    async def get_outgoing(user_id: int) -> List[Dict[str, Any]]:
        """Получить исходящие предложения"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("""
                                      SELECT sp.id,
                                             sp.liked_ad_id,
                                             sp.proposer_ad_id,
                                             sp.target_user_id,
                                             sp.status,
                                             sp.message,
                                             sp.proposed_at,
                                             a1.title as their_ad_title,
                                             a2.title as my_ad_title
                                      FROM swap_proposals sp
                                               JOIN ads a1 ON sp.liked_ad_id = a1.id
                                               JOIN ads a2 ON sp.proposer_ad_id = a2.id
                                      WHERE sp.proposer_user_id = ?
                                      ORDER BY sp.proposed_at DESC
                                      """, (user_id,))
            rows = await cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "liked_ad_id": row[1],
                    "proposer_ad_id": row[2],
                    "target_user_id": row[3],
                    "status": row[4],
                    "message": row[5],
                    "proposed_at": row[6],
                    "their_ad_title": row[7],
                    "my_ad_title": row[8]
                }
                for row in rows
            ]

    @staticmethod
    async def update_status(swap_id: int, status: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE swap_proposals SET status = ?, responded_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, swap_id)
            )
            await db.commit()


class RatingModel:
    """Модель для работы с рейтингами"""

    @staticmethod
    async def add_rating(from_user_id: int, to_user_id: int, rating: int,
                         comment: str = "", swap_id: Optional[int] = None) -> bool:
        async with aiosqlite.connect(DB_PATH) as db:
            try:
                await db.execute("""
                                 INSERT INTO ratings (from_user_id, to_user_id, rating, comment, swap_id)
                                 VALUES (?, ?, ?, ?, ?)
                                 """, (from_user_id, to_user_id, rating, comment, swap_id))
                await db.commit()

                await RatingModel.update_user_rating(to_user_id)
                return True
            except aiosqlite.IntegrityError:
                return False

    @staticmethod
    async def update_user_rating(user_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT AVG(rating), COUNT(*) FROM ratings WHERE to_user_id = ?",
                (user_id,)
            )
            avg_rating, count = await cursor.fetchone()
            avg_rating = avg_rating or DEFAULT_RATING

            await db.execute(
                "UPDATE users SET rating = ? WHERE tg_id = ?",
                (avg_rating, user_id)
            )
            await db.commit()

    @staticmethod
    async def get_user_ratings(user_id: int) -> Tuple[float, int]:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT AVG(rating), COUNT(*) FROM ratings WHERE to_user_id = ?",
                (user_id,)
            )
            avg_rating, count = await cursor.fetchone()
            return (avg_rating or DEFAULT_RATING, count or 0)


class FavoriteModel:
    """Модель для работы с избранным"""

    @staticmethod
    async def add(user_id: int, ad_id: int) -> bool:
        """Добавить объявление в избранное"""
        async with aiosqlite.connect(DB_PATH) as db:
            try:
                await db.execute(
                    "INSERT INTO favorites (user_id, ad_id) VALUES (?, ?)",
                    (user_id, ad_id)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    @staticmethod
    async def remove(user_id: int, ad_id: int) -> bool:
        """Удалить из избранного"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "DELETE FROM favorites WHERE user_id = ? AND ad_id = ?",
                (user_id, ad_id)
            )
            await db.commit()
            return cursor.rowcount > 0

    @staticmethod
    async def get_all(user_id: int) -> List[Dict[str, Any]]:
        """Получить все избранные объявления"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("""
                SELECT a.id, a.title, a.description, a.price, a.photo_file_id,
                       a.category, a.created_at
                FROM favorites f
                JOIN ads a ON f.ad_id = a.id
                WHERE f.user_id = ?
                  AND a.is_active = 1
                ORDER BY f.added_at DESC
            """, (user_id,))
            
            rows = await cursor.fetchall()
            
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "price": row[3],
                    "photo_file_id": row[4],
                    "category": row[5],
                    "created_at": row[6]
                }
                for row in rows
            ]

    @staticmethod
    async def is_favorite(user_id: int, ad_id: int) -> bool:
        """Проверить, в избранном ли объявление"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT 1 FROM favorites WHERE user_id = ? AND ad_id = ?",
                (user_id, ad_id)
            )
            return await cursor.fetchone() is not None