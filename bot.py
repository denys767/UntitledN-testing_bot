import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from db import init_db

from handlers.registration import router as reg_router
from handlers.quiz import router as quiz_router
from handlers.admin import router as admin_router
from handlers.teacher import router as teacher_router
from handlers.menu import router as menu_router

async def main():
    init_db()

    bot = Bot(TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(reg_router)
    dp.include_router(quiz_router)
    dp.include_router(admin_router)
    dp.include_router(teacher_router)
    dp.include_router(menu_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
