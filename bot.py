import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from db import init_db
import admin_manager  # Загружаем администраторов

from handlers.registration import router as reg_router
from handlers.help_handler import router as help_router
from handlers.admin_handler import router as admin_router
from handlers.teacher_handler import router as teacher_router
from handlers.student_handler import router as student_router
from handlers.quiz import router as quiz_router

async def main():
    init_db()

    bot = Bot(TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Порядок роутеров важен - более специфичные должны быть перед общими
    dp.include_router(reg_router)
    dp.include_router(help_router)
    dp.include_router(admin_router)
    dp.include_router(teacher_router)
    dp.include_router(student_router)
    dp.include_router(quiz_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
