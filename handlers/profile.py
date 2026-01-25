# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.models import UserModel, AdModel, RatingModel
from keyboards.main_menu import get_main_menu, get_phone_request_kb, get_location_request_kb, get_back_kb
from keyboards.inline_kb import get_profile_actions_kb
from states.user_states import ProfileStates
from utils.formatters import format_profile_text
from utils.validators import validate_name, validate_phone

router = Router()


@router.message(F.text == "👤 Профиль")
async def view_profile(message: Message, state: FSMContext):
    """Просмотр профиля"""
    await state.clear()

    user = await UserModel.get_profile(message.from_user.id)
    if not user:
        await message.answer("❌ Профиль не найден")
        return

    # Получаем количество объявлений
    ads = await AdModel.get_user_ads(message.from_user.id, active_only=False)
    ads_count = len(ads)

    # Формируем текст профиля
    profile_text = format_profile_text(
        user['name'],
        user['phone'],
        user['location_name'],
        user['rating'],
        user['total_swaps'],
        ads_count
    )

    await message.answer(
        profile_text,
        reply_markup=get_profile_actions_kb(message.from_user.id, is_own=True)
    )


@router.callback_query(F.data == "edit_profile")
async def edit_profile_menu(callback: CallbackQuery):
    """Меню редактирования профиля"""
    await callback.message.edit_text(
        "✏️ <b>Редактирование профиля</b>\n\nВыберите, что хотите изменить:",
        reply_markup=None
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Имя", callback_data="edit_name")],
        [InlineKeyboardButton(text="📞 Телефон", callback_data="edit_phone")],
        [InlineKeyboardButton(text="📍 Местоположение", callback_data="edit_location")],
        [InlineKeyboardButton(text="◀️ Назад к профилю", callback_data="back_to_profile")]
    ])

    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "edit_name")
async def start_edit_name(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования имени"""
    await callback.message.answer(
        "Введите новое имя:",
        reply_markup=get_back_kb()
    )
    await state.set_state(ProfileStates.editing_name)
    await callback.answer()


@router.message(ProfileStates.editing_name)
async def process_new_name(message: Message, state: FSMContext):
    """Обработка нового имени"""
    if message.text == "◀️ Назад":
        await state.clear()
        await view_profile(message, state)
        return

    name = validate_name(message.text)
    if not name:
        await message.answer("❌ Имя слишком длинное или некорректное. Попробуйте ещё раз:")
        return

    await UserModel.update_field(message.from_user.id, 'name', name)
    await state.clear()

    await message.answer(
        f"✅ Имя изменено на: {name}",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "edit_phone")
async def start_edit_phone(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования телефона"""
    await callback.message.answer(
        "📞 Поделитесь телефоном или введите вручную:",
        reply_markup=get_phone_request_kb()
    )
    await state.set_state(ProfileStates.editing_phone)
    await callback.answer()


@router.message(ProfileStates.editing_phone, F.contact)
async def process_new_contact(message: Message, state: FSMContext):
    """Обработка нового контакта"""
    phone = message.contact.phone_number
    await UserModel.update_phone(message.from_user.id, phone)
    await state.clear()

    await message.answer(
        f"✅ Телефон обновлён: {phone}",
        reply_markup=get_main_menu()
    )


@router.message(ProfileStates.editing_phone, F.text.regexp(r'[\d\+\-\(\)\s]+'))
async def process_new_phone_text(message: Message, state: FSMContext):
    """Обработка текстового телефона"""
    phone = validate_phone(message.text)

    if not phone:
        await message.answer("❌ Неверный формат. Попробуйте ещё раз:")
        return

    await UserModel.update_phone(message.from_user.id, phone)
    await state.clear()

    await message.answer(
        f"✅ Телефон обновлён: {phone}",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "edit_location")
async def start_edit_location(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования местоположения"""
    await callback.message.answer(
        "📍 Поделитесь новым местоположением:",
        reply_markup=get_location_request_kb()
    )
    await state.set_state(ProfileStates.editing_location)
    await callback.answer()


@router.message(ProfileStates.editing_location, F.location)
async def process_new_location(message: Message, state: FSMContext):
    """Обработка нового местоположения"""
    latitude = message.location.latitude
    longitude = message.location.longitude

    await UserModel.update_location(
        message.from_user.id,
        latitude,
        longitude,
        f"Координаты: {latitude:.4f}, {longitude:.4f}"
    )
    await state.clear()

    await message.answer(
        "✅ Местоположение обновлено!",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "my_ads")
async def show_my_ads(callback: CallbackQuery):
    """Показ моих объявлений"""
    ads = await AdModel.get_user_ads(callback.from_user.id, active_only=False)

    if not ads:
        await callback.answer("У вас пока нет объявлений", show_alert=True)
        return

    from utils.formatters import escape_html, format_price, format_date
    from config.constants import CATEGORIES

    text = "<b>📋 Ваши объявления:</b>\n\n"

    for ad in ads[:10]:  # Показываем первые 10
        status = "🟢" if ad['is_active'] else "🔴"
        cat_title = CATEGORIES[ad['category']]['emoji']

        text += f"{status} <b>{escape_html(ad['title'])}</b>\n"
        text += f"   {cat_title} {format_price(ad['price'])} | 👁 {ad['views']}\n"
        text += f"   <small>{format_date(ad['created_at'])}</small>\n\n"

    if len(ads) > 10:
        text += f"<i>...и ещё {len(ads) - 10}</i>"

    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery, state: FSMContext):
    """Возврат к профилю"""
    await state.clear()

    user = await UserModel.get_profile(callback.from_user.id)
    if not user:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return
    ads = await AdModel.get_user_ads(callback.from_user.id, active_only=False)

    profile_text = format_profile_text(
        user['name'],
        user['phone'],
        user['location_name'],
        user['rating'],
        user['total_swaps'],
        len(ads)
    )

    await callback.message.edit_text(
        profile_text,
        reply_markup=get_profile_actions_kb(callback.from_user.id, is_own=True)
    )
    await callback.answer()


@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message):
    """Показ статистики пользователя"""
    user = await UserModel.get_profile(message.from_user.id)
    if not user:
        await message.answer("❌ Профиль не найден. Нажмите /start")
        return
    ads = await AdModel.get_user_ads(message.from_user.id, active_only=False)
    rating, reviews_count = await RatingModel.get_user_ratings(message.from_user.id)

    from utils.formatters import format_rating

    text = f"""
📊 <b>Ваша статистика</b>

<b>Рейтинг:</b> {format_rating(rating)}
<b>Отзывов:</b> {reviews_count}
<b>Обменов:</b> {user['total_swaps']}
<b>Объявлений:</b> {len(ads)}

<b>Активных:</b> {sum(1 for ad in ads if ad['is_active'])}
<b>Неактивных:</b> {sum(1 for ad in ads if not ad['is_active'])}
<b>Всего просмотров:</b> {sum(ad['views'] for ad in ads)}
"""

    await message.answer(text)