# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.models import UserModel
from keyboards.main_menu import get_main_menu, get_location_request_kb, get_phone_request_kb
from states.user_states import RegistrationStates
from config.constants import MESSAGES
from utils.validators import validate_phone

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start"""
    await state.clear()

    user = await UserModel.get_or_create(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name or "Пользователь"
    )

    # Если пользователь новый и не указал местоположение
    if not user['latitude']:
        await message.answer(MESSAGES['welcome'])
        await message.answer(
            "📍 Пожалуйста, поделитесь своим местоположением, чтобы находить товары рядом с вами:",
            reply_markup=get_location_request_kb()
        )
        await state.set_state(RegistrationStates.waiting_for_location)
    else:
        await message.answer(
            f"С возвращением, {user['name']}! 👋\n\n🏠 Главная страница",
            reply_markup=get_main_menu()
        )


@router.message(RegistrationStates.waiting_for_location, F.location)
async def process_location(message: Message, state: FSMContext):
    """Обработка местоположения"""
    latitude = message.location.latitude
    longitude = message.location.longitude

    await UserModel.update_location(
        message.from_user.id,
        latitude,
        longitude,
        f"Координаты: {latitude:.4f}, {longitude:.4f}"
    )

    await message.answer(MESSAGES['location_saved'])
    await message.answer(
        "📞 Теперь укажите ваш телефон, чтобы другие пользователи могли связаться с вами:",
        reply_markup=get_phone_request_kb()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_location, F.text == "⏭️ Пропустить")
async def skip_location(message: Message, state: FSMContext):
    """Пропуск указания местоположения"""
    await message.answer(
        "📞 Укажите ваш телефон, чтобы другие пользователи могли связаться с вами:",
        reply_markup=get_phone_request_kb()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_location, F.text == "◀️ Назад")
async def back_from_reg_location(message: Message, state: FSMContext):
    """Назад из регистрации"""
    await state.clear()
    await message.answer("Регистрация отменена. Нажмите /start для начала", reply_markup=get_main_menu())


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_contact(message: Message, state: FSMContext):
    """Обработка контакта"""
    phone = message.contact.phone_number

    await UserModel.update_phone(message.from_user.id, phone)

    await state.clear()
    await message.answer(
        "✅ Отлично! Регистрация завершена.\n\n🏠 Главная страница\n\nТеперь вы можете создавать объявления и искать товары для обмена!",
        reply_markup=get_main_menu()
    )


@router.message(RegistrationStates.waiting_for_phone, F.text == "✏️ Ввести вручную")
async def manual_phone_input(message: Message, state: FSMContext):
    """Ручной ввод телефона"""
    await message.answer("Введите ваш номер телефона в формате: +79991234567")


@router.message(RegistrationStates.waiting_for_phone, F.text.regexp(r'[\d\+\-\(\)\s]+'))
async def process_phone_text(message: Message, state: FSMContext):
    """Обработка текстового ввода телефона"""
    phone = validate_phone(message.text)

    if not phone:
        await message.answer(
            "❌ Неверный формат телефона. Попробуйте ещё раз.\n\nПример: +79991234567",
            reply_markup=get_phone_request_kb()
        )
        return

    await UserModel.update_phone(message.from_user.id, phone)

    await state.clear()
    await message.answer(
        "✅ Отлично! Регистрация завершена.\n\n🏠 Главная страница\n\nТеперь вы можете создавать объявления и искать товары для обмена!",
        reply_markup=get_main_menu()
    )


@router.message(RegistrationStates.waiting_for_phone, F.text == "⏭️ Пропустить")
async def skip_phone(message: Message, state: FSMContext):
    """Пропуск указания телефона"""
    await state.clear()
    await message.answer(
        "Вы можете указать телефон позже в настройках профиля.\n\n🏠 Главная страница\n\nДобро пожаловать!",
        reply_markup=get_main_menu()
    )


@router.message(RegistrationStates.waiting_for_phone, F.text == "◀️ Назад")
async def back_from_reg_phone(message: Message, state: FSMContext):
    """Назад к местоположению"""
    await message.answer(
        "📍 Поделитесь своим местоположением:",
        reply_markup=get_location_request_kb()
    )
    await state.set_state(RegistrationStates.waiting_for_location)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    help_text = """
<b>📖 Справка по боту</b>

<b>Основные возможности:</b>
🔥 <b>Смотреть объявления</b> - просмотр товаров для обмена
➕ <b>Создать объявление</b> - размещение своего товара
💬 <b>Мои предложения</b> - входящие и исходящие предложения
👤 <b>Профиль</b> - управление вашими данными

<b>Как это работает:</b>
1. Создайте объявление о товаре
2. Просматривайте ленту других объявлений
3. Предложите обмен, если нашли интересный товар
4. Договоритесь о встрече с владельцем
5. Оцените сделку после обмена

<b>Советы:</b>
• Укажите реальное местоположение для поиска товаров рядом
• Добавьте качественное фото товара
• Подробно опишите состояние вещи
• Будьте вежливы при общении

По вопросам: @support
"""
    await message.answer(help_text)