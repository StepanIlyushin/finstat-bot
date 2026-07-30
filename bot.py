import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token = BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет, я твой финансовый трекер. \n"
        "Отправь мне трату в формате: 500 еда. \n"
        "Если хочешь посмотреть статистику своих трат, нажми /stats"
    )

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
