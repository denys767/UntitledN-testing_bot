from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import db
from admin_manager import is_admin, add_admin

router = Router()


class AdminStates(StatesGroup):
    waiting_discipline_name = State()
    waiting_discipline_description = State()
    waiting_teacher_username = State()
    waiting_new_admin_id = State()


@router.message(Command("admin"))
async def admin_menu(msg: types.Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("❌ У вас нет доступа к этой команде.")
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📚 Дисциплины", callback_data="admin_disciplines")],
        [types.InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [types.InlineKeyboardButton(text="➕ Добавить учителя", callback_data="admin_add_teacher")],
        [types.InlineKeyboardButton(text="👨‍💼 Добавить админа", callback_data="admin_add_admin")],
        [types.InlineKeyboardButton(text="👨‍🏫 Меню учителя", callback_data="admin_teacher_menu")]
    ])
    
    await msg.answer("👨‍💼 Администраторское меню:", reply_markup=kb)


@router.callback_query(F.data == "admin_disciplines")
async def show_disciplines(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    disciplines = await db.get_all_disciplines()
    
    if not disciplines:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="➕ Создать дисциплину", callback_data="admin_new_discipline")],
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ])
        await callback.message.edit_text("📚 Нет дисциплин.\n\nСоздайте первую:", reply_markup=kb)
    else:
        text = "📚 *Все дисциплины:*\n\n"
        for i, disc in enumerate(disciplines, 1):
            text += f"{i}. **{disc[1]}** ({disc[2] or 'без описания'})\n"
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="➕ Создать дисциплину", callback_data="admin_new_discipline")],
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ])
        
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    
    await callback.answer()


@router.callback_query(F.data == "admin_new_discipline")
async def new_discipline(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_disciplines")]
    ])
    
    await callback.message.edit_text("Введите название дисциплины:", reply_markup=kb)
    await callback.answer()
    await state.set_state(AdminStates.waiting_discipline_name)


@router.message(AdminStates.waiting_discipline_name)
async def process_discipline_name(msg: types.Message, state: FSMContext):
    name = msg.text.strip()
    
    if not name:
        await msg.answer("❌ Название не может быть пустым.")
        return
    
    await state.update_data(discipline_name=name)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_disciplines")]
    ])
    await msg.answer("Введите описание дисциплины (или напишите 'пропустить'):", reply_markup=kb)
    await state.set_state(AdminStates.waiting_discipline_description)


@router.message(AdminStates.waiting_discipline_description)
async def process_discipline_description(msg: types.Message, state: FSMContext):
    description = msg.text.strip() if msg.text.lower() != "пропустить" else ""
    
    data = await state.get_data()
    name = data["discipline_name"]
    
    discipline_id = await db.add_discipline(name, description)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_disciplines")]
    ])
    
    if discipline_id:
        await msg.answer(f"✅ Дисциплина '{name}' создана!", reply_markup=kb)
    else:
        await msg.answer(f"❌ Дисциплина '{name}' уже существует.", reply_markup=kb)
    
    await state.clear()


@router.callback_query(F.data == "admin_users")
async def show_users(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    users = await db.get_all_users()
    
    if not users:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ])
        await callback.message.edit_text("👥 Нет зарегистрированных пользователей.", reply_markup=kb)
    else:
        text = "👥 *Все пользователи:*\n\n"
        for user in users:
            user_id, first_name, last_name, grad_year, specialty, role, banned = user
            status = "🚫 ЗАБЛОКИРОВАН" if banned else "✅"
            text += f"{status} {first_name} {last_name} ({role}) - {user_id}\n"
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ])
        
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    
    await callback.answer()


@router.callback_query(F.data == "admin_add_teacher")
async def add_teacher_menu(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text("Отправьте Telegram ID пользователя, которого хотите назначить учителем:", reply_markup=kb)
    await callback.answer()
    await state.set_state(AdminStates.waiting_teacher_username)


@router.message(AdminStates.waiting_teacher_username)
async def process_teacher_username(msg: types.Message, state: FSMContext):
    try:
        user_id = int(msg.text.strip())
    except ValueError:
        await msg.answer("❌ Введите корректный Telegram ID (число).")
        return
    
    # Проверяем, существует ли пользователь
    user = await db.get_user(user_id)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    if not user:
        # Создаем нового пользователя с ролью учителя
        await db.add_user(user_id, "Unknown", "Unknown", 0, "Unknown", role="teacher")
        await msg.answer(f"✅ Пользователь {user_id} добавлен как учитель!", reply_markup=kb)
    else:
        # Обновляем роль существующего пользователя
        await db.update_role(user_id, "teacher")
        await msg.answer(f"✅ Пользователь {user_id} теперь учитель!", reply_markup=kb)
    
    await state.clear()


@router.callback_query(F.data == "admin_add_admin")
async def add_admin_menu(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text("Отправьте Telegram ID пользователя, которого хотите назначить администратором:", reply_markup=kb)
    await callback.answer()
    await state.set_state(AdminStates.waiting_new_admin_id)


@router.message(AdminStates.waiting_new_admin_id)
async def process_new_admin(msg: types.Message, state: FSMContext):
    try:
        user_id = int(msg.text.strip())
    except ValueError:
        await msg.answer("❌ Введите корректный Telegram ID (число).")
        return
    
    # Проверяем, существует ли пользователь
    user = await db.get_user(user_id)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    if not user:
        # Создаем нового пользователя с ролью админа
        await db.add_user(user_id, "Unknown", "Unknown", 0, "Unknown", role="admin")
        await add_admin(user_id)
        await msg.answer(f"✅ Пользователь {user_id} добавлен как администратор!", reply_markup=kb)
    else:
        # Обновляем роль существующего пользователя
        await db.update_role(user_id, "admin")
        await add_admin(user_id)
        await msg.answer(f"✅ Пользователь {user_id} теперь администратор!", reply_markup=kb)
    
    await state.clear()


@router.callback_query(F.data == "admin_teacher_menu")
async def admin_teacher_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📝 Мои тесты", callback_data="teacher_tests")],
        [types.InlineKeyboardButton(text="➕ Создать тест", callback_data="teacher_new_test")],
        [types.InlineKeyboardButton(text="📊 Результаты", callback_data="teacher_results")],
        [types.InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text("👨‍🏫 Меню учителя (как администратор):", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def admin_back_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📚 Дисциплины", callback_data="admin_disciplines")],
        [types.InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [types.InlineKeyboardButton(text="➕ Добавить учителя", callback_data="admin_add_teacher")],
        [types.InlineKeyboardButton(text="👨‍💼 Добавить админа", callback_data="admin_add_admin")],
        [types.InlineKeyboardButton(text="👨‍🏫 Меню учителя", callback_data="admin_teacher_menu")]
    ])
    
    await callback.message.edit_text("👨‍💼 Администраторское меню:", reply_markup=kb)
    await callback.answer()
