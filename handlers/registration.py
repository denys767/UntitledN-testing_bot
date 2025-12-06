from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import db
from admin_manager import is_admin

router = Router()


class RegistrationStates(StatesGroup):
    waiting_name = State()
    waiting_grad_year = State()
    waiting_specialty = State()


async def show_commands(msg: types.Message, role: str):
    """Показать доступные команды в зависимости от роли"""
    if role == "admin":
        text = """
*Доступные команды для администратора:*

/admin - Администраторское меню
/student - Пройти тест (студент)

*Функции:*
• Создание дисциплин
• Управление пользователями
• Назначение учителей
"""
    elif role == "teacher":
        text = """
*Доступные команды для учителя:*

/teacher - Меню учителя
/student - Пройти тест (студент)

*Функции:*
• Создание тестов
• Добавление вопросов
• Просмотр результатов студентов
"""
    else:  # student
        text = """
*Доступные команды для студента:*

/student - Пройти тест
/help - Справка

*Функции:*
• Выбор дисциплины и теста
• Прохождение тестов
• Просмотр результатов
• Просмотр рейтингов
"""
    
    await msg.answer(text, parse_mode="Markdown")


@router.message(Command("start"))
async def start(msg: types.Message, state: FSMContext):
    user = await db.get_user(msg.from_user.id)
    if user:
        # Обработка обеих структур БД
        if len(user) >= 9:  # Старая структура: индекс роли = 6
            role = user[6]
        else:  # Новая структура: индекс роли = 5
            role = user[5]
        await msg.answer(f"👋 Вы уже зарегистрированы как {role}!\n\nДоступные команды:")
        await show_commands(msg, role)
        await state.clear()
        return
    
    # Проверяем, является ли пользователь администратором
    if is_admin(msg.from_user.id):
        await msg.answer("👋 Добро пожаловать, администратор!\n\nПожалуйста, введите ваше имя и фамилию (например, 'Иван Иванов'):")
        await state.update_data(role="admin")
        await state.set_state(RegistrationStates.waiting_name)
    else:
        # Обычные пользователи регистрируются как студенты
        await msg.answer("👋 Добро пожаловать! Давайте зарегистрируемся.\nПожалуйста, введите ваше имя и фамилию (например, 'Иван Иванов'):")
        await state.update_data(role="student")
        await state.set_state(RegistrationStates.waiting_name)


@router.message(RegistrationStates.waiting_name)
async def process_name(msg: types.Message, state: FSMContext):
    name_parts = msg.text.strip().split(maxsplit=1)
    if len(name_parts) < 2:
        await msg.answer("❌ Пожалуйста, введите имя И фамилию (например, 'Иван Иванов'):")
        return
    
    first_name = name_parts[0]
    last_name = name_parts[1]
    await state.update_data(first_name=first_name, last_name=last_name)
    
    # Create inline keyboard for graduation year
    year_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="2025", callback_data=f"reg_year_{msg.from_user.id}_2025"),
            types.InlineKeyboardButton(text="2026", callback_data=f"reg_year_{msg.from_user.id}_2026"),
            types.InlineKeyboardButton(text="2027", callback_data=f"reg_year_{msg.from_user.id}_2027")
        ],
        [
            types.InlineKeyboardButton(text="2028", callback_data=f"reg_year_{msg.from_user.id}_2028"),
            types.InlineKeyboardButton(text="2029", callback_data=f"reg_year_{msg.from_user.id}_2029")
        ]
    ])
    
    await msg.answer("Выберите год окончания:", reply_markup=year_kb)
    await state.set_state(RegistrationStates.waiting_grad_year)


@router.callback_query(F.data.startswith("reg_year_"), RegistrationStates.waiting_grad_year)
async def process_grad_year(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    user_id = int(parts[2])
    year = int(parts[3])
    
    if callback.from_user.id != user_id:
        await callback.answer("❌ Это не ваша регистрация!", show_alert=True)
        return
    
    await state.update_data(grad_year=year)
    
    # Create inline keyboard for specialty
    specialty_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="AM", callback_data=f"reg_spec_{user_id}_AM"),
            types.InlineKeyboardButton(text="CS", callback_data=f"reg_spec_{user_id}_CS"),
            types.InlineKeyboardButton(text="SE", callback_data=f"reg_spec_{user_id}_SE")
        ],
        [
            types.InlineKeyboardButton(text="BE", callback_data=f"reg_spec_{user_id}_BE"),
            types.InlineKeyboardButton(text="PS", callback_data=f"reg_spec_{user_id}_PS"),
            types.InlineKeyboardButton(text="EBD", callback_data=f"reg_spec_{user_id}_EBD")
        ],
        [
            types.InlineKeyboardButton(text="LAW", callback_data=f"reg_spec_{user_id}_LAW")
        ]
    ])
    
    await callback.message.edit_text("Выберите специальность:", reply_markup=specialty_kb)
    await callback.answer()
    await state.set_state(RegistrationStates.waiting_specialty)


@router.callback_query(F.data.startswith("reg_spec_"), RegistrationStates.waiting_specialty)
async def process_specialty(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    user_id = int(parts[2])
    specialty = parts[3]
    
    if callback.from_user.id != user_id:
        await callback.answer("❌ Это не ваша регистрация!", show_alert=True)
        return
    
    data = await state.get_data()
    
    if "first_name" not in data or "last_name" not in data or "grad_year" not in data or "role" not in data:
        await callback.answer("❌ Ошибка регистрации. Начните заново с /start.", show_alert=True)
        return
    
    # Регистрируем пользователя
    await db.add_user(
        user_id,
        data["first_name"],
        data["last_name"],
        data["grad_year"],
        specialty,
        role=data["role"]
    )
    
    await state.clear()
    
    role_text = {
        "student": "👨‍🎓 Студент",
        "teacher": "👨‍🏫 Учитель",
        "admin": "👨‍💼 Администратор"
    }.get(data["role"], "Пользователь")
    
    text = f"✅ Регистрация завершена!\n\nВаша роль: {role_text}\n\n"
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()
    
    # Показываем доступные команды
    await show_commands(callback.message, data["role"])
