from aiogram import Router, types, F
from aiogram.filters import Command
import json
import random
import db

router = Router()

with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

# Store current questions for each user
current_questions = {}


async def start_quiz(user_id, message_or_callback):
    """Функція для запуску квізу, яку можна викликати з різних місць"""
    user = await db.get_user(user_id)
    if not user:
        if hasattr(message_or_callback, 'answer'):
            await message_or_callback.answer("You are not registered. Use /start.")
        return False

    if user[8] == 1:  # banned (index 8)
        if hasattr(message_or_callback, 'answer'):
            await message_or_callback.answer("You are banned.")
        return False

    q = random.choice(QUESTIONS)
    
    # Create inline keyboard with buttons A, B, C, D
    inline_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="A", callback_data=f"answer_{user_id}_A"),
            types.InlineKeyboardButton(text="B", callback_data=f"answer_{user_id}_B")
        ],
        [
            types.InlineKeyboardButton(text="C", callback_data=f"answer_{user_id}_C"),
            types.InlineKeyboardButton(text="D", callback_data=f"answer_{user_id}_D")
        ]
    ])
    
    if hasattr(message_or_callback, 'edit_text'):
        # Якщо це callback, редагуємо повідомлення
        await message_or_callback.edit_text(
            f"{q['question']}\n\nA: {q['A']}\nB: {q['B']}\nC: {q['C']}\nD: {q['D']}",
            reply_markup=inline_kb
        )
    else:
        # Якщо це message, відправляємо нове повідомлення
        await message_or_callback.answer(
            f"{q['question']}\n\nA: {q['A']}\nB: {q['B']}\nC: {q['C']}\nD: {q['D']}",
            reply_markup=inline_kb
        )

    # Store correct answer
    current_questions[user_id] = q
    return True


@router.message(Command("quiz"))
async def quiz(msg: types.Message):
    await start_quiz(msg.from_user.id, msg)


@router.message(Command("rating"))
async def rating(msg: types.Message):
    r = await db.get_rating()
    text = "🏆 *Rating*\n\n"
    for i, row in enumerate(r, 1):
        text += f"{i}. {row[0]} {row[1]} — {row[2]} coins\n"
    await msg.answer(text)


@router.callback_query(F.data.startswith("answer_"))
async def answer_callback(callback: types.CallbackQuery):
    # Parse callback data: answer_userid_answer
    parts = callback.data.split("_")
    user_id = int(parts[1])
    selected_answer = parts[2]
    
    # Check if this callback is for the current user
    if callback.from_user.id != user_id:
        await callback.answer("Це не ваше питання!", show_alert=True)
        return
    
    user = await db.get_user(user_id)
    if not user:
        await callback.answer("Користувач не знайдений!", show_alert=True)
        return
    
    # Get stored question
    if user_id not in current_questions or current_questions[user_id] is None:
        await callback.answer("Питання не знайдено. Використайте /quiz для початку.", show_alert=True)
        return
    
    q = current_questions[user_id]
    correct = q["answer"]
    coins = user[5]
    streak = user[7]  # streak is at index 7

    if selected_answer == correct:
        streak += 1
        bonus = (streak // 5) * 5
        coins += (30 + bonus)
        result = f"✅ Правильно! +{30 + bonus} монет!"
    else:
        streak = 0
        if coins >= 20:
            coins -= 20
        result = f"❌ Неправильно! Правильна відповідь: {correct}. -20 монет (не може бути менше 0)."

    await db.update_coins_and_streak(user_id, coins, streak)

    # Edit message to show result
    await callback.message.edit_text(
        f"{callback.message.text}\n\n{result}\nВаші монети: {coins}"
    )
    
    await callback.answer()

    # Clear stored question
    current_questions[user_id] = None
