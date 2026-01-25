# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.models import UserModel, AdModel, RatingModel
from keyboards.main_menu import (
    get_main_menu, get_profile_menu, get_settings_menu,
    get_phone_request_kb, get_location_request_kb, 
    get_create_back_only, get_my_ads_menu
)
from keyboards.inline_kb import get_my_ad_actions_kb
from states.user_states import ProfileStates
from utils.formatters import format_rating, escape_html, format_phone, format_price, format_date
from utils.validators import validate_name, validate_phone
from config.constants import CATEGORIES

router = Router()


@router.message(F.text == "👤 Профиль")
async def view_profile(message: Message, state: FSMContext):
    """Просмотр профиля - 2 сообщения"""
    await state.clear()

    try:
        user = await UserModel.get_profile(message.from_user.id)
        if not user:
            await message.answer("❌ Профиль не найден. Нажмите /start")
            return

        ads = await AdModel.get_user_ads(message.from_user.id, active_only=False)
        rating, reviews_count = await RatingModel.get_user_ratings(message.from_user.id)
    except Exception as e:
        print(f"Ошибка view_profile: {e}")
        await message.answer(f"❌ Ошибка загрузки профиля: {str(e)}")
        return

    # Сообщение 1: Профиль со статистикой
    active_ads = sum(1 for ad in ads if ad['is_active'])
    total_views = sum(ad['views'] for ad in ads)

    profile_text = f"""
👤 <b>Ваш профиль</b>

<b>Имя:</b> {escape_html(user['name'])}
<b>Телефон:</b> {format_phone(user['phone'])}
<b>Локация:</b> {escape_html(user['location_name']) if user.get('location_name') else 'не указана'}

📊 <b>Статистика:</b>
• Рейтинг: {format_rating(rating)} ({reviews_count} отзывов)
• Обменов: {user['total_swaps']}
• Объявлений: {len(ads)} (активных: {active_ads})
• Всего просмотров: {total_views}
"""

    await message.answer(profile_text)

    # Сообщение 2: Выбор действий с меню внизу
    menu_text = """
<b>Выберите действие:</b>

1️⃣ Мои объявления
2️⃣ Редактировать профиль
3️⃣ Настройки
4️⃣ Назад
"""

    await message.answer(menu_text, reply_markup=get_profile_menu())


@router.message(F.text == "1", ProfileStates.viewing_profile | F.state is None)
@router.message(F.text == "1")
async def profile_action_1(message: Message, state: FSMContext):
    """1️⃣ Мои объявления"""
    # Проверяем контекст - если мы в профиле
    current_state = await state.get_state()
    
    # Если мы не в профиле и не в начальном состоянии, игнорируем
    # Это нужно чтобы цифра "1" работала только в нужных местах
    
    try:
        ads = await AdModel.get_user_ads(message.from_user.id, active_only=False)
    except Exception as e:
        print(f"Ошибка get_user_ads: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")
        return

    if not ads:
        await message.answer("У вас пока нет объявлений", reply_markup=get_profile_menu())
        return

    text = "<b>📋 Ваши объявления:</b>\n\n"

    for idx, ad in enumerate(ads[:10], 1):
        status = "🟢" if ad['is_active'] else "🔴"
        cat_emoji = CATEGORIES[ad['category']]['emoji']

        text += f"{idx}. {status} <b>{escape_html(ad['title'])}</b>\n"
        text += f"   {cat_emoji} {format_price(ad['price'])} | 👁 {ad['views']}\n"
        text += f"   <small>{format_date(ad['created_at'])}</small>\n\n"

    if len(ads) > 10:
        text += f"<i>...и ещё {len(ads) - 10}</i>\n\n"

    text += "\n<b>Что хотите сделать?</b>\n\n"
    text += "1️⃣ Посмотреть детали (введите номер объявления)\n"
    text += "2️⃣ Создать новое\n"
    text += "3️⃣ Назад"

    await message.answer(text, reply_markup=get_my_ads_menu())
    await state.set_state(ProfileStates.viewing_ads)
    await state.update_data(ads_list=[(ad['id'], ad['title']) for ad in ads])


@router.message(F.text == "2")
async def profile_action_2(message: Message, state: FSMContext):
    """2️⃣ Редактировать профиль"""
    edit_text = """
✏️ <b>Редактирование профиля</b>

Что хотите изменить?

1️⃣ Имя
2️⃣ Телефон
3️⃣ Местоположение
4️⃣ Назад
"""

    await message.answer(edit_text, reply_markup=get_settings_menu())
    await state.set_state(ProfileStates.editing_menu)


@router.message(F.text == "3")
async def profile_action_3(message: Message, state: FSMContext):
    """3️⃣ Настройки или Назад (в зависимости от контекста)"""
    current_state = await state.get_state()
    
    if current_state == ProfileStates.viewing_ads.state:
        # Назад из моих объявлений
        await view_profile(message, state)
    else:
        # Настройки из главного меню профиля
        settings_text = """
⚙️ <b>Настройки</b>

1️⃣ Уведомления (🔔 Вкл)
2️⃣ Радиус поиска (10 км)
3️⃣ Язык (Русский)
4️⃣ Назад
"""

        await message.answer(settings_text, reply_markup=get_settings_menu())
        await state.set_state(ProfileStates.in_settings)


@router.message(F.text == "4")
async def profile_action_4(message: Message, state: FSMContext):
    """4️⃣ Назад"""
    await state.clear()
    await message.answer("🏠 Главная страница", reply_markup=get_main_menu())


# ==================== РЕДАКТИРОВАНИЕ ПРОФИЛЯ ====================

@router.message(ProfileStates.editing_menu, F.text == "1")
async def edit_name(message: Message, state: FSMContext):
    """Редактирование имени"""
    await message.answer(
        "✏️ Введите новое имя:",
        reply_markup=get_create_back_only()
    )
    await state.set_state(ProfileStates.editing_name)


@router.message(ProfileStates.editing_name, F.text == "◀️ Назад")
async def cancel_edit_name(message: Message, state: FSMContext):
    """Отмена редактирования имени"""
    await profile_action_2(message, state)


@router.message(ProfileStates.editing_name)
async def process_new_name(message: Message, state: FSMContext):
    """Обработка нового имени"""
    name = validate_name(message.text)
    if not name:
        await message.answer("❌ Имя слишком длинное или некорректное. Попробуйте ещё раз:")
        return

    try:
        await UserModel.update_field(message.from_user.id, 'name', name)
    except Exception as e:
        print(f"Ошибка update_field: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")
        return

    await message.answer(f"✅ Имя изменено на: {name}")
    await profile_action_2(message, state)


@router.message(ProfileStates.editing_menu, F.text == "2")
async def edit_phone(message: Message, state: FSMContext):
    """Редактирование телефона"""
    await message.answer(
        "📞 Поделитесь телефоном или введите вручную:",
        reply_markup=get_phone_request_kb()
    )
    await state.set_state(ProfileStates.editing_phone)


@router.message(ProfileStates.editing_phone, F.text == "◀️ Назад")
async def cancel_edit_phone(message: Message, state: FSMContext):
    """Отмена редактирования телефона"""
    await profile_action_2(message, state)


@router.message(ProfileStates.editing_phone, F.contact)
async def process_new_contact(message: Message, state: FSMContext):
    """Обработка нового контакта"""
    phone = message.contact.phone_number

    try:
        await UserModel.update_phone(message.from_user.id, phone)
    except Exception as e:
        print(f"Ошибка update_phone: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")
        return

    await message.answer(f"✅ Телефон обновлён: {phone}")
    await profile_action_2(message, state)


@router.message(ProfileStates.editing_phone, F.text == "✏️ Ввести вручную")
async def manual_phone_edit(message: Message):
    """Ручной ввод телефона"""
    await message.answer("Введите номер в формате: +79991234567")


@router.message(ProfileStates.editing_phone, F.text.regexp(r'[\d\+\-\(\)\s]+'))
async def process_new_phone_text(message: Message, state: FSMContext):
    """Обработка текстового телефона"""
    phone = validate_phone(message.text)

    if not phone:
        await message.answer("❌ Неверный формат. Попробуйте ещё раз:")
        return

    try:
        await UserModel.update_phone(message.from_user.id, phone)
    except Exception as e:
        print(f"Ошибка update_phone: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")
        return

    await message.answer(f"✅ Телефон обновлён: {phone}")
    await profile_action_2(message, state)


@router.message(ProfileStates.editing_menu, F.text == "3")
async def edit_location(message: Message, state: FSMContext):
    """Редактирование местоположения"""
    await message.answer(
        "📍 Поделитесь новым местоположением:",
        reply_markup=get_location_request_kb()
    )
    await state.set_state(ProfileStates.editing_location)


@router.message(ProfileStates.editing_location, F.text == "◀️ Назад")
async def cancel_edit_location(message: Message, state: FSMContext):
    """Отмена редактирования местоположения"""
    await profile_action_2(message, state)


@router.message(ProfileStates.editing_location, F.location)
async def process_new_location(message: Message, state: FSMContext):
    """Обработка нового местоположения"""
    latitude = message.location.latitude
    longitude = message.location.longitude

    try:
        await UserModel.update_location(
            message.from_user.id,
            latitude,
            longitude,
            f"Координаты: {latitude:.4f}, {longitude:.4f}"
        )
    except Exception as e:
        print(f"Ошибка update_location: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")
        return

    await message.answer("✅ Местоположение обновлено!")
    await profile_action_2(message, state)


@router.message(ProfileStates.editing_menu, F.text == "4")
async def back_from_editing(message: Message, state: FSMContext):
    """Назад из редактирования"""
    await view_profile(message, state)


# ==================== НАСТРОЙКИ ====================

@router.message(ProfileStates.in_settings, F.text == "1")
async def toggle_notifications(message: Message):
    """Переключение уведомлений"""
    await message.answer("✅ Уведомления включены\n\n(функция в разработке)")


@router.message(ProfileStates.in_settings, F.text == "2")
async def change_radius(message: Message):
    """Изменение радиуса поиска"""
    await message.answer("📍 Радиус поиска изменён на 25 км\n\n(функция в разработке)")


@router.message(ProfileStates.in_settings, F.text == "3")
async def change_language(message: Message):
    """Смена языка"""
    await message.answer("🇷🇺 Язык: Русский\n\n(пока доступен только русский)")


@router.message(ProfileStates.in_settings, F.text == "4")
async def back_from_settings(message: Message, state: FSMContext):
    """Назад из настроек"""
    await view_profile(message, state)