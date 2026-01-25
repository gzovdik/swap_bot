# -*- coding: utf-8 -*-
"""Модели для бота (aiosqlite). ORM — в models_orm.py."""
import aiosqlite
from typing import Optional, List, Dict, Any, Tuple

from app.config import constants, get_db_path


class UserModel:
    @staticmethod
    async def get_or_create(tg_id: int, username: str = None, name: str = "Пользователь") -> Dict[str, Any]:
        async with aiosqlite.connect(get_db_path()) as db:
            cursor = await db.execute(
                "SELECT tg_id, username, name, phone, latitude, longitude, location_name, rating, total_swaps FROM users WHERE tg_id = ?",
                (tg_id,),
            )
            row = await cursor.fetchone()
            if row:
                return {
                    "tg_id": row[0], "username": row[1], "name": row[2], "phone": row[3],
                    "latitude": row[4], "longitude": row[5], "location_name": row[6],
                    "rating": row[7], "total_swaps": row[8],
                }
            await db.execute("INSERT INTO users (tg_id, username, name) VALUES (?, ?, ?)", (tg_id, username, name))
            await db.commit()
            return {
                "tg_id": tg_id, "username": username, "name": name, "phone": None,
                "latitude": None, "longitude": None, "location_name": None,
                "rating": constants.DEFAULT_RATING, "total_swaps": 0,
            }

    @staticmethod
    async def update_location(tg_id: int, latitude: float, longitude: float, location_name: str = ""):
        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute(
                "UPDATE users SET latitude=?, longitude=?, location_name=?, last_active=CURRENT_TIMESTAMP WHERE tg_id=?",
                (latitude, longitude, location_name, tg_id),
            )
            await db.commit()

    @staticmethod
    async def update_phone(tg_id: int, phone: str):
        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute("UPDATE users SET phone=?, last_active=CURRENT_TIMESTAMP WHERE tg_id=?", (phone, tg_id))
            await db.commit()

    @staticmethod
    async def update_field(tg_id: int, field: str, value: Any):
        if field not in ("name", "phone", "location_name"):
            return
        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute(f"UPDATE users SET {field}=?, last_active=CURRENT_TIMESTAMP WHERE tg_id=?", (value, tg_id))
            await db.commit()

    @staticmethod
    async def get_profile(tg_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(get_db_path()) as db:
            cursor = await db.execute(
                "SELECT tg_id, username, name, phone, latitude, longitude, location_name, rating, total_swaps, created_at FROM users WHERE tg_id=?",
                (tg_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return {
                "tg_id": row[0], "username": row[1], "name": row[2], "phone": row[3],
                "latitude": row[4], "longitude": row[5], "location_name": row[6],
                "rating": row[7], "total_swaps": row[8], "created_at": row[9],
            }


class AdModel:
    @staticmethod
    async def create(user_tg_id: int, category: str, title: str, description: str, price: Optional[str],
                     photo_file_id: Optional[str], latitude=None, longitude=None, location_name=None) -> int:
        async with aiosqlite.connect(get_db_path()) as db:
            cursor = await db.execute(
                """INSERT INTO ads (user_tg_id, category, title, description, price, photo_file_id,
                   latitude, longitude, location_name, is_active) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (user_tg_id, category, title, description, price, photo_file_id,
                 latitude, longitude, location_name, constants.AD_STATUS_ACTIVE),
            )
            await db.commit()
            return cursor.lastrowid

    @staticmethod
    async def get_by_id(ad_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(get_db_path()) as db:
            cursor = await db.execute(
                "SELECT id, user_tg_id, category, title, description, price, photo_file_id, latitude, longitude, location_name, views, is_active, created_at FROM ads WHERE id=?",
                (ad_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return {
                "id": row[0], "user_tg_id": row[1], "category": row[2], "title": row[3], "description": row[4],
                "price": row[5], "photo_file_id": row[6], "latitude": row[7], "longitude": row[8],
                "location_name": row[9], "views": row[10], "is_active": row[11], "created_at": row[12],
            }

    @staticmethod
    async def get_user_ads(user_tg_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        q = "SELECT id, category, title, description, price, photo_file_id, views, is_active, created_at FROM ads WHERE user_tg_id=?"
        if active_only:
            q += " AND is_active=1"
        q += " ORDER BY created_at DESC"
        async with aiosqlite.connect(get_db_path()) as db:
            cursor = await db.execute(q, (user_tg_id,))
            rows = await cursor.fetchall()
        return [
            {"id": r[0], "category": r[1], "title": r[2], "description": r[3], "price": r[4],
             "photo_file_id": r[5], "views": r[6], "is_active": r[7], "created_at": r[8]}
            for r in rows
        ]

    @staticmethod
    async def get_next_ad(category: str, viewer_tg_id: int, last_ad_id: int = 0, user_lat=None, user_lon=None, max_distance_km: int = 100) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(get_db_path()) as db:
            if user_lat and user_lon:
                q = """SELECT id, user_tg_id, title, description, price, photo_file_id, latitude, longitude, location_name, created_at,
                        (6371*acos(cos(radians(?))*cos(radians(latitude))*cos(radians(longitude)-radians(?))+sin(radians(?))*sin(radians(latitude)))) AS distance
                        FROM ads WHERE is_active=1 AND category=? AND user_tg_id!=? AND id>?
                        HAVING distance<=? OR latitude IS NULL ORDER BY distance ASC, id ASC LIMIT 1"""
                params = (user_lat, user_lon, user_lat, category, viewer_tg_id, last_ad_id, max_distance_km)
            else:
                q = "SELECT id, user_tg_id, title, description, price, photo_file_id, latitude, longitude, location_name, created_at FROM ads WHERE is_active=1 AND category=? AND user_tg_id!=? AND id>? ORDER BY id ASC LIMIT 1"
                params = (category, viewer_tg_id, last_ad_id)
            cursor = await db.execute(q, params)
            row = await cursor.fetchone()
        if not row:
            if last_ad_id > 0:
                return await AdModel.get_next_ad(category, viewer_tg_id, 0, user_lat, user_lon, max_distance_km)
            return None
        out = {"id": row[0], "user_tg_id": row[1], "title": row[2], "description": row[3], "price": row[4], "photo_file_id": row[5], "latitude": row[6], "longitude": row[7], "location_name": row[8], "created_at": row[9]}
        if user_lat and user_lon and len(row) > 10:
            out["distance"] = row[10]
        return out

    @staticmethod
    async def increment_views(ad_id: int, viewer_id: int):
        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute("UPDATE ads SET views=views+1 WHERE id=?", (ad_id,))
            await db.execute("INSERT OR IGNORE INTO ad_views (ad_id, viewer_id) VALUES (?,?)", (ad_id, viewer_id))
            await db.commit()

    @staticmethod
    async def deactivate(ad_id: int):
        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute("UPDATE ads SET is_active=0 WHERE id=?", (ad_id,))
            await db.commit()

    @staticmethod
    async def activate(ad_id: int):
        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute("UPDATE ads SET is_active=1, updated_at=CURRENT_TIMESTAMP WHERE id=?", (ad_id,))
            await db.commit()


class SwapModel:
    @staticmethod
    async def create(liked_ad_id: int, proposer_ad_id: int, proposer_user_id: int, target_user_id: int, message: str = "") -> Tuple[bool, Optional[int]]:
        try:
            async with aiosqlite.connect(get_db_path()) as db:
                cursor = await db.execute(
                    "INSERT INTO swap_proposals (liked_ad_id, proposer_ad_id, proposer_user_id, target_user_id, message) VALUES (?,?,?,?,?)",
                    (liked_ad_id, proposer_ad_id, proposer_user_id, target_user_id, message),
                )
                await db.commit()
                return True, cursor.lastrowid
        except aiosqlite.IntegrityError:
            return False, None

    @staticmethod
    async def get_incoming(user_id: int, status: str = "pending") -> List[Dict[str, Any]]:
        async with aiosqlite.connect(get_db_path()) as db:
            cursor = await db.execute("""
                SELECT sp.id, sp.liked_ad_id, sp.proposer_ad_id, sp.proposer_user_id, sp.status, sp.message, sp.proposed_at,
                       a1.title, a2.title
                FROM swap_proposals sp JOIN ads a1 ON sp.liked_ad_id=a1.id JOIN ads a2 ON sp.proposer_ad_id=a2.id
                WHERE sp.target_user_id=? AND sp.status=? ORDER BY sp.proposed_at DESC
            """, (user_id, status))
            rows = await cursor.fetchall()
        return [{"id": r[0], "liked_ad_id": r[1], "proposer_ad_id": r[2], "proposer_user_id": r[3], "status": r[4], "message": r[5], "proposed_at": r[6], "my_ad_title": r[7], "their_ad_title": r[8]} for r in rows]

    @staticmethod
    async def get_outgoing(user_id: int) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(get_db_path()) as db:
            cursor = await db.execute("""
                SELECT sp.id, sp.liked_ad_id, sp.proposer_ad_id, sp.target_user_id, sp.status, sp.message, sp.proposed_at,
                       a1.title, a2.title
                FROM swap_proposals sp JOIN ads a1 ON sp.liked_ad_id=a1.id JOIN ads a2 ON sp.proposer_ad_id=a2.id
                WHERE sp.proposer_user_id=? ORDER BY sp.proposed_at DESC
            """, (user_id,))
            rows = await cursor.fetchall()
        return [{"id": r[0], "liked_ad_id": r[1], "proposer_ad_id": r[2], "target_user_id": r[3], "status": r[4], "message": r[5], "proposed_at": r[6], "their_ad_title": r[7], "my_ad_title": r[8]} for r in rows]

    @staticmethod
    async def update_status(swap_id: int, status: str):
        async with aiosqlite.connect(get_db_path()) as db:
            await db.execute("UPDATE swap_proposals SET status=?, responded_at=CURRENT_TIMESTAMP WHERE id=?", (status, swap_id))
            await db.commit()


class RatingModel:
    @staticmethod
    async def add_rating(from_user_id: int, to_user_id: int, rating: int, comment: str = "", swap_id: Optional[int] = None) -> bool:
        try:
            async with aiosqlite.connect(get_db_path()) as db:
                await db.execute("INSERT INTO ratings (from_user_id, to_user_id, rating, comment, swap_id) VALUES (?,?,?,?,?)", (from_user_id, to_user_id, rating, comment, swap_id))
                await db.commit()
                cursor = await db.execute("SELECT AVG(rating) FROM ratings WHERE to_user_id=?", (to_user_id,))
                avg, = (await cursor.fetchone())
                avg = avg or constants.DEFAULT_RATING
                await db.execute("UPDATE users SET rating=? WHERE tg_id=?", (avg, to_user_id))
                await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    @staticmethod
    async def get_user_ratings(user_id: int) -> Tuple[float, int]:
        async with aiosqlite.connect(get_db_path()) as db:
            cursor = await db.execute("SELECT AVG(rating), COUNT(*) FROM ratings WHERE to_user_id=?", (user_id,))
            avg, cnt = await cursor.fetchone()
            return (avg or constants.DEFAULT_RATING, cnt or 0)


class FavoriteModel:
    @staticmethod
    async def add(user_id: int, ad_id: int) -> bool:
        try:
            async with aiosqlite.connect(get_db_path()) as db:
                await db.execute("INSERT INTO favorites (user_id, ad_id) VALUES (?,?)", (user_id, ad_id))
                await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False
