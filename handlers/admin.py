from aiogram import Router, types
from aiogram.filters import Command
import json
import random
import db

router = Router()

with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

@router.message(Command("quiz"))
async def quiz(msg: types.Message):
    user = await db.get_user(msg.from_user.id)
    if not user:
        await msg.answer("You are not registered. Use /start.")
        return

    if user[8] == 1:  # banned (index 8)
        await msg.answer("You are banned.")
        return

    q = random.choice(QUESTIONS)
    kb = [
        [types.KeyboardButton(text="A"), types.KeyboardButton(text="B")],
        [types.KeyboardButton(text="C"), types.KeyboardButton(text="D")],
    ]
    await msg.answer(
        f"{q['question']}\nA: {q['A']}\nB: {q['B']}\nC: {q['C']}\nD: {q['D']}",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )

    # Store correct answer in FSM memory or use a lightweight in-memory store
    msg.bot["current_question"] = {msg.from_user.id: q}

@router.message(lambda m: m.text in ["A", "B", "C", "D"])
async def answer(msg: types.Message):
    user = await db.get_user(msg.from_user.id)
    q = msg.bot["current_question"].get(msg.from_user.id)

    if not q:
        await msg.answer("Use /quiz to start.")
        return

    correct = q["answer"]
    coins = user[5]
    streak = user[7]  # streak is at index 7

    if msg.text == correct:
        streak += 1
        bonus = (streak // 5) * 5
        coins += (30 + bonus)
        result = f"Correct! +{30 + bonus} coins!"
    else:
        streak = 0
        if coins >= 20:
            coins -= 20
        result = "Wrong! -20 coins (cannot go below 0)."

    await db.update_coins_and_streak(msg.from_user.id, coins, streak)

    await msg.answer(f"{result}\nYour coins: {coins}")

    msg.bot["current_question"][msg.from_user.id] = None
