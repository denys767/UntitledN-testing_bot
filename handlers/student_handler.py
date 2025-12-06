from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import db

router = Router()


class StudentStates(StatesGroup):
    choosing_discipline = State()
    choosing_test = State()
    taking_test = State()


async def is_student(user_id: int) -> bool:
    user = await db.get_user(user_id)
    if not user:
        return False
    # Обработка обеих структур БД
    if len(user) >= 9:  # Старая структура: индекс роли = 6
        return user[6] in ("student", "teacher", "admin")
    else:  # Новая структура: индекс роли = 5
        return user[5] in ("student", "teacher", "admin")


@router.message(Command("student"))
async def student_menu(msg: types.Message, state: FSMContext):
    if not await is_student(msg.from_user.id):
        await msg.answer("❌ Вы не зарегистрированы.")
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📚 Начать тест", callback_data="student_disciplines")],
        [types.InlineKeyboardButton(text="📊 Мои результаты", callback_data="student_results")],
        [types.InlineKeyboardButton(text="🏆 Рейтинги", callback_data="student_ratings")]
    ])
    
    await msg.answer("👨‍🎓 Меню студента:", reply_markup=kb)
    await state.clear()


@router.callback_query(F.data == "student_disciplines")
async def show_disciplines(callback: types.CallbackQuery, state: FSMContext):
    if not await is_student(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    disciplines = await db.get_all_disciplines()
    
    if not disciplines:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="student_back")]
        ])
        await callback.message.edit_text("📚 Нет доступных дисциплин.", reply_markup=kb)
        await callback.answer()
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=disc[1], callback_data=f"student_tests_{disc[0]}")]
        for disc in disciplines
    ] + [[types.InlineKeyboardButton(text="🔙 Назад", callback_data="student_back")]])
    
    text = "📚 *Выберите дисциплину:*\n\n"
    for disc in disciplines:
        text += f"• {disc[1]}\n"
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()
    await state.set_state(StudentStates.choosing_discipline)


@router.callback_query(F.data.startswith("student_tests_"))
async def show_tests(callback: types.CallbackQuery, state: FSMContext):
    discipline_id = int(callback.data.split("_")[-1])
    
    tests = await db.get_tests_by_discipline(discipline_id)
    
    if not tests:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 Назад к дисциплинам", callback_data="student_disciplines")]
        ])
        await callback.message.edit_text("📝 Нет тестов в этой дисциплине.", reply_markup=kb)
        await callback.answer()
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=test[3], callback_data=f"student_test_{test[0]}")]
        for test in tests
    ] + [[types.InlineKeyboardButton(text="🔙 Назад к дисциплинам", callback_data="student_disciplines")]])
    
    text = "📝 *Выберите тест:*\n\n"
    for test in tests:
        test_id, discipline_id_val, teacher_id, name, description, max_score, created_at = test
        text += f"• **{name}** (макс {max_score} баллов)\n"
        if description:
            text += f"  {description}\n"
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()
    await state.set_state(StudentStates.choosing_test)


@router.callback_query(F.data.startswith("student_test_"))
async def start_test(callback: types.CallbackQuery, state: FSMContext):
    test_id = int(callback.data.split("_")[-1])
    
    test = await db.get_test(test_id)
    if not test:
        await callback.answer("❌ Тест не найден!", show_alert=True)
        return
    
    # Проверяем, начал ли студент уже этот тест
    already_started = await db.student_started_test(callback.from_user.id, test_id)
    
    questions = await db.get_questions_by_test(test_id)
    
    if not questions:
        await callback.message.edit_text("❌ В этом тесте нет вопросов.")
        await callback.answer()
        return
    
    await state.update_data(
        test_id=test_id,
        test_name=test[3],
        questions=questions,
        current_question_index=0,
        student_id=callback.from_user.id,
        already_started=already_started
    )
    
    await show_question(callback, state)


async def show_question(callback_or_msg, state: FSMContext):
    data = await state.get_data()
    test_id = data["test_id"]
    student_id = data["student_id"]
    current_index = data["current_question_index"]
    questions = data["questions"]
    
    if current_index >= len(questions):
        # Тест завершен
        total_score = await db.get_test_score(student_id, test_id)
        max_score = await db.get_test_max_score(test_id)
        
        text = f"✅ *Тест завершен!*\n\n"
        text += f"Ваш результат: **{total_score}/{max_score}** баллов\n"
        text += f"Процент: **{int(total_score/max_score*100) if max_score > 0 else 0}%**\n"
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔄 Вернуться к тестам", callback_data="student_disciplines")],
            [types.InlineKeyboardButton(text="📊 Мои результаты", callback_data="student_results")]
        ])
        
        if isinstance(callback_or_msg, types.CallbackQuery):
            await callback_or_msg.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        else:
            await callback_or_msg.answer(text, reply_markup=kb, parse_mode="Markdown")
        
        await state.clear()
        return
    
    question = questions[current_index]
    question_id, test_id_val, question_text, score_value, correct_answer, created_at = question
    
    # Получаем варианты ответов
    answers = await db.get_answers_by_question(question_id)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=answer[2], callback_data=f"answer_{question_id}_{answer[3]}")]
        for answer in answers
    ])
    
    text = f"*Вопрос {current_index + 1}/{len(questions)}*\n\n"
    text += f"{question_text}\n\n"
    text += f"Баллы: {score_value}"
    
    if isinstance(callback_or_msg, types.CallbackQuery):
        await callback_or_msg.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        await callback_or_msg.answer()
    else:
        await callback_or_msg.answer(text, reply_markup=kb, parse_mode="Markdown")
    
    await state.set_state(StudentStates.taking_test)


@router.callback_query(F.data.startswith("answer_"))
async def process_answer(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    question_id = int(parts[1])
    selected_answer = parts[2]
    
    data = await state.get_data()
    test_id = data["test_id"]
    student_id = data["student_id"]
    questions = data["questions"]
    current_index = data["current_question_index"]
    
    question = questions[current_index]
    question_id_val, test_id_val, question_text, score_value, correct_answer, created_at = question
    
    # Проверяем ответ
    is_correct = selected_answer == correct_answer
    score_earned = score_value if is_correct else 0
    
    # Сохраняем результат
    await db.add_result(student_id, test_id, question_id, selected_answer, score_earned)
    
    # Показываем результат
    if is_correct:
        result_text = f"✅ *Правильно!*\n\n+{score_earned} баллов!"
    else:
        result_text = f"❌ *Неправильно.*\n\n"
        result_text += f"Вы выбрали: {selected_answer}\n"
        result_text += f"Правильный ответ: {correct_answer}\n"
        result_text += f"Баллов получено: 0"
    
    # Переходим к следующему вопросу
    new_index = current_index + 1
    await state.update_data(current_question_index=new_index)
    
    if new_index < len(questions):
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="➡️ Следующий вопрос", callback_data="next_question")]
        ])
        await callback.message.edit_text(result_text + f"\n\n({new_index}/{len(questions)})", reply_markup=kb, parse_mode="Markdown")
    else:
        await callback.message.edit_text(result_text, parse_mode="Markdown")
        await show_question(callback, state)
        return
    
    await callback.answer()


@router.callback_query(F.data == "next_question")
async def next_question(callback: types.CallbackQuery, state: FSMContext):
    await show_question(callback, state)


@router.callback_query(F.data == "student_results")
async def show_results(callback: types.CallbackQuery):
    if not await is_student(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    disciplines = await db.get_all_disciplines()
    
    if not disciplines:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="student_back")]
        ])
        await callback.message.edit_text("📊 Нет дисциплин.", reply_markup=kb)
        await callback.answer()
        return
    
    text = "📊 *Ваши результаты:*\n\n"
    
    for disc in disciplines:
        disc_id = disc[0]
        disc_name = disc[1]
        
        results = await db.get_student_results_by_discipline(callback.from_user.id, disc_id)
        
        if results:
            text += f"📚 {disc_name}\n"
            for test_id, test_name, score, max_score in results:
                if max_score > 0:
                    percentage = int(score / max_score * 100)
                    text += f"  • {test_name}: {score}/{max_score} ({percentage}%)\n"
                else:
                    text += f"  • {test_name}: не пройден\n"
            text += "\n"
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="student_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "student_ratings")
async def show_ratings(callback: types.CallbackQuery):
    if not await is_student(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    tests = []
    disciplines = await db.get_all_disciplines()
    
    if not disciplines:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="student_back")]
        ])
        await callback.message.edit_text("🏆 Нет дисциплин.", reply_markup=kb)
        await callback.answer()
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=disc[1], callback_data=f"rating_disc_{disc[0]}")]
        for disc in disciplines
    ] + [[types.InlineKeyboardButton(text="🔙 Назад", callback_data="student_back")]])
    
    text = "🏆 *Выберите дисциплину для просмотра рейтинга:*"
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("rating_disc_"))
async def show_discipline_rating(callback: types.CallbackQuery):
    discipline_id = int(callback.data.split("_")[-1])
    
    tests = await db.get_tests_by_discipline(discipline_id)
    
    if not tests:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 Назад к рейтингам", callback_data="student_ratings")]
        ])
        await callback.message.edit_text("🏆 Нет тестов в этой дисциплине.", reply_markup=kb)
        await callback.answer()
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=test[3], callback_data=f"rating_test_{test[0]}")]
        for test in tests
    ] + [[types.InlineKeyboardButton(text="🔙 Назад к рейтингам", callback_data="student_ratings")]])
    
    text = "🏆 *Выберите тест для просмотра рейтинга:*"
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("rating_test_"))
async def show_test_rating(callback: types.CallbackQuery):
    test_id = int(callback.data.split("_")[-1])
    
    rating = await db.get_test_rating(test_id)
    
    test = await db.get_test(test_id)
    max_score = await db.get_test_max_score(test_id)
    
    if not rating:
        text = "🏆 *Рейтинг*\n\nНет результатов."
    else:
        text = f"🏆 *Рейтинг - {test[3]}*\n\n"
        
        for i, (student_id, first_name, last_name, score) in enumerate(rating, 1):
            percentage = int(score / max_score * 100) if max_score > 0 else 0
            text += f"{i}. {first_name} {last_name} - {score}/{max_score} ({percentage}%)\n"
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Назад к тестам", callback_data="student_ratings")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "student_back")
async def student_back_menu(callback: types.CallbackQuery):
    if not await is_student(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📚 Начать тест", callback_data="student_disciplines")],
        [types.InlineKeyboardButton(text="📊 Мои результаты", callback_data="student_results")],
        [types.InlineKeyboardButton(text="🏆 Рейтинги", callback_data="student_ratings")]
    ])
    
    await callback.message.edit_text("👨‍🎓 Меню студента:", reply_markup=kb)
    await callback.answer()
