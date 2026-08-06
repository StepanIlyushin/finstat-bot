import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from handlers import router

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
    
async def main():
    bot = Bot(token = BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    main_menu_commands = [BotCommand(command="/start", description="Запустить бота"), BotCommand(command="/stats", description="Посмотреть статистику"), BotCommand(command="/help", description="Справка"), BotCommand(command="/clear", description="Очистить историю трат")]
    await bot.set_my_commands(main_menu_commands)
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
