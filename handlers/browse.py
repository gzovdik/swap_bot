# -*- coding: utf-8 -*-
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from database.models import AdModel, UserModel, SwapModel
from keyboards.main_menu import get_categories_kb, get_main_menu
from keyboards.inline_kb import get_ad_actions_kb, get_my_ads_selection_kb
from states.user_states import BrowseAdStates
from config.constants import TEXT_TO_CATEGORY, CATEGORIES, MESSAGES, SWAP_STATUS_PENDING
from utils.formatters import format_ad_text, escape_html

router = Router()


@router.message(F.text == "🔥 Смотреть объявления")
async def start_browse(message: Message, state: FSMContext):
    """Начало просмотра объявлений"""
    await state.clear()
    await state.set_state(BrowseAdStates.choosing_category)

    await message.answer(
        "🔥 <b>Просмотр объявлений</b>\n\nВыберите категорию:",
        reply_markup=get_categories_kb()
    )


@router.message(BrowseAdStates.choosing_category, F.text == "◀️ Назад")
async def cancel_browse(message: Message, state: FSMContext):
    """Отмена просмотра"""
    await state.clear()
    await message.answer("Возврат в главное меню", reply_markup=get_main_menu())


@router.message(BrowseAdStates.choosing_category)
async def process_browse_category(message: Message, state: FSMContext):
    """Обработка выбора категории для просмотра"""
    category_key = TEXT_TO_CATEGORY.get(message.text)

    if not category_key:
        await message.answer("❌ Пожалуйста, выберите категорию из списка:")
        return

    # Получаем местоположение пользователя для сортировки по близости
    user = await UserModel.get_profile(message.from_user.id)

    await state.update_data(
        category=category_key,
        last_ad_id=0,
        user_lat=user.get('latitude'),
        user_lon=user.get('longitude')
    )
    await state.set_state(BrowseAdStates.showing_ads)

    await show_next_ad(message, state)


async def show_next_ad(
    message: Message, state: FSMContext, user_id: Optional[int] = None
):
    """Показать следующее объявление. user_id нужен при вызове из callback (message без from_user)."""
    uid = user_id
    if uid is None:
        uid = message.from_user.id if message.from_user else message.chat.id

    data = await state.get_data()

    ad = await AdModel.get_next_ad(
        category=data["category"],
        viewer_tg_id=uid,
        last_ad_id=data.get("last_ad_id", 0),
        user_lat=data.get("user_lat"),
        user_lon=data.get("user_lon"),
    )

    if not ad:
        await message.answer(
            "😔 Больше нет объявлений в этой категории.\n\n"
            "Попробуйте выбрать другую категорию!",
            reply_markup=get_main_menu()
        )
        await state.clear()
        return

    await AdModel.increment_views(ad["id"], uid)

    await state.update_data(
        last_ad_id=ad["id"],
        current_ad_id=ad["id"],
        current_ad_owner_id=ad["user_tg_id"],
    )

    # Получаем информацию о владельце
    owner = await UserModel.get_profile(ad['user_tg_id'])

    # Формируем текст объявления
    text = format_ad_text(
        ad['title'],
        ad['description'],
        ad['price'],
        ad.get('location_name'),
        ad.get('distance'),
        owner['name'] if owner else None,
        owner['rating'] if owner else None
    )

    # Отправляем объявление
    if ad.get('photo_file_id'):
        await message.answer_photo(
            ad['photo_file_id'],
            caption=text,
            reply_markup=get_ad_actions_kb(ad['id'])
        )
    else:
        await message.answer(
            text,
            reply_markup=get_ad_actions_kb(ad['id'])
        )


@router.callback_query(BrowseAdStates.showing_ads, F.data == "skip")
async def skip_ad(callback: CallbackQuery, state: FSMContext):
    """Пропустить объявление"""
    await callback.answer()

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    await show_next_ad(callback.message, state, user_id=callback.from_user.id)


@router.callback_query(BrowseAdStates.showing_ads, F.data == "exit_browse")
async def exit_browse(callback: CallbackQuery, state: FSMContext):
    """Выйти из просмотра"""
    await state.clear()

    await callback.message.answer(
        "Вы вышли из просмотра объявлений",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.callback_query(BrowseAdStates.showing_ads, F.data.startswith("propose:"))
async def start_propose_swap(callback: CallbackQuery, state: FSMContext):
    """Начать предложение обмена"""
    ad_id = int(callback.data.split(":")[1])

    # Получаем объявления пользователя в той же категории
    data = await state.get_data()
    category = data['category']

    my_ads = await AdModel.get_user_ads(callback.from_user.id, active_only=True)

    # Фильтруем по категории
    category_ads = [(ad['id'], ad['title'], ad['category']) for ad in my_ads if ad['category'] == category]

    if not category_ads:
        await callback.answer(
            f"❌ У вас нет активных объявлений в категории {CATEGORIES[category]['title']} для обмена",
            show_alert=True
        )
        return

    await state.update_data(
        liked_ad_id=ad_id,
        target_owner_id=data['current_ad_owner_id']
    )
    await state.set_state(BrowseAdStates.selecting_my_ad)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await callback.message.answer(
        "❤️ <b>Предложение обмена</b>\n\n"
        "Выберите ваше объявление, которое хотите предложить в обмен:",
        reply_markup=get_my_ads_selection_kb(category_ads)
    )
    await callback.answer()


@router.callback_query(BrowseAdStates.selecting_my_ad, F.data.startswith("select_ad:"))
async def select_my_ad_for_swap(callback: CallbackQuery, state: FSMContext):
    """Выбор своего объявления для обмена"""
    my_ad_id = int(callback.data.split(":")[1])
    data = await state.get_data()

    # Создаём предложение обмена
    success, swap_id = await SwapModel.create(
        liked_ad_id=data['liked_ad_id'],
        proposer_ad_id=my_ad_id,
        proposer_user_id=callback.from_user.id,
        target_user_id=data['target_owner_id']
    )

    if not success:
        await callback.answer("❌ Вы уже отправляли это предложение", show_alert=True)
        return

    # Получаем детали для уведомления
    liked_ad = await AdModel.get_by_id(data['liked_ad_id'])
    my_ad = await AdModel.get_by_id(my_ad_id)

    try:
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from config.settings import BOT_TOKEN

        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

        proposer = await UserModel.get_profile(callback.from_user.id)

        notification = (
            f"🔔 <b>Новое предложение обмена!</b>\n\n"
            f"Пользователь <b>{escape_html(proposer['name'])}</b> предлагает обменять:\n\n"
            f"<b>{escape_html(my_ad['title'])}</b>\n"
            f"на ваш товар:\n"
            f"<b>{escape_html(liked_ad['title'])}</b>\n\n"
            f"Посмотрите в разделе «💬 Мои предложения»"
        )

        await bot.send_message(data['target_owner_id'], notification)
        await bot.session.close()
    except Exception as e:
        print(f"Не удалось отправить уведомление: {e}")

    # Возвращаемся к просмотру
    await state.set_state(BrowseAdStates.showing_ads)

    await callback.message.edit_text(
        f"✅ {MESSAGES['swap_sent']}\n\n"
        f"Владелец получит уведомление о вашем предложении."
    )
    await callback.answer()

    await show_next_ad(callback.message, state, user_id=callback.from_user.id)


@router.callback_query(BrowseAdStates.selecting_my_ad, F.data == "cancel")
async def cancel_swap_proposal(callback: CallbackQuery, state: FSMContext):
    """Отмена предложения обмена"""
    await state.set_state(BrowseAdStates.showing_ads)

    await callback.message.edit_text("❌ Предложение обмена отменено")
    await callback.answer()

    await show_next_ad(callback.message, state, user_id=callback.from_user.id)


@router.message(F.text == "💬 Мои предложения")
async def show_my_proposals(message: Message, state: FSMContext):
    """Показать мои предложения обмена"""
    await state.clear()

    # Получаем входящие предложения
    incoming = await SwapModel.get_incoming(message.from_user.id, SWAP_STATUS_PENDING)

    # Получаем исходящие предложения
    outgoing = await SwapModel.get_outgoing(message.from_user.id)

    if not incoming and not outgoing:
        await message.answer(
            "📭 У вас пока нет предложений обмена.\n\n"
            "Начните просматривать объявления и предлагайте обмен!",
            reply_markup=get_main_menu()
        )
        return

    text = "<b>💬 Ваши предложения</b>\n\n"

    if incoming:
        text += "<b>📥 Входящие:</b>\n"
        for swap in incoming[:5]:
            text += f"• {escape_html(swap['their_ad_title'])} → {escape_html(swap['my_ad_title'])}\n"
        text += "\n"

    if outgoing:
        text += "<b>📤 Исходящие:</b>\n"
        for swap in outgoing[:5]:
            status_emoji = {"pending": "⏳", "accepted": "✅", "declined": "❌"}.get(swap['status'], "❓")
            text += f"{status_emoji} {escape_html(swap['my_ad_title'])} → {escape_html(swap['their_ad_title'])}\n"

    await message.answer(text)


@router.callback_query(F.data.startswith("profile:"))
async def show_ad_owner_profile(callback: CallbackQuery):
    """Показать профиль владельца объявления"""
    ad_id = int(callback.data.split(":")[1])

    ad = await AdModel.get_by_id(ad_id)
    if not ad:
        await callback.answer("❌ Объявление не найдено", show_alert=True)
        return

    owner = await UserModel.get_profile(ad['user_tg_id'])
    if not owner:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return

    from utils.formatters import format_rating, format_phone

    profile_text = f"""
👤 <b>Профиль пользователя</b>

<b>Имя:</b> {escape_html(owner['name'])}
<b>Рейтинг:</b> {format_rating(owner['rating'])}
<b>Обменов:</b> {owner['total_swaps']}
<b>Телефон:</b> {format_phone(owner['phone'])}
"""

    await callback.message.answer(profile_text)
    await callback.answer()