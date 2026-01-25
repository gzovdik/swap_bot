# -*- coding: utf-8 -*-
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config.constants import CATEGORIES


# ==================== ГЛАВНОЕ МЕНЮ ====================
def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню - показывается только на главной странице"""
    kb = [
        [KeyboardButton(text="🔥 Смотреть объявления")],
        [KeyboardButton(text="➕ Создать объявление")],
        [KeyboardButton(text="💬 Мои предложения")],
        [KeyboardButton(text="👤 Профиль")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# ==================== МЕНЮ ПРОФИЛЯ ====================
def get_profile_menu() -> ReplyKeyboardMarkup:
    """Меню в профиле - цифровой выбор"""
    kb = [
        [KeyboardButton(text="1"), KeyboardButton(text="2")],
        [KeyboardButton(text="3"), KeyboardButton(text="4")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# ==================== МЕНЮ НАСТРОЕК ====================
def get_settings_menu() -> ReplyKeyboardMarkup:
    """Меню настроек - цифровой выбор"""
    kb = [
        [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
        [KeyboardButton(text="4")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# ==================== МЕНЮ ПРОСМОТРА ====================
def get_browse_menu() -> ReplyKeyboardMarkup:
    """Меню при просмотре объявлений"""
    kb = [
        [KeyboardButton(text="👎 Далее"), KeyboardButton(text="❤️ Обмен")],
        [KeyboardButton(text="⭐ Избранное"), KeyboardButton(text="👤 Автор")],
        [KeyboardButton(text="🏠 Главная")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# ==================== МЕНЮ СОЗДАНИЯ ====================
def get_create_menu() -> ReplyKeyboardMarkup:
    """Меню при создании объявления - только 2 кнопки"""
    kb = [
        [KeyboardButton(text="◀️ Назад"), KeyboardButton(text="⏭️ Пропустить")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_create_back_only() -> ReplyKeyboardMarkup:
    """Только кнопка Назад (когда пропуск невозможен)"""
    kb = [
        [KeyboardButton(text="◀️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# ==================== МЕНЮ МОИ ОБЪЯВЛЕНИЯ ====================
def get_my_ads_menu() -> ReplyKeyboardMarkup:
    """Меню моих объявлений"""
    kb = [
        [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
        [KeyboardButton(text="◀️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# ==================== СПЕЦИАЛЬНЫЕ КЛАВИАТУРЫ ====================
def get_location_request_kb() -> ReplyKeyboardMarkup:
    """Клавиатура для запроса местоположения"""
    kb = [
        [KeyboardButton(text="📍 Поделиться местоположением", request_location=True)],
        [KeyboardButton(text="◀️ Назад"), KeyboardButton(text="⏭️ Пропустить")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def get_phone_request_kb() -> ReplyKeyboardMarkup:
    """Клавиатура для запроса телефона"""
    kb = [
        [KeyboardButton(text="📞 Поделиться телефоном", request_contact=True)],
        [KeyboardButton(text="✏️ Ввести вручную")],
        [KeyboardButton(text="◀️ Назад"), KeyboardButton(text="⏭️ Пропустить")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


# ==================== INLINE КЛАВИАТУРЫ ====================
def get_categories_inline() -> InlineKeyboardMarkup:
    """Inline клавиатура категорий - цифровой выбор"""
    active_categories = ["electronics", "clothing", "home", "hobbies", "free"]

    buttons = []
    for idx, cat_key in enumerate(active_categories, 1):
        cat = CATEGORIES[cat_key]
        buttons.append([
            InlineKeyboardButton(
                text=f"{idx}. {cat['emoji']} {cat['title']}",
                callback_data=f"cat:{cat_key}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirmation_kb() -> InlineKeyboardMarkup:
    """Inline клавиатура подтверждения"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="confirm_no")
        ]
    ])


def get_filters_kb() -> InlineKeyboardMarkup:
    """Клавиатура фильтров для поиска"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Радиус: 10 км", callback_data="filter_radius")],
        [InlineKeyboardButton(text="💰 Цена: любая", callback_data="filter_price")],
        [InlineKeyboardButton(text="📸 Только с фото", callback_data="filter_photo")],
        [InlineKeyboardButton(text="✅ Применить", callback_data="apply_filters")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="cancel_filters")]
    ])


def get_radius_kb(current_radius: int = 10) -> InlineKeyboardMarkup:
    """Выбор радиуса поиска"""
    radiuses = [1, 3, 5, 10, 25, 50, 100]
    buttons = []

    row = []
    for r in radiuses:
        check = "✅ " if r == current_radius else ""
        row.append(InlineKeyboardButton(
            text=f"{check}{r}км",
            callback_data=f"radius:{r}"
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_filters")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_price_kb(current_filter: str = "any") -> InlineKeyboardMarkup:
    """Выбор ценового диапазона"""
    prices = [
        ("any", "Любая"),
        ("free", "🎁 Бесплатно"),
        ("1000", "До 1 000₽"),
        ("5000", "До 5 000₽"),
        ("10000", "До 10 000₽"),
        ("10000+", "Больше 10 000₽")
    ]

    buttons = []
    for key, label in prices:
        check = "✅ " if key == current_filter else ""
        buttons.append([InlineKeyboardButton(
            text=f"{check}{label}",
            callback_data=f"price:{key}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_filters")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)