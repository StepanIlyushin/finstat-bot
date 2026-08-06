from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import database as db

router = Router()

def get_prev_month(year: int, month: int) -> str :
    if month == 1:
        return f"{year - 1}-12"
    else:
        return f"{year}-{month - 1:02d}"

def get_next_month(year: int, month: int) -> str :
    if month == 12:
        return f"{year + 1}-1"
    else:
        return f"{year}-{month + 1:02d}"

class FSM(StatesGroup):
    waiting_for_category = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет, я твой финансовый трекер. \n"
        "Отправь мне сумму траты (например, 500) или сумму траты с датой (например, 500 03.08.2026), и я предложу тебе выбрать категорию.\n"
        "Если хочешь посмотреть статистику своих трат, нажми /stats.\n"
        "Если хочешь посмотреть основные возможности бота, нажми /help."
    )


@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = str(message.from_user.id)
    data = db.load_data()
    need_date = datetime.now().strftime("%Y-%m")
    year = datetime.now().year
    month = datetime.now().month
    prev_month = get_prev_month(year, month)
    next_month = get_next_month(year, month)

    if user_id not in data or not data[user_id]:
        await message.answer("У тебя пока нет записей о тратах.")
        return

    user_expenses = data[user_id]
    total_spent =  0

    category_sums = {}
    for item in user_expenses:
        if item["date"].startswith(need_date):
            cat = item["category"]
            amt = item["amount"]
            total_spent += amt
            if cat in category_sums:
                category_sums[cat] += amt
            else:
                category_sums[cat] = amt

    response_text = f"Твоя статистика трат за {need_date}: \n\n"

    for cat, amt in category_sums.items():
        response_text += f"{cat.capitalize()} : {amt} рублей \n"

    response_text += f"\nВсего потрачено: {total_spent} рублей."

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=f"stats_{prev_month}"),InlineKeyboardButton(text="Вперед ➡️", callback_data=f"stats_{next_month}")]])

    await message.answer(response_text, reply_markup=kb)

@router.callback_query(F.data.startswith("stats_"))
async def cmd_stats_mounth(callback: types.CallbackQuery):
    need_date = callback.data.split("_")[1]
    year, month = map(int, need_date.split("-"))
    prev_month = get_prev_month(year, month)
    next_month = get_next_month(year, month)
    data = db.load_data()

    user_id = str(callback.from_user.id)
    if user_id not in data or not data[user_id]:
        await callback.answer("У тебя пока нет записей о тратах.")
        return

    user_expenses = data[user_id]

    category_sums = {}
    total_spent = 0
    for item in user_expenses:
        if item["date"].startswith(need_date):
            cat = item["category"]
            amt = item["amount"]
            total_spent += amt
            if cat in category_sums:
                category_sums[cat] += amt
            else:
                category_sums[cat] = amt

    response_text = f"Твоя статистика трат за {need_date}: \n\n"

    for cat, amt in category_sums.items():
        response_text += f"{cat.capitalize()} : {amt} рублей \n"

    response_text += f"\nВсего потрачено: {total_spent} рублей."

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=f"stats_{prev_month}"),InlineKeyboardButton(text="Вперед ➡️", callback_data=f"stats_{next_month}")]])

    await callback.message.edit_text(response_text, reply_markup=kb)
    await callback.answer()

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Вот что я умею: \n\n"
        "1. Отправь мне число (например, 500) или число с датой (например, 500 03.08.2026), чтобы записать трату, затем выбери подходящую категорию.\n"
        "2. /stats - посмотреть статистику трат. \n"
        "3. /help - помощь по использованию бота.\n"
        "4. /clear - очистить историю трат."
        )

@router.message(Command("clear"))
async def cmd_clear(message: types.Message):
    data = db.load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or not data[user_id]: 
        await message.answer("У тебя пока нет записей о тратах.")
        return
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_clear"),InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_clear")]])
        await message.answer("Ты уверен, что хочешь удалить записи о тратах? Потом их нельзя будет вернуть!", reply_markup=kb)

@router.callback_query(F.data == "cancel_clear")
async def cmd_cancel_clear(callback: types.CallbackQuery):
    await callback.message.edit_text("Действие отменено.")
    await callback.answer()

@router.callback_query(F.data == "confirm_clear")
async def cmd_confirm_clear(callback: types.CallbackQuery):
    data = db.load_data()
    user_id = str(callback.from_user.id)
    if user_id in data:
        del data[user_id]
        db.save_data(data)
        await callback.message.edit_text("История трат очищена.")
    else:
        await callback.message.edit_text("История трат уже пуста.")
    await callback.answer()

@router.message(F.text.regexp(r'^\d+'))
async def process_amount(message: types.Message, state: FSMContext):
    parts = message.text.split()
    amount = int(parts[0])

    if (len(parts) > 1):
        data_input = parts[1]
        try:
            parsed_date = datetime.strptime(data_input, "%d.%m.%Y")
            #храним в таком виде, чтобы потом можно было удобно перенести в SQL
            date_to_save = parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            await message.answer("Неверный формат даты. Пожалуйста, введи только сумму, либо сумму и дату в формате ДД.ММ.ГГГГ (например: 500 03.08.2026)")
            return
    else:
        date_to_save = datetime.now().strftime("%Y-%m-%d")

    await state.update_data(amount=amount, date=date_to_save)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🍕 Еда", callback_data="cat_еда"),InlineKeyboardButton(text="🚕 Транспорт", callback_data="cat_транспорт")], [InlineKeyboardButton(text="🎬 Развлечения", callback_data="cat_развлечения"), InlineKeyboardButton(text="👕 Одежда", callback_data="cat_одежда")], [InlineKeyboardButton(text="💊 Здоровье", callback_data="cat_здоровье"), InlineKeyboardButton(text="🛒 Прочее", callback_data="cat_прочее")]])
    await message.answer("Выбери категорию для этой траты:", reply_markup=kb)
    await state.set_state(FSM.waiting_for_category)

@router.callback_query(FSM.waiting_for_category, F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[1]
    data_fsm = await state.get_data()
    amount = data_fsm["amount"]
    date_to_save = data_fsm["date"]
    user_id = str(callback.from_user.id)
    data = db.load_data()
    if user_id not in data:
        data[user_id] = []

    data[user_id].append({"amount": amount, "category": category, "date": date_to_save})
    db.save_data(data)

    await callback.message.edit_text(f"Добавлено: {amount} рублей в категорию {category.capitalize()} за {date_to_save}")
    await callback.answer()
    await state.clear()

@router.message()
async def fall(message: types.Message):
    await message.answer("Пожалуйста, просто отправь сумму траты числом (например, 500) или с датой (например, 500 03.08.2026).")