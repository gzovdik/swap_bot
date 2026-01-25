# -*- coding: utf-8 -*-
from aiogram.fsm.state import StatesGroup, State


class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_location = State()
    waiting_for_phone = State()


class CreateAdStates(StatesGroup):
    choosing_category = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_photo = State()
    waiting_for_location = State()
    confirmation = State()


class BrowseAdStates(StatesGroup):
    choosing_category = State()
    showing_ads = State()
    selecting_my_ad = State()
    entering_message = State()


# states/user_states.py
class ProfileStates(StatesGroup):
    viewing_profile = State()
    viewing_ads = State()
    editing_menu = State()
    editing_name = State()
    editing_phone = State()
    editing_location = State()
    in_settings = State()


class SwapStates(StatesGroup):
    viewing_proposals = State()
    accepting_swap = State()
    rating_user = State()
    writing_review = State()