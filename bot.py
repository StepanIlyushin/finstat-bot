import asyncio
import os
import json
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "expenses.json"

bot = Bot(token = BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет, я твой финансовый трекер. \n"
        "Отправь мне трату в формате: 500 еда. Сначала идет сумма, затем категория.\n"
        "Если хочешь посмотреть статистику своих трат, нажми /stats"
    )

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii = False, indent = 4)

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

@dp.message()
async def add_expense(message: types.Message):
    text = message.text
    try:
        parts = text.split()
        amount = int(parts[0])
        category = parts[1]
        user_id = str(message.from_user.id)
        data = load_data()

        if user_id not in data:
            data[user_id] = []

        data[user_id].append({"amount": amount, "category": category})

        save_data(data)

        await message.answer(f"Добавлено: {amount} рублей в категорию {category}")

    except(ValueError, IndexError):
        await message.answer("Ошибка формата ввода! Напиши так: 500 еда. Сначала идет сумма, затем категория.")

if __name__ == "__main__":
    asyncio.run(main())
