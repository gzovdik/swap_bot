# -*- coding: utf-8 -*-
"""
Парсинг объявлений с Avito (Идея #14: Интеграции)

ВНИМАНИЕ: Парсинг Avito может нарушать их Terms of Service.
Используйте на свой риск или получите официальный API доступ.
"""
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import asyncio
import re
from urllib.parse import urljoin

from app.config import settings


class AvitoParserService:
    """Сервис парсинга Avito"""

    BASE_URL = "https://www.avito.ru"

    def __init__(self):
        self.enabled = settings.AVITO_PARSER_ENABLED
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        }

    async def search_ads(
            self,
            query: str,
            category: Optional[str] = None,
            city: str = "moskva",
            limit: int = 20
    ) -> List[Dict]:
        """
        Поиск объявлений на Avito

        Args:
            query: Поисковый запрос
            category: Категория (electronics, clothing, etc)
            city: Город
            limit: Максимальное количество результатов

        Returns:
            Список объявлений
        """
        if not self.enabled:
            return []

        # Маппинг категорий на Avito
        category_map = {
            "electronics": "elektronika",
            "clothing": "odezhda_obuv_aksessuary",
            "home": "tovary_dlya_doma_i_dachi",
            "hobbies": "hobbi_i_otdyh",
        }

        avito_category = category_map.get(category, "")

        # Формируем URL
        if avito_category:
            url = f"{self.BASE_URL}/{city}/{avito_category}?q={query}"
        else:
            url = f"{self.BASE_URL}/{city}?q={query}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        print(f"❌ Avito parser error: HTTP {response.status}")
                        return []

                    html = await response.text()
                    ads = await self._parse_search_results(html, limit)

                    return ads

        except Exception as e:
            print(f"❌ Avito parser exception: {e}")
            return []

    async def _parse_search_results(self, html: str, limit: int) -> List[Dict]:
        """Парсинг результатов поиска"""
        soup = BeautifulSoup(html, 'lxml')

        # Ищем контейнеры с объявлениями
        # ВНИМАНИЕ: Селекторы могут измениться в любой момент!
        items = soup.select('[data-marker="item"]')[:limit]

        ads = []
        for item in items:
            try:
                ad_data = await self._parse_ad_item(item)
                if ad_data:
                    ads.append(ad_data)
            except Exception as e:
                print(f"⚠️  Error parsing ad item: {e}")
                continue

        return ads

    async def _parse_ad_item(self, item) -> Optional[Dict]:
        """Парсинг одного объявления"""

        # Заголовок
        title_elem = item.select_one('[itemprop="name"]')
        if not title_elem:
            return None
        title = title_elem.get_text(strip=True)

        # Описание
        description_elem = item.select_one('[class*="item-description"]')
        description = description_elem.get_text(strip=True) if description_elem else ""

        # Цена
        price_elem = item.select_one('[itemprop="price"]')
        price_text = price_elem.get('content') if price_elem else None
        price = self._parse_price(price_text) if price_text else None

        # Ссылка
        link_elem = item.select_one('a[itemprop="url"]')
        link = urljoin(self.BASE_URL, link_elem.get('href')) if link_elem else None

        # Изображение
        img_elem = item.select_one('img[itemprop="image"]')
        image_url = img_elem.get('src') if img_elem else None

        # Местоположение
        location_elem = item.select_one('[class*="geo-georeferences"]')
        location = location_elem.get_text(strip=True) if location_elem else None

        return {
            "title": title,
            "description": description,
            "price": price,
            "link": link,
            "image_url": image_url,
            "location": location,
            "source": "avito"
        }

    def _parse_price(self, price_text: str) -> Optional[int]:
        """Извлечение цены из текста"""
        # Убираем все кроме цифр
        numbers = re.sub(r'\D', '', price_text)

        try:
            return int(numbers) if numbers else None
        except ValueError:
            return None

    async def download_image(self, image_url: str) -> Optional[bytes]:
        """Скачивание изображения"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.read()
        except Exception as e:
            print(f"⚠️  Error downloading image: {e}")

        return None

    async def import_ad_to_bot(
            self,
            ad_data: Dict,
            user_id: int,
            category: str
    ) -> Dict:
        """
        Импорт объявления в бота

        Returns:
            Подготовленные данные для создания объявления
        """
        # Загружаем изображение если есть
        photo_data = None
        if ad_data.get("image_url"):
            photo_data = await self.download_image(ad_data["image_url"])

        return {
            "user_id": user_id,
            "category": category,
            "title": ad_data["title"][:150],  # Ограничиваем длину
            "description": (
                f"{ad_data['description']}\n\n"
                f"🔗 Источник: {ad_data.get('link', 'Avito')}"
            )[:500],
            "price": ad_data.get("price"),
            "photo_data": photo_data,
            "location_name": ad_data.get("location"),
        }


# Singleton instance
avito_parser = AvitoParserService()


# ==================== USAGE EXAMPLE ====================

async def example_usage():
    """Пример использования парсера"""

    # Поиск iPhone на Avito
    results = await avito_parser.search_ads(
        query="iPhone 13",
        category="electronics",
        city="moskva",
        limit=10
    )

    print(f"Найдено объявлений: {len(results)}")

    for ad in results:
        print(f"\n📱 {ad['title']}")
        print(f"💰 {ad['price']} ₽")
        print(f"📍 {ad['location']}")
        print(f"🔗 {ad['link']}")


if __name__ == "__main__":
    asyncio.run(example_usage())