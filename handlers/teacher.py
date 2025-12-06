from aiogram import Router, types
from aiogram.filters import Command
import json
import db

router = Router()

@router.message(Command("add_question"))
async def add_question(msg: types.Message):
    user = await db.get_user(msg.from_user.id)
    if not user or user[6] == "student":
        await msg.answer("Only teachers can create tests.")
        return

    try:
        parts = msg.text.split("|")
        # Format: /add_question question | A | B | C | D | answer
        q = {
            "question": parts[1],
            "A": parts[2],
            "B": parts[3],
            "C": parts[4],
            "D": parts[5],
            "answer": parts[6]
        }
        with open("questions.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        data.append(q)
        with open("questions.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        await msg.answer("Question added.")
    except:
        await msg.answer("Usage:\n/add_question question|A|B|C|D|answer")
