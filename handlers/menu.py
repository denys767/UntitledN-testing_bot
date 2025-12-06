from aiogram import Router, types, F
from aiogram.filters import Command
import db

router = Router()


def get_menu_keyboard():
    """Створює клавіатуру головного меню"""
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🎯 Почати квіз", callback_data="menu_start_quiz")
        ],
        [
            types.InlineKeyboardButton(text="🏆 Рейтингова таблиця", callback_data="menu_rating")
        ],
        [
            types.InlineKeyboardButton(text="👤 Мій профіль", callback_data="menu_profile")
        ]
    ])


@router.message(Command("menu"))
async def show_menu(msg: types.Message):
    """Показує головне меню"""
    user = await db.get_user(msg.from_user.id)
    if not user:
        await msg.answer("Ви не зареєстровані. Використайте /start для реєстрації.")
        return
    
    if user[8] == 1:  # banned (index 8)
        await msg.answer("Ви заблоковані.")
        return
    
    await msg.answer(
        "📋 *Головне меню*\n\nОберіть дію:",
        reply_markup=get_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "menu_start_quiz")
async def menu_start_quiz(callback: types.CallbackQuery):
    """Обробник кнопки 'Почати квіз'"""
    from handlers.quiz import start_quiz
    success = await start_quiz(callback.from_user.id, callback.message)
    if success:
        await callback.answer()
    else:
        await callback.answer("Помилка запуску квізу!", show_alert=True)


@router.callback_query(F.data == "menu_rating")
async def menu_rating(callback: types.CallbackQuery):
    """Обробник кнопки 'Рейтингова таблиця'"""
    r = await db.get_rating()
    text = "🏆 *Рейтингова таблиця*\n\n"
    
    if not r:
        text += "Поки що немає учасників."
    else:
        for i, row in enumerate(r, 1):
            text += f"{i}. {row[0]} {row[1]} — {row[2]} монет\n"
    
    # Кнопка повернення до меню
    back_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Назад до меню", callback_data="menu_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "menu_profile")
async def menu_profile(callback: types.CallbackQuery):
    """Обробник кнопки 'Мій профіль'"""
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Ви не зареєстровані!", show_alert=True)
        return
    
    # user structure: (user_id, first_name, last_name, grad_year, specialty, coins, role, streak, banned)
    first_name = user[1] or "Невідомо"
    last_name = user[2] or "Невідомо"
    grad_year = user[3] or "Невідомо"
    specialty = user[4] or "Невідомо"
    coins = user[5] or 0
    role = user[6] or "student"
    streak = user[7] or 0  # streak is at index 7
    
    role_emoji = "👨‍🏫" if role == "teacher" else "👤"
    role_text = "Вчитель" if role == "teacher" else "Студент"
    
    profile_text = (
        f"👤 *Мій профіль*\n\n"
        f"📝 Ім'я: {first_name} {last_name}\n"
        f"🎓 Рік випуску: {grad_year}\n"
        f"📚 Спеціальність: {specialty}\n"
        f"{role_emoji} Роль: {role_text}\n"
        f"💰 Монети: {coins}\n"
        f"🔥 Серія: {streak}"
    )
    
    # Кнопка повернення до меню
    back_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Назад до меню", callback_data="menu_back")]
    ])
    
    await callback.message.edit_text(profile_text, reply_markup=back_kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "menu_back")
async def menu_back(callback: types.CallbackQuery):
    """Повернення до головного меню"""
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Ви не зареєстровані!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📋 *Головне меню*\n\nОберіть дію:",
        reply_markup=get_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

