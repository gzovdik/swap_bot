# -*- coding: utf-8 -*-
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from app.database.models import AdModel, UserModel, SwapModel, FavoriteModel
from app.keyboards.main_menu import get_categories_inline, get_main_menu, get_browse_menu, get_filters_kb
from app.keyboards.inline_kb import get_ad_actions_kb, get_my_ads_selection_kb
from app.states.user_states import BrowseAdStates
from app.config import constants
from app.utils.formatters import format_ad_text, escape_html

CATEGORIES = constants.CATEGORIES
MESSAGES = constants.MESSAGES
SWAP_STATUS_PENDING = constants.SWAP_STATUS_PENDING

router = Router()


@router.message(F.text == "🔥 Смотреть объявления")
async def start_browse(message: Message, state: FSMContext):
    """Начало просмотра объявлений"""
    await state.clear()
    await state.set_state(BrowseAdStates.choosing_category)

    await message.answer("🔥 <b>Просмотр объявлений</b>\n\nВыберите категорию:")
    await message.answer(
        "Выберите категорию цифрой (1-5):",
        reply_markup=get_categories_inline()
    )


@router.callback_query(BrowseAdStates.choosing_category, F.data == "cancel")
async def cancel_browse_category(callback: CallbackQuery, state: FSMContext):
    """Отмена выбора категории"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Возврат в главное меню", reply_markup=get_main_menu())
    await callback.answer()


@router.callback_query(BrowseAdStates.choosing_category, F.data.startswith("cat:"))
async def process_browse_category(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории для просмотра"""
    category_key = callback.data.split(":")[1]

    if category_key not in CATEGORIES:
        await callback.answer("❌ Неверная категория", show_alert=True)
        return

    # Получаем местоположение пользователя
    user = await UserModel.get_profile(callback.from_user.id)

    await state.update_data(
        category=category_key,
        last_ad_id=0,
        user_lat=user.get('latitude') if user else None,
        user_lon=user.get('longitude') if user else None,
        radius_filter=10,  # По умолчанию 10 км
        price_filter="any",  # Любая цена
        photo_only=False  # Показывать все
    )
    await state.set_state(BrowseAdStates.showing_ads)

    await callback.message.delete()
    
    # Показываем первое объявление с меню просмотра
    await show_next_ad(callback.message, state, user_id=callback.from_user.id)
    await callback.answer()


async def show_next_ad(message: Message, state: FSMContext, user_id: Optional[int] = None):
    """Показать следующее объявление"""
    uid = user_id if user_id else message.from_user.id
    data = await state.get_data()

    try:
        ad = await AdModel.get_next_ad(
            category=data["category"],
            viewer_tg_id=uid,
            last_ad_id=data.get("last_ad_id", 0),
            user_lat=data.get("user_lat"),
            user_lon=data.get("user_lon"),
            max_distance_km=data.get("radius_filter", 10)
        )
    except Exception as e:
        print(f"Ошибка get_next_ad: {e}")
        await message.answer(
            f"❌ {MESSAGES['error']}\n\nПодробности: {str(e)}",
            reply_markup=get_main_menu()
        )
        await state.clear()
        return

    if not ad:
        await message.answer(
            f"{MESSAGES['no_ads_found']}\n\nПопробуйте выбрать другую категорию!",
            reply_markup=get_main_menu()
        )
        await state.clear()
        return

    # Применяем фильтры
    price_filter = data.get("price_filter", "any")
    photo_only = data.get("photo_only", False)

    # Фильтр по цене
    if price_filter != "any":
        if price_filter == "free" and ad.get('price'):
            # Пропускаем платные если выбрано "бесплатно"
            await state.update_data(last_ad_id=ad["id"])
            return await show_next_ad(message, state, user_id=uid)
        elif price_filter.endswith("+"):
            max_price = int(price_filter.replace("+", ""))
            if ad.get('price') and int(ad['price']) <= max_price:
                await state.update_data(last_ad_id=ad["id"])
                return await show_next_ad(message, state, user_id=uid)
        elif price_filter.isdigit():
            max_price = int(price_filter)
            if ad.get('price') and int(ad['price']) > max_price:
                await state.update_data(last_ad_id=ad["id"])
                return await show_next_ad(message, state, user_id=uid)

    # Фильтр по фото
    if photo_only and not ad.get('photo_file_id'):
        await state.update_data(last_ad_id=ad["id"])
        return await show_next_ad(message, state, user_id=uid)

    # Увеличиваем просмотры
    try:
        await AdModel.increment_views(ad["id"], uid)
    except Exception as e:
        print(f"Ошибка increment_views: {e}")

    await state.update_data(
        last_ad_id=ad["id"],
        current_ad_id=ad["id"],
        current_ad_owner_id=ad["user_tg_id"],
    )

    # Получаем информацию о владельце
    try:
        owner = await UserModel.get_profile(ad['user_tg_id'])
    except Exception as e:
        print(f"Ошибка get_profile: {e}")
        owner = None

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

    # Отправляем объявление с меню просмотра
    try:
        if ad.get('photo_file_id'):
            await message.answer_photo(
                ad['photo_file_id'],
                caption=text,
                reply_markup=get_browse_menu()
            )
        else:
            await message.answer(text, reply_markup=get_browse_menu())
    except Exception as e:
        print(f"Ошибка отправки объявления: {e}")
        await message.answer(
            f"❌ Ошибка отображения объявления\n\n{str(e)}",
            reply_markup=get_main_menu()
        )
        await state.clear()


# Обработка кнопок меню просмотра
@router.message(BrowseAdStates.showing_ads, F.text == "👎 Далее")
async def skip_ad_text(message: Message, state: FSMContext):
    """Пропустить объявление"""
    await show_next_ad(message, state, user_id=message.from_user.id)


@router.message(BrowseAdStates.showing_ads, F.text == "❤️ Обмен")
async def propose_swap_text(message: Message, state: FSMContext):
    """Предложить обмен через текстовую кнопку"""
    data = await state.get_data()
    ad_id = data.get('current_ad_id')
    
    if not ad_id:
        await message.answer("❌ Объявление не найдено")
        return
    
    await start_propose_swap_internal(message, state, ad_id, message.from_user.id)


@router.message(BrowseAdStates.showing_ads, F.text == "⭐ Избранное")
async def add_to_favorites_text(message: Message, state: FSMContext):
    """Добавить в избранное через текстовую кнопку"""
    data = await state.get_data()
    ad_id = data.get('current_ad_id')
    
    if not ad_id:
        await message.answer("❌ Объявление не найдено")
        return
    
    try:
        success = await FavoriteModel.add(message.from_user.id, ad_id)
        if success:
            await message.answer("⭐ Добавлено в избранное!")
        else:
            await message.answer("ℹ️ Уже в избранном")
    except Exception as e:
        print(f"Ошибка add_to_favorites: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(BrowseAdStates.showing_ads, F.text == "👤 Автор")
async def show_author_text(message: Message, state: FSMContext):
    """Показать профиль автора через текстовую кнопку"""
    data = await state.get_data()
    owner_id = data.get('current_ad_owner_id')
    
    if not owner_id:
        await message.answer("❌ Автор не найден")
        return
    
    try:
        owner = await UserModel.get_profile(owner_id)
        if not owner:
            await message.answer("❌ Профиль не найден")
            return
    except Exception as e:
        print(f"Ошибка get_profile: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")
        return

    from app.utils.formatters import format_rating, format_phone

    profile_text = f"""
👤 <b>Профиль пользователя</b>

<b>Имя:</b> {escape_html(owner['name'])}
<b>Рейтинг:</b> {format_rating(owner['rating'])}
<b>Обменов:</b> {owner['total_swaps']}
<b>Телефон:</b> {format_phone(owner['phone'])}
"""

    await message.answer(profile_text)


@router.message(BrowseAdStates.showing_ads, F.text == "🏠 Главная")
async def exit_browse_text(message: Message, state: FSMContext):
    """Выйти в главное меню"""
    await state.clear()
    await message.answer("Вы вышли из просмотра объявлений", reply_markup=get_main_menu())


async def start_propose_swap_internal(message: Message, state: FSMContext, ad_id: int, user_id: int):
    """Внутренняя функция для предложения обмена"""
    data = await state.get_data()
    category = data['category']

    # Получаем объявления пользователя
    try:
        my_ads = await AdModel.get_user_ads(user_id, active_only=True)
        category_ads = [(ad['id'], ad['title'], ad['category']) for ad in my_ads if ad['category'] == category]
    except Exception as e:
        print(f"Ошибка get_user_ads: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")
        return

    if not category_ads:
        await message.answer(
            f"❌ У вас нет активных объявлений в категории «{CATEGORIES[category]['title']}»\n\n"
            f"Сначала создайте объявление!",
            reply_markup=get_browse_menu()
        )
        return

    await state.update_data(
        liked_ad_id=ad_id,
        target_owner_id=data['current_ad_owner_id']
    )
    await state.set_state(BrowseAdStates.selecting_my_ad)

    await message.answer(
        "❤️ <b>Предложение обмена</b>\n\n"
        "Выберите ваше объявление для обмена:",
        reply_markup=get_my_ads_selection_kb(category_ads)
    )


@router.callback_query(BrowseAdStates.selecting_my_ad, F.data.startswith("select_ad:"))
async def select_my_ad_for_swap(callback: CallbackQuery, state: FSMContext):
    """Выбор своего объявления для обмена"""
    my_ad_id = int(callback.data.split(":")[1])
    data = await state.get_data()

    # Создаём предложение обмена
    try:
        success, swap_id = await SwapModel.create(
            liked_ad_id=data['liked_ad_id'],
            proposer_ad_id=my_ad_id,
            proposer_user_id=callback.from_user.id,
            target_user_id=data['target_owner_id']
        )
    except Exception as e:
        print(f"Ошибка create swap: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        return

    if not success:
        await callback.answer("❌ Вы уже отправляли это предложение", show_alert=True)
        return

    # Получаем детали для уведомления
    try:
        liked_ad = await AdModel.get_by_id(data['liked_ad_id'])
        my_ad = await AdModel.get_by_id(my_ad_id)
        proposer = await UserModel.get_profile(callback.from_user.id)
    except Exception as e:
        print(f"Ошибка получения данных: {e}")

    # Отправляем уведомление владельцу
    try:
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from app.config import settings as app_settings

        bot = Bot(
            token=app_settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

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

    await callback.message.edit_text(f"✅ {MESSAGES['swap_sent']}\n\nВладелец получит уведомление.")
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

    try:
        incoming = await SwapModel.get_incoming(message.from_user.id, SWAP_STATUS_PENDING)
        outgoing = await SwapModel.get_outgoing(message.from_user.id)
    except Exception as e:
        print(f"Ошибка get proposals: {e}")
        await message.answer(f"❌ {MESSAGES['error']}\n\n{str(e)}")
        return

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

    await message.answer(text, reply_markup=get_main_menu())