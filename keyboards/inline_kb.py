# -*- coding: utf-8 -*-
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Tuple
from config.constants import CATEGORIES


def get_ad_actions_kb(ad_id: int, show_favorite: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура действий с объявлением"""
    buttons = [
        [InlineKeyboardButton(text="❤️ Предложить обмен", callback_data=f"propose:{ad_id}")],
        [InlineKeyboardButton(text="👤 Профиль автора", callback_data=f"profile:{ad_id}")]
    ]

    if show_favorite:
        buttons.append([InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav:{ad_id}")])

    buttons.append([
        InlineKeyboardButton(text="👎 Далее", callback_data="skip"),
        InlineKeyboardButton(text="🚪 Выйти", callback_data="exit_browse")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_my_ads_selection_kb(ads: List[Tuple[int, str, str]]) -> InlineKeyboardMarkup:
    """Клавиатура выбора своего объявления для обмена"""
    buttons = []

    for ad_id, title, category in ads:
        cat_emoji = CATEGORIES[category]['emoji']
        short_title = title[:25] + "..." if len(title) > 25 else title
        buttons.append([
            InlineKeyboardButton(
                text=f"{cat_emoji} {short_title}",
                callback_data=f"select_ad:{ad_id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_swap_actions_kb(swap_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с предложением обмена"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"accept:{swap_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline:{swap_id}")
        ],
        [InlineKeyboardButton(text="👤 Профиль", callback_data=f"swap_profile:{swap_id}")]
    ])


def get_rating_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора оценки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐", callback_data="rate:1"),
            InlineKeyboardButton(text="⭐⭐", callback_data="rate:2"),
            InlineKeyboardButton(text="⭐⭐⭐", callback_data="rate:3")
        ],
        [
            InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rate:4"),
            InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rate:5")
        ]
    ])


def get_profile_actions_kb(user_id: int, is_own: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура действий с профилем"""
    if is_own:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile")],
            [InlineKeyboardButton(text="📋 Мои объявления", callback_data="my_ads")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Объявления", callback_data=f"user_ads:{user_id}")],
            [InlineKeyboardButton(text="📊 Отзывы", callback_data=f"reviews:{user_id}")]
        ])


def get_my_ad_actions_kb(ad_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Клавиатура действий с моим объявлением"""
    status_btn = InlineKeyboardButton(
        text="✅ Активировать" if not is_active else "⏸ Деактивировать",
        callback_data=f"toggle:{ad_id}"
    )

    return InlineKeyboardMarkup(inline_keyboard=[
        [status_btn],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{ad_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{ad_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_my_ads")]
    ])


def get_pagination_kb(current_page: int, total_pages: int, prefix: str = "page") -> InlineKeyboardMarkup:
    """Клавиатура пагинации"""
    buttons = []

    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"{prefix}:{current_page - 1}"))

    nav_buttons.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="ignore"))

    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"{prefix}:{current_page + 1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)