
import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import create_engine, select, asc, desc
from sqlalchemy.orm import sessionmaker

from database.models import Event, Base  # Убедитесь, что структура проекта верная
from parser.config import CHANNELS       # Убедитесь, что CHANNELS определён

# Загрузка токена и БД
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "eventdb.sqlite3")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в .env")

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# SQLAlchemy setup
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


# FSM состояния
class FilterStates(StatesGroup):
    cost = State()
    time_willing = State()
    district = State()
    indoor = State()
    paid_sort = State()
    channel = State()


# Главное меню
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Показать 5 последних")],
        [KeyboardButton(text="🔍 Фильтровать")],
    ],
    resize_keyboard=True,
)

cost_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Бесплатно"), KeyboardButton(text="Платно")],
        [KeyboardButton(text="Отмена")],
    ],
    resize_keyboard=True,
)

time_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="≤ 1 час"), KeyboardButton(text="> 1 часа")],
        [KeyboardButton(text="Отмена")],
    ],
    resize_keyboard=True,
)

indoor_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Открытое"), KeyboardButton(text="Закрытое")],
        [KeyboardButton(text="Оба варианта"), KeyboardButton(text="Отмена")],
    ],
    resize_keyboard=True,
)

paid_sort_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="По возрастанию цены"), KeyboardButton(text="По убыванию цены")],
        [KeyboardButton(text="Отмена")],
    ],
    resize_keyboard=True,
)

channel_buttons = [[KeyboardButton(text=ch)] for ch in CHANNELS]
channel_buttons.append([KeyboardButton(text="Все")])
channel_buttons.append([KeyboardButton(text="Отмена")])
channel_kb = ReplyKeyboardMarkup(keyboard=channel_buttons, resize_keyboard=True)


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Я помогу найти мероприятия. Выберите режим:", reply_markup=main_kb)


@dp.message(F.text == "📋 Показать 5 последних" or F.text.contains("Показать 5 последних"))
async def show_latest(message: Message, state: FSMContext):
    session = SessionLocal()
    stmt = select(Event).order_by(desc(Event.date)).limit(5)
    events = session.execute(stmt).scalars().all()
    session.close()

    if not events:
        await message.answer("Нет доступных мероприятий.", reply_markup=main_kb)
        return

    for ev in events:
        price_text = "Бесплатно" if not ev.price or ev.price == 0 else f"Цена: {ev.price}₽"
        text = (
            f"🎫 <b>{ev.title}</b>\n"
            f"{ev.description or ''}\n"
            f"📅 {ev.date}\n"
            f"📍 {ev.location}\n"
            f"{price_text}\n"
            f"{'Открытое' if ev.is_outdoor else 'Закрытое'}\n"
            f"Источник: {ev.source_channel or 'неизвестен'}\n"
        )
        await message.answer(text, parse_mode="HTML")

    await message.answer("Выберите режим:", reply_markup=main_kb)


@dp.message(F.text == "🔍 Фильтровать")
async def start_filter(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите стоимость мероприятия:", reply_markup=cost_kb)
    await state.set_state(FilterStates.cost)


@dp.message(FilterStates.cost)
async def filter_cost(message: Message, state: FSMContext):
    if message.text not in ["Бесплатно", "Платно", "Отмена"]:
        return await message.answer("Выберите из доступных вариантов", reply_markup=cost_kb)
    if message.text == "Отмена":
        await state.clear()
        return await message.answer("Фильтрация отменена.", reply_markup=main_kb)
    await state.update_data(cost=message.text)
    await message.answer("Сколько готовы потратить времени?", reply_markup=time_kb)
    await state.set_state(FilterStates.time_willing)


@dp.message(FilterStates.time_willing)
async def filter_time(message: Message, state: FSMContext):
    if message.text not in ["≤ 1 час", "> 1 часа", "Отмена"]:
        return await message.answer("Выберите из доступных вариантов", reply_markup=time_kb)
    if message.text == "Отмена":
        await state.clear()
        return await message.answer("Фильтрация отменена.", reply_markup=main_kb)
    await state.update_data(time_willing=message.text)
    await message.answer("Введите интересующий район (или «Все»):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(FilterStates.district)


@dp.message(FilterStates.district)
async def filter_district(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        return await message.answer("Фильтрация отменена.", reply_markup=main_kb)
    await state.update_data(district=None if message.text.lower() == "все" else message.text.strip())
    await message.answer("Выберите тип помещения:", reply_markup=indoor_kb)
    await state.set_state(FilterStates.indoor)


@dp.message(FilterStates.indoor)
async def filter_indoor(message: Message, state: FSMContext):
    if message.text not in ["Открытое", "Закрытое", "Оба варианта", "Отмена"]:
        return await message.answer("Выберите из доступных вариантов", reply_markup=indoor_kb)
    if message.text == "Отмена":
        await state.clear()
        return await message.answer("Фильтрация отменена.", reply_markup=main_kb)
    await state.update_data(indoor=message.text)
    data = await state.get_data()
    if data["cost"] == "Платно":
        await message.answer("Выберите сортировку по цене:", reply_markup=paid_sort_kb)
        await state.set_state(FilterStates.paid_sort)
    else:
        await message.answer("Выберите канал:", reply_markup=channel_kb)
        await state.set_state(FilterStates.channel)


@dp.message(FilterStates.paid_sort)
async def filter_paid_sort(message: Message, state: FSMContext):
    if message.text not in ["По возрастанию цены", "По убыванию цены", "Отмена"]:
        return await message.answer("Выберите из доступных вариантов", reply_markup=paid_sort_kb)
    if message.text == "Отмена":
        await state.clear()
        return await message.answer("Фильтрация отменена.", reply_markup=main_kb)
    await state.update_data(paid_sort=message.text)
    await message.answer("Выберите канал:", reply_markup=channel_kb)
    await state.set_state(FilterStates.channel)


@dp.message(FilterStates.channel)
async def filter_channel(message: Message, state: FSMContext):
    if message.text not in CHANNELS + ["Все", "Отмена"]:
        return await message.answer("Выберите из доступных вариантов", reply_markup=channel_kb)
    if message.text == "Отмена":
        await state.clear()
        return await message.answer("Фильтрация отменена.", reply_markup=main_kb)

    data = await state.get_data()
    cost = data["cost"]
    time_willing = data["time_willing"]
    district = data.get("district")
    indoor = data["indoor"]
    paid_sort = data.get("paid_sort")
    selected_channel = message.text

    stmt = select(Event)
    if cost == "Бесплатно":
        stmt = stmt.where((Event.price == None) | (Event.price == 0))
    else:
        stmt = stmt.where(Event.price > 0)
        if paid_sort == "По возрастанию цены":
            stmt = stmt.order_by(asc(Event.price))
        elif paid_sort == "По убыванию цены":
            stmt = stmt.order_by(desc(Event.price))

    if time_willing == "≤ 1 час":
        stmt = stmt.where(Event.duration_minutes <= 60)
    else:
        stmt = stmt.where(Event.duration_minutes > 60)

    if district:
        stmt = stmt.where(Event.district.ilike(f"%{district}%"))

    if indoor == "Открытое":
        stmt = stmt.where(Event.is_outdoor.is_(True))
    elif indoor == "Закрытое":
        stmt = stmt.where(Event.is_outdoor.is_(False))

    if selected_channel != "Все":
        stmt = stmt.where(Event.source_channel == selected_channel)

    if not (cost == "Платно" and paid_sort):
        stmt = stmt.order_by(desc(Event.date))

    stmt = stmt.limit(5)
    session = SessionLocal()
    events = session.execute(stmt).scalars().all()
    session.close()

    if not events:
        await message.answer("Ничего не найдено.", reply_markup=main_kb)
        await state.clear()
        return

    for ev in events:
        price_text = "Бесплатно" if not ev.price or ev.price == 0 else f"Цена: {ev.price}₽"
        text = (
            f"🎫 <b>{ev.title}</b>\n"
            f"{ev.description or ''}\n"
            f"📅 {ev.date}\n"
            f"📍 {ev.location}\n"
            f"{price_text}\n"
            f"{'Открытое' if ev.is_outdoor else 'Закрытое'}\n"
            f"Источник: {ev.source_channel or 'неизвестен'}\n"
        )
        await message.answer(text, parse_mode="HTML")

    await message.answer("Выберите режим:", reply_markup=main_kb)
    await state.clear()


if __name__ == "__main__":
    dp.run_polling(bot)