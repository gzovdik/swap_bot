# -*- coding: utf-8 -*-
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config.constants import CATEGORIES, CATEGORY_BUTTONS, TEXT_TO_CATEGORY


def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню"""
    kb = [
        [KeyboardButton(text="🔥 Смотреть объявления")],
        [KeyboardButton(text="➕ Создать объявление")],
        [KeyboardButton(text="💬 Мои предложения"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="⚙️ Настройки")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_location_request_kb() -> ReplyKeyboardMarkup:
    """Клавиатура для запроса местоположения"""
    kb = [
        [KeyboardButton(text="📍 Поделиться местоположением", request_location=True)],
        [KeyboardButton(text="⏭️ Пропустить")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def get_phone_request_kb() -> ReplyKeyboardMarkup:
    """Клавиатура для запроса телефона"""
    kb = [
        [KeyboardButton(text="📞 Поделиться телефоном", request_contact=True)],
        [KeyboardButton(text="✏️ Ввести вручную")],
        [KeyboardButton(text="⏭️ Пропустить")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def get_cancel_kb() -> ReplyKeyboardMarkup:
    """Клавиатура отмены"""
    kb = [[KeyboardButton(text="❌ Отменить")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_back_kb() -> ReplyKeyboardMarkup:
    """Клавиатура возврата"""
    kb = [[KeyboardButton(text="◀️ Назад")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_categories_kb(include_back: bool = True) -> ReplyKeyboardMarkup:
    """Клавиатура с категориями"""
    categories = list(CATEGORY_BUTTONS.values())

    # Создаём по 2 кнопки в ряд
    kb_rows = []
    for i in range(0, len(categories), 2):
        if i + 1 < len(categories):
            kb_rows.append([
                KeyboardButton(text=categories[i]),
                KeyboardButton(text=categories[i + 1])
            ])
        else:
            kb_rows.append([KeyboardButton(text=categories[i])])

    if include_back:
        kb_rows.append([KeyboardButton(text="◀️ Назад")])

    return ReplyKeyboardMarkup(keyboard=kb_rows, resize_keyboard=True)


def get_confirmation_kb() -> InlineKeyboardMarkup:
    """Inline клавиатура подтверждения"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="confirm_no")
        ]
    ])


def get_skip_kb() -> ReplyKeyboardMarkup:
    """Клавиатура пропуска"""
    kb = [
        [KeyboardButton(text="⏭️ Пропустить")],
        [KeyboardButton(text="❌ Отменить")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)