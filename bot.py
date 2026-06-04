import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery

from config import BOT_TOKEN, HR_CHAT_ID
from states import CandidateForm
from keyboards import (
    get_vacancy_keyboard,
    get_city_keyboard,
    get_moscow_districts_keyboard,
    get_spb_districts_keyboard,
    get_confirm_keyboard,
)
from data.vacancies import VACANCIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ─── /start ───────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Привет! Я бот компании <b>ВашаКомпания</b>.\n\n"
        "Помогу подобрать подходящую вакансию и передам ваш контакт "
        "HR-специалисту, который свяжется с вами для записи на собеседование.\n\n"
        "Выберите интересующую вас должность 👇",
        parse_mode="HTML",
        reply_markup=get_vacancy_keyboard(),
    )
    await state.set_state(CandidateForm.choosing_vacancy)


# ─── Шаг 1: выбор вакансии ────────────────────────────────────────────────────

@dp.callback_query(CandidateForm.choosing_vacancy, F.data.startswith("vacancy:"))
async def vacancy_chosen(call: CallbackQuery, state: FSMContext):
    vacancy_key = call.data.split(":", 1)[1]
    vacancy = VACANCIES.get(vacancy_key)
    if not vacancy:
        await call.answer("Неизвестная вакансия")
        return

    await state.update_data(vacancy=vacancy_key, vacancy_name=vacancy["name"])
    await call.message.edit_text(
        f"<b>{vacancy['name']}</b>\n\n"
        f"📋 <b>Обязанности:</b>\n{vacancy['duties']}\n\n"
        f"🕐 <b>График:</b> {vacancy['schedule']}\n"
        f"💰 <b>Зарплата:</b> {vacancy['salary']}\n\n"
        f"📄 <b>Тип занятости:</b> {vacancy['employment_type']}\n"
        f"🎓 <b>Обучение:</b> {vacancy['training']}\n"
        f"📝 <b>Оформление:</b> {vacancy['registration']}\n\n"
        "<b>🗺 Как проходит найм:</b>\n"
        "1️⃣ Оставляете заявку здесь\n"
        "2️⃣ Специалист звонит и рассказывает подробности\n"
        "3️⃣ Собеседование (онлайн или очно)\n"
        "4️⃣ Выход на работу 🎉\n\n"
        "Выберите город 👇",
        parse_mode="HTML",
        reply_markup=get_city_keyboard(),
    )
    await state.set_state(CandidateForm.choosing_city)


# ─── Шаг 2: выбор города ──────────────────────────────────────────────────────

@dp.callback_query(CandidateForm.choosing_city, F.data.startswith("city:"))
async def city_chosen(call: CallbackQuery, state: FSMContext):
    city = call.data.split(":", 1)[1]
    await state.update_data(city=city)

    if city == "moscow":
        kb = get_moscow_districts_keyboard()
        city_label = "Москва"
    else:
        kb = get_spb_districts_keyboard()
        city_label = "Санкт-Петербург"

    await call.message.edit_text(
        f"📍 Город: <b>{city_label}</b>\n\nВыберите район или магазин 👇",
        parse_mode="HTML",
        reply_markup=kb,
    )
    await state.set_state(CandidateForm.choosing_location)


# ─── Шаг 3: выбор локации ─────────────────────────────────────────────────────

@dp.callback_query(CandidateForm.choosing_location, F.data.startswith("loc:"))
async def location_chosen(call: CallbackQuery, state: FSMContext):
    location = call.data.split(":", 1)[1]
    await state.update_data(location=location)

    await call.message.edit_text(
        "✅ Отлично! Почти готово.\n\n"
        "Для связи нам понадобятся ваши контактные данные.\n"
        "Продолжая, вы даёте <b>согласие на обработку персональных данных</b> "
        "(имя и номер телефона) в целях трудоустройства.",
        parse_mode="HTML",
        reply_markup=get_confirm_keyboard(),
    )
    await state.set_state(CandidateForm.waiting_consent)


@dp.callback_query(CandidateForm.waiting_consent, F.data == "consent:agree")
async def consent_given(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "Напишите своё <b>имя</b> 👇",
        parse_mode="HTML",
    )
    await state.set_state(CandidateForm.entering_name)


@dp.callback_query(CandidateForm.waiting_consent, F.data == "consent:decline")
async def consent_declined(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "Понимаем 🙏 Если передумаете — просто напишите /start"
    )


# ─── Шаг 4: имя ───────────────────────────────────────────────────────────────

@dp.message(CandidateForm.entering_name)
async def name_entered(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Пожалуйста, введите корректное имя.")
        return
    await state.update_data(name=name)
    await message.answer(
        f"Приятно познакомиться, <b>{name}</b>! 👋\n\n"
        "Введите ваш <b>номер телефона</b>\n"
        "Пример: +7 900 123 45 67 👇",
        parse_mode="HTML",
    )
    await state.set_state(CandidateForm.entering_phone)


# ─── Шаг 5: телефон → отправка HR ────────────────────────────────────────────

@dp.message(CandidateForm.entering_phone)
async def phone_entered(message: Message, state: FSMContext):
    phone = message.text.strip()
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 10:
        await message.answer(
            "Пожалуйста, введите корректный номер телефона (минимум 10 цифр)."
        )
        return

    await state.update_data(phone=phone)
    data = await state.get_data()

    city_label = "Москва" if data["city"] == "moscow" else "Санкт-Петербург"
    tg_username = f"@{message.from_user.username}" if message.from_user.username else "—"

    # ── Сообщение для HR-специалиста ──────────────────────────────────────────
    hr_message = (
        "🆕 <b>Новый кандидат!</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Имя: <b>{data['name']}</b>\n"
        f"📞 Телефон: <b>{data['phone']}</b>\n"
        f"🏙 Город: <b>{city_label}</b>\n"
        f"📍 Локация: <b>{data['location']}</b>\n"
        f"💼 Вакансия: <b>{data['vacancy_name']}</b>\n"
        f"✈️ Telegram: {tg_username} (ID: <code>{message.from_user.id}</code>)"
    )

    try:
        await bot.send_message(HR_CHAT_ID, hr_message, parse_mode="HTML")
        logger.info(f"Заявка отправлена HR: {data['name']} {data['phone']}")
    except Exception as e:
        logger.error(f"Ошибка отправки заявки HR: {e}")

    await message.answer(
        "🎉 <b>Спасибо!</b>\n\n"
        "Ваша заявка принята. В ближайшее время с вами свяжется "
        "специалист для записи на собеседование.\n\n"
        "Удачи! 🍀\n\n"
        "<i>Хотите выбрать другую вакансию? Напишите /start</i>",
        parse_mode="HTML",
    )
    await state.clear()


# ─── Запуск ───────────────────────────────────────────────────────────────────

async def main():
    logger.info("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
