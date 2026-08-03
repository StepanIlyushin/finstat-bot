import asyncio
import os
import json
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "expenses.json"

bot = Bot(token = BOT_TOKEN)
dp = Dispatcher()

class FSM(StatesGroup):
    waiting_for_category = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет, я твой финансовый трекер. \n"
        "Отправь мне сумму траты (например, 500), и я предложу тебе выбрать категорию.\n"
        "Если хочешь посмотреть статистику своих трат, нажми /stats.\n"
        "Если хочешь посмотреть основные возможности бота, нажми /help."
    )

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii = False, indent = 4)

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data or not data[user_id]:
        await message.answer("У тебя пока нет записей о тратах")
        return

    user_expenses = data[user_id]
    total_spent =  sum(item["amount"] for item in user_expenses)

    category_sums = {}
    for item in user_expenses:
        cat = item["category"]
        amt = item["amount"]
        if cat in category_sums:
            category_sums[cat] += amt
        else:
            category_sums[cat] = amt

    response_text = "Твоя статистика трат: \n\n"

    for cat, amt in category_sums.items():
        response_text += f"{cat.capitalize()} : {amt} рублей \n"

    response_text += f"\nВсего потрачено: {total_spent} рублей"

    await message.answer(response_text)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Вот что я умею: \n\n"
        "1. Отправь мне число (например, 500), чтобы записать трату, затем выбери подходящую категорию.\n"
        "2. /stats - посмотреть статистику трат. \n"
        "3. /help - помощь по использованию бота.\n"
        "4. /clear - очистить историю трат."
        )

@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or not data[user_id]: 
        await message.answer("У тебя пока нет записей о тратах.")
        return
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_clear"),InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_clear")]])
        await message.answer("Ты уверен, что хочешь удалить записи о тратах? Потом их нельзя будет вернуть!", reply_markup=kb)

@dp.callback_query(F.data == "cancel_clear")
async def cmd_cancel_clear(callback: types.CallbackQuery):
    await callback.message.edit_text("Действие отменено.")
    await callback.answer()

@dp.callback_query(F.data == "confirm_clear")
async def cmd_confirm_clear(callback: types.CallbackQuery):
    data = load_data()
    user_id = str(callback.from_user.id)
    if user_id in data:
        del data[user_id]
        save_data(data)
        await callback.message.edit_text("История трат очищена.")
    else:
        await callback.message.edit_text("История трат уже пуста.")
    await callback.answer()

@dp.message(F.text.regexp(r'^\d+$'))
async def process_amount(message: types.Message, state: FSMContext):
    amount = int(message.text)

    await state.update_data(amount=amount)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🍕 Еда", callback_data="cat_еда"),InlineKeyboardButton(text="🚕 Транспорт", callback_data="cat_транспорт")], [InlineKeyboardButton(text="🎬 Развлечения", callback_data="cat_развлечения"), InlineKeyboardButton(text="👕 Одежда", callback_data="cat_одежда")], [InlineKeyboardButton(text="💊 Здоровье", callback_data="cat_здоровье"), InlineKeyboardButton(text="🛒 Прочее", callback_data="cat_прочее")]])
    await message.answer("Выбери категорию для этой траты:", reply_markup=kb)
    await state.set_state(FSM.waiting_for_category)

@dp.callback_query(FSM.waiting_for_category, F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[1]
    data_fsm = await state.get_data()
    amount = data_fsm["amount"]
    user_id = str(callback.from_user.id)
    data = load_data()

    if user_id not in data:
        data[user_id] = []

    data[user_id].append({"amount": amount, "category": category})
    save_data(data)

    await callback.message.edit_text(f"Добавлено: {amount} рублей в категорию {category.capitalize()}")
    await callback.answer()
    await state.clear()

@dp.message()
async def fall(message: types.Message):
    await message.answer("Пожалуйста, просто отправь сумму траты числом (например, 500).")
    
async def main():
    main_menu_commands = [BotCommand(command="/start", description="Запустить бота"), BotCommand(command="/stats", description="Посмотреть статистику"), BotCommand(command="/help", description="Справка"), BotCommand(command="/clear", description="Очистить историю трат")]
    await bot.set_my_commands(main_menu_commands)
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
