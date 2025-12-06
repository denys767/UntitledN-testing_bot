from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import db

router = Router()


class RegistrationStates(StatesGroup):
    waiting_name = State()
    waiting_grad_year = State()
    waiting_specialty = State()


@router.message(Command("start"))
async def start(msg: types.Message, state: FSMContext):
    user = await db.get_user(msg.from_user.id)
    if user:
        await msg.answer("You are already registered! Use /quiz to start.")
        return
    
    await msg.answer("Welcome! Let's register you.\nPlease enter your first name and last name (e.g., 'Іван Іванов'):")
    await state.set_state(RegistrationStates.waiting_name)


@router.message(RegistrationStates.waiting_name)
async def process_name(msg: types.Message, state: FSMContext):
    name_parts = msg.text.strip().split(maxsplit=1)
    if len(name_parts) < 2:
        await msg.answer("Please enter both first name and last name (e.g., 'Іван Іванов'):")
        return
    
    first_name = name_parts[0]
    last_name = name_parts[1]
    await state.update_data(first_name=first_name, last_name=last_name)
    
    # Create inline keyboard for graduation year
    year_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="2025", callback_data=f"year_{msg.from_user.id}_25"),
            types.InlineKeyboardButton(text="2026", callback_data=f"year_{msg.from_user.id}_26"),
            types.InlineKeyboardButton(text="2027", callback_data=f"year_{msg.from_user.id}_27")
        ],
        [
            types.InlineKeyboardButton(text="2028", callback_data=f"year_{msg.from_user.id}_28"),
            types.InlineKeyboardButton(text="2029", callback_data=f"year_{msg.from_user.id}_29")
        ]
    ])
    
    await msg.answer("Select your graduation year:", reply_markup=year_kb)
    await state.set_state(RegistrationStates.waiting_grad_year)


@router.callback_query(F.data.startswith("year_"), RegistrationStates.waiting_grad_year)
async def process_grad_year(callback: types.CallbackQuery, state: FSMContext):
    # Parse callback data: year_userid_year
    parts = callback.data.split("_")
    user_id = int(parts[1])
    year = int(parts[2])
    
    # Check if this callback is for the current user
    if callback.from_user.id != user_id:
        await callback.answer("Це не ваша реєстрація!", show_alert=True)
        return
    
    await state.update_data(grad_year=year)
    
    # Create inline keyboard for specialty
    specialty_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="AM", callback_data=f"spec_{user_id}_AM"),
            types.InlineKeyboardButton(text="CS", callback_data=f"spec_{user_id}_CS"),
            types.InlineKeyboardButton(text="SE", callback_data=f"spec_{user_id}_SE")
        ],
        [
            types.InlineKeyboardButton(text="BE", callback_data=f"spec_{user_id}_BE"),
            types.InlineKeyboardButton(text="PS", callback_data=f"spec_{user_id}_PS"),
            types.InlineKeyboardButton(text="EBD", callback_data=f"spec_{user_id}_EBD")
        ],
        [
            types.InlineKeyboardButton(text="LAW", callback_data=f"spec_{user_id}_LAW")
        ]
    ])
    
    await callback.message.edit_text("Select your specialty:", reply_markup=specialty_kb)
    await callback.answer()
    await state.set_state(RegistrationStates.waiting_specialty)


@router.callback_query(F.data.startswith("spec_"), RegistrationStates.waiting_specialty)
async def process_specialty(callback: types.CallbackQuery, state: FSMContext):
    # Parse callback data: spec_userid_specialty
    parts = callback.data.split("_")
    user_id = int(parts[1])
    specialty = parts[2]
    
    # Check if this callback is for the current user
    if callback.from_user.id != user_id:
        await callback.answer("Це не ваша реєстрація!", show_alert=True)
        return
    
    data = await state.get_data()
    
    # Validate that all required data is present
    if "first_name" not in data or "last_name" not in data or "grad_year" not in data:
        await callback.answer("Помилка реєстрації. Почніть спочатку з /start.", show_alert=True)
        return
    await db.add_user(
        user_id,
        data["first_name"],
        data["last_name"],
        data["grad_year"],
        specialty
    )
    await state.clear()
    
    await callback.message.edit_text("✅ Registration complete! Use /quiz to start answering questions.")
    await callback.answer()
