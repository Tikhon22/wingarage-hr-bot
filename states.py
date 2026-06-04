from aiogram.fsm.state import State, StatesGroup


class CandidateForm(StatesGroup):
    choosing_vacancy = State()
    choosing_city = State()
    choosing_location = State()
    waiting_consent = State()
    entering_name = State()
    entering_phone = State()
