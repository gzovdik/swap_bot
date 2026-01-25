# -*- coding: utf-8 -*-
import re
from typing import Optional
from config.constants import MAX_TEXT_LEN, MAX_NAME_LEN, MAX_TITLE_LEN, MAX_DESC_LEN


def validate_text(text: str, max_len: int = MAX_TEXT_LEN) -> Optional[str]:
    """Валидация текста"""
    text = text.strip()
    if not text:
        return None
    if len(text) > max_len:
        return None
    return text


def validate_name(name: str) -> Optional[str]:
    """Валидация имени"""
    return validate_text(name, MAX_NAME_LEN)


def validate_title(title: str) -> Optional[str]:
    """Валидация заголовка объявления"""
    return validate_text(title, MAX_TITLE_LEN)


def validate_description(description: str) -> Optional[str]:
    """Валидация описания"""
    return validate_text(description, MAX_DESC_LEN)


def validate_phone(phone: str) -> Optional[str]:
    """Валидация телефона"""
    # Убираем все символы кроме цифр и +
    phone = re.sub(r'[^\d+]', '', phone)

    # Проверяем формат
    if re.match(r'^\+?\d{10,15}$', phone):
        return phone
    return None


def validate_price(price_text: str) -> Optional[str]:
    """Валидация цены"""
    price_text = price_text.strip()

    # Убираем всё кроме цифр
    digits = re.sub(r'\D', '', price_text)

    if not digits:
        return None

    price_int = int(digits)
    if price_int < 0:
        return None

    return str(price_int) if price_int > 0 else None


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Валидация координат"""
    return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)