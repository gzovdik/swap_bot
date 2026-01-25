# -*- coding: utf-8 -*-
import aiosqlite

from app.config import constants, get_db_path


async def init_db():
    """Инициализация базы данных"""
    path = get_db_path()
    async with aiosqlite.connect(path) as db:
        await db.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            name TEXT DEFAULT 'Пользователь',
            phone TEXT,
            latitude REAL,
            longitude REAL,
            location_name TEXT,
            rating REAL DEFAULT {constants.DEFAULT_RATING},
            total_swaps INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_active DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Таблица объявлений
        await db.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_tg_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            price TEXT,
            photo_file_id TEXT,
            latitude REAL,
            longitude REAL,
            location_name TEXT,
            views INTEGER DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_tg_id) REFERENCES users (tg_id)
        )
        """)

        # Индекс для быстрого поиска активных объявлений
        await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_ads_active 
        ON ads(is_active, category, created_at DESC)
        """)

        # Таблица предложений обмена
        await db.execute("""
        CREATE TABLE IF NOT EXISTS swap_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            liked_ad_id INTEGER NOT NULL,
            proposer_ad_id INTEGER NOT NULL,
            proposer_user_id INTEGER NOT NULL,
            target_user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            message TEXT,
            proposed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            responded_at DATETIME,
            FOREIGN KEY (liked_ad_id) REFERENCES ads (id),
            FOREIGN KEY (proposer_ad_id) REFERENCES ads (id),
            FOREIGN KEY (proposer_user_id) REFERENCES users (tg_id),
            FOREIGN KEY (target_user_id) REFERENCES users (tg_id),
            UNIQUE(liked_ad_id, proposer_ad_id)
        )
        """)

        # Таблица отзывов
        await db.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            swap_id INTEGER,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            rated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user_id) REFERENCES users (tg_id),
            FOREIGN KEY (to_user_id) REFERENCES users (tg_id),
            FOREIGN KEY (swap_id) REFERENCES swap_proposals (id),
            UNIQUE(from_user_id, to_user_id, swap_id)
        )
        """)

        # Таблица избранного
        await db.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ad_id INTEGER NOT NULL,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (tg_id),
            FOREIGN KEY (ad_id) REFERENCES ads (id),
            UNIQUE(user_id, ad_id)
        )
        """)

        # Таблица просмотров
        await db.execute("""
        CREATE TABLE IF NOT EXISTS ad_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_id INTEGER NOT NULL,
            viewer_id INTEGER NOT NULL,
            viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ad_id) REFERENCES ads (id),
            FOREIGN KEY (viewer_id) REFERENCES users (tg_id)
        )
        """)

        await db.commit()
        print("✅ База данных инициализирована")