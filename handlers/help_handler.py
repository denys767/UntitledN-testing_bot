from aiogram import Router, types
from aiogram.filters import Command
import db

router = Router()


@router.message(Command("help"))
async def help_command(msg: types.Message):
    """Справка по командам"""
    user = await db.get_user(msg.from_user.id)
    
    if not user:
        text = """
*Справка по командам*

/start - Начать регистрацию
/help - Эта справка

Сначала пройдите регистрацию командой /start
"""
    else:
        # Обработка обеих структур БД
        if len(user) >= 9:  # Старая структура
            role = user[6]
        else:  # Новая структура
            role = user[5]
        
        if role == "admin":
            text = """
*Справка для администратора*

/admin - Администраторское меню
/student - Пройти тест (если нужно)

*Основные функции:*
📚 Дисциплины - создание и управление дисциплинами
👥 Пользователи - просмотр всех пользователей
➕ Добавить учителя - назначить учителя по ID
👨‍💼 Добавить админа - назначить администратора по ID
"""
        elif role == "teacher":
            text = """
*Справка для учителя*

/teacher - Меню учителя
/student - Пройти тест (если нужно)

*Основные функции:*
📝 Мои тесты - просмотр созданных тестов
➕ Создать тест - создание нового теста
📊 Результаты - просмотр результатов студентов
"""
        else:  # student
            text = """
*Справка для студента*

/student - Пройти тест

*Основные функции:*
📚 Выбор дисциплины - выберите предмет
📝 Выбор теста - выберите тест по предмету
✏️ Прохождение теста - ответьте на все вопросы
📊 Мои результаты - просмотр своих оценок
🏆 Рейтинги - просмотр рейтингов студентов
"""
    
    await msg.answer(text, parse_mode="Markdown")


@router.message(Command("commands"))
async def commands_list(msg: types.Message):
    """Полный список команд"""
    user = await db.get_user(msg.from_user.id)
    
    text = """
*Все доступные команды*

*Основные:*
/start - Начать регистрацию
/help - Справка по командам
/commands - Полный список команд

*Для администраторов:*
/admin - Администраторское меню

*Для учителей:*
/teacher - Меню учителя

*Для студентов:*
/student - Пройти тест

*Прочие:*
"""
    
    if not user:
        text += "/start - Зарегистрироваться"
    else:
        text += "(нет дополнительных команд)"
    
    await msg.answer(text, parse_mode="Markdown")
