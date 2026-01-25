# -*- coding: utf-8 -*-
import html
from datetime import datetime
from typing import Optional


def format_rating(rating: float) -> str:
    """Форматирование рейтинга"""
    full_stars = int(rating)
    empty_stars = 5 - full_stars
    return f"{'⭐' * full_stars}{'☆' * empty_stars} ({rating:.1f})"


def format_distance(distance_km: float) -> str:
    """Форматирование расстояния"""
    if distance_km < 1:
        return f"{int(distance_km * 1000)} м"
    elif distance_km < 10:
        return f"{distance_km:.1f} км"
    else:
        return f"{int(distance_km)} км"


def format_price(price: Optional[str]) -> str:
    """Форматирование цены"""
    if not price or price == "0":
        return "🎁 Бесплатно"

    try:
        price_int = int(price)
        return f"💰 {price_int:,} ₽".replace(',', ' ')
    except:
        return "🎁 Бесплатно"


def format_date(date_str: str) -> str:
    """Форматирование даты (SQLite: YYYY-MM-DD HH:MM:SS)."""
    try:
        s = (date_str or "").strip().replace(" ", "T", 1)
        dt = datetime.fromisoformat(s)
        now = datetime.now()
        diff = now - dt

        if diff.days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                minutes = diff.seconds // 60
                return f"{minutes} мин назад" if minutes > 0 else "только что"
            return f"{hours} ч назад"
        elif diff.days == 1:
            return "вчера"
        elif diff.days < 7:
            return f"{diff.days} дн назад"
        else:
            return dt.strftime("%d.%m.%Y")
    except:
        return date_str


def escape_html(text: str) -> str:
    """Экранирование HTML"""
    return html.escape(str(text))


def format_phone(phone: Optional[str]) -> str:
    """Форматирование телефона"""
    if not phone:
        return "не указан"

    # Убираем + в начале если есть
    phone = phone.lstrip('+')

    # Форматируем российский номер
    if len(phone) == 11 and phone.startswith('7'):
        return f"+7 ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:11]}"
    elif len(phone) == 10:
        return f"+7 ({phone[0:3]}) {phone[3:6]}-{phone[6:8]}-{phone[8:10]}"
    else:
        return f"+{phone}"


def format_ad_text(title: str, description: str, price: Optional[str],
                   location: Optional[str] = None, distance: Optional[float] = None,
                   owner_name: Optional[str] = None, owner_rating: Optional[float] = None) -> str:
    """Форматирование текста объявления"""
    text = f"<b>{escape_html(title)}</b>\n\n"
    text += f"{escape_html(description)}\n\n"
    text += format_price(price)

    if location:
        text += f"\n📍 {escape_html(location)}"
        if distance is not None:
            text += f" ({format_distance(distance)})"

    if owner_name and owner_rating:
        text += f"\n\n👤 {escape_html(owner_name)} | {format_rating(owner_rating)}"

    return text


def format_profile_text(name: str, phone: Optional[str], location: Optional[str],
                        rating: float, total_swaps: int, ads_count: int) -> str:
    """Форматирование текста профиля"""
    text = "👤 <b>Ваш профиль</b>\n\n"
    text += f"<b>Имя:</b> {escape_html(name)}\n"
    text += f"<b>Телефон:</b> {format_phone(phone)}\n"
    text += f"<b>Локация:</b> {escape_html(location) if location else 'не указана'}\n\n"
    text += f"📊 <b>Статистика:</b>\n"
    text += f"• Рейтинг: {format_rating(rating)}\n"
    text += f"• Обменов: {total_swaps}\n"
    text += f"• Объявлений: {ads_count}\n"

    return text