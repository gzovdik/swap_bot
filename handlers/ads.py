# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.models import AdModel, UserModel
from keyboards.main_menu import (get_categories_kb, get_skip_kb, get_main_menu,
                                 get_location_request_kb, get_confirmation_kb)
from states.user_states import CreateAdStates
from config.constants import TEXT_TO_CATEGORY, CATEGORIES, MESSAGES
from utils.validators import validate_title, validate_description, validate_price
from utils.formatters import format_ad_text

router = Router()


@router.message(F.text == "➕ Создать объявление")
async def start_create_ad(message: Message, state: FSMContext):
    """Начало создания объявления"""
    await state.clear()
    await state.set_state(CreateAdStates.choosing_category)

    await message.answer(
        "📂 <b>Создание объявления</b>\n\nВыберите категорию товара:",
        reply_markup=get_categories_kb()
    )


@router.message(CreateAdStates.choosing_category, F.text == "◀️ Назад")
async def cancel_category(message: Message, state: FSMContext):
    """Отмена выбора категории"""
    await state.clear()
    await message.answer("Создание объявления отменено", reply_markup=get_main_menu())


@router.message(CreateAdStates.choosing_category)
async def process_category(message: Message, state: FSMContext):
    """Обработка выбора категории"""
    category_key = TEXT_TO_CATEGORY.get(message.text)

    if not category_key:
        await message.answer("❌ Пожалуйста, выберите категорию из списка:")
        return

    await state.update_data(category=category_key)
    await state.set_state(CreateAdStates.waiting_for_title)

    from aiogram.types import ReplyKeyboardRemove

    await message.answer(
        f"Отлично! Категория: {CATEGORIES[category_key]['emoji']} <b>{CATEGORIES[category_key]['title']}</b>\n\n"
        f"Теперь введите <b>название</b> товара (до 150 символов):",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(CreateAdStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    """Обработка названия"""
    title = validate_title(message.text)

    if not title:
        await message.answer("❌ Название слишком длинное или пустое. Попробуйте ещё раз (до 150 символов):")
        return

    await state.update_data(title=title)
    await state.set_state(CreateAdStates.waiting_for_description)

    await message.answer(
        "✅ Название сохранено!\n\n"
        "Теперь введите <b>описание</b> товара (до 500 символов):"
    )


@router.message(CreateAdStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Обработка описания"""
    description = validate_description(message.text)

    if not description:
        await message.answer("❌ Описание слишком длинное или пустое. Попробуйте ещё раз (до 500 символов):")
        return

    await state.update_data(description=description)

    data = await state.get_data()
    category = data['category']

    # Если категория требует цену
    if CATEGORIES[category]['requires_price']:
        await state.set_state(CreateAdStates.waiting_for_price)
        await message.answer(
            "✅ Описание сохранено!\n\n"
            "Укажите <b>примерную стоимость</b> товара в рублях (или '0' для бесплатного обмена):",
            reply_markup=get_skip_kb()
        )
    else:
        # Категория "Отдам даром" - цена не нужна
        await state.update_data(price=None)
        await state.set_state(CreateAdStates.waiting_for_photo)
        await message.answer(
            "✅ Описание сохранено!\n\n"
            "Пришлите <b>фото</b> товара:"
        )


@router.message(CreateAdStates.waiting_for_price, F.text == "⏭️ Пропустить")
async def skip_price(message: Message, state: FSMContext):
    """Пропуск указания цены"""
    await state.update_data(price=None)
    await state.set_state(CreateAdStates.waiting_for_photo)

    await message.answer(
        "Хорошо, цена не указана (бесплатный обмен)\n\n"
        "Пришлите <b>фото</b> товара:"
    )


@router.message(CreateAdStates.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    """Обработка цены"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer("Создание объявления отменено", reply_markup=get_main_menu())
        return

    price = validate_price(message.text)
    if message.text and message.text.strip() == "0":
        price = None

    if price is None and (not message.text or message.text.strip() != "0"):
        await message.answer(
            "❌ Неверный формат. Введите число (рубли) или 0 для бесплатного обмена:",
            reply_markup=get_skip_kb(),
        )
        return

    await state.update_data(price=price)
    await state.set_state(CreateAdStates.waiting_for_photo)

    price_text = f"{price} ₽" if price else "бесплатный обмен"

    from aiogram.types import ReplyKeyboardRemove

    await message.answer(
        f"✅ Цена: {price_text}\n\nПришлите <b>фото</b> товара:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(CreateAdStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Обработка фото"""
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_id)

    # Спрашиваем про местоположение
    user = await UserModel.get_profile(message.from_user.id)

    if user and user.get("latitude"):
        await state.update_data(
            latitude=user["latitude"],
            longitude=user["longitude"],
            location_name=user.get("location_name") or "",
        )
        await state.set_state(CreateAdStates.confirmation)
        await show_confirmation(message, state)
    else:
        # Просим указать местоположение
        await state.set_state(CreateAdStates.waiting_for_location)
        await message.answer(
            "✅ Фото сохранено!\n\n"
            "📍 Укажите местоположение товара (или пропустите):",
            reply_markup=get_location_request_kb()
        )


@router.message(CreateAdStates.waiting_for_photo)
async def process_no_photo(message: Message, state: FSMContext):
    """Если не прислали фото"""
    await message.answer("❌ Пожалуйста, пришлите фото товара:")


@router.message(CreateAdStates.waiting_for_location, F.location)
async def process_ad_location(message: Message, state: FSMContext):
    """Обработка местоположения для объявления"""
    await state.update_data(
        latitude=message.location.latitude,
        longitude=message.location.longitude,
        location_name=f"Координаты: {message.location.latitude:.4f}, {message.location.longitude:.4f}"
    )

    await state.set_state(CreateAdStates.confirmation)
    await show_confirmation(message, state)


@router.message(CreateAdStates.waiting_for_location, F.text == "⏭️ Пропустить")
async def skip_ad_location(message: Message, state: FSMContext):
    """Пропуск местоположения"""
    # Используем местоположение пользователя
    user = await UserModel.get_profile(message.from_user.id)

    if user['latitude']:
        await state.update_data(
            latitude=user['latitude'],
            longitude=user['longitude'],
            location_name=user['location_name']
        )

    await state.set_state(CreateAdStates.confirmation)
    await show_confirmation(message, state)


async def show_confirmation(message: Message, state: FSMContext):
    """Показ подтверждения создания объявления"""
    data = await state.get_data()

    # Формируем превью объявления
    text = format_ad_text(
        data['title'],
        data['description'],
        data.get('price'),
        data.get('location_name')
    )

    preview_text = f"<b>📋 Предпросмотр объявления:</b>\n\n{text}\n\n<i>Всё верно?</i>"

    if data.get('photo_file_id'):
        await message.answer_photo(
            data['photo_file_id'],
            caption=preview_text,
            reply_markup=get_confirmation_kb()
        )
    else:
        await message.answer(
            preview_text,
            reply_markup=get_confirmation_kb()
        )


@router.callback_query(CreateAdStates.confirmation, F.data == "confirm_yes")
async def confirm_ad_creation(callback: CallbackQuery, state: FSMContext):
    """Подтверждение создания объявления"""
    data = await state.get_data()

    # Создаём объявление
    ad_id = await AdModel.create(
        user_tg_id=callback.from_user.id,
        category=data['category'],
        title=data['title'],
        description=data['description'],
        price=data.get('price'),
        photo_file_id=data.get('photo_file_id'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        location_name=data.get('location_name')
    )

    await state.clear()

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"✅ {MESSAGES['ad_created']}\n\n"
        f"ID объявления: #{ad_id}\n"
        f"Ваше объявление теперь видно другим пользователям!",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.callback_query(CreateAdStates.confirmation, F.data == "confirm_no")
async def cancel_ad_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания объявления"""
    await state.clear()

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "❌ Создание объявления отменено",
        reply_markup=get_main_menu()
    )
    await callback.answer()