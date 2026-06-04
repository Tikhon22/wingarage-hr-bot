from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.vacancies import VACANCIES
from data.locations import MOSCOW_LOCATIONS, SPB_LOCATIONS


def get_vacancy_keyboard() -> InlineKeyboardMarkup:
    """Кнопки с вакансиями — берутся из data/vacancies.py"""
    buttons = [
        [InlineKeyboardButton(text=v["name"], callback_data=f"vacancy:{key}")]
        for key, v in VACANCIES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_city_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏙 Москва", callback_data="city:moscow")],
        [InlineKeyboardButton(text="🌊 Санкт-Петербург", callback_data="city:spb")],
    ])


def _build_location_keyboard(locations: dict) -> InlineKeyboardMarkup:
    """Строит клавиатуру из словаря локаций {label: display_name}"""
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"loc:{label}")]
        for label, name in locations.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_moscow_districts_keyboard() -> InlineKeyboardMarkup:
    return _build_location_keyboard(MOSCOW_LOCATIONS)


def get_spb_districts_keyboard() -> InlineKeyboardMarkup:
    return _build_location_keyboard(SPB_LOCATIONS)


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Согласен(а)", callback_data="consent:agree")],
        [InlineKeyboardButton(text="❌ Не согласен(а)", callback_data="consent:decline")],
    ])
