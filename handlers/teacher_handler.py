from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import db
from admin_manager import is_admin

router = Router()


class TeacherStates(StatesGroup):
    waiting_test_name = State()
    waiting_test_description = State()
    waiting_test_max_score = State()
    waiting_question_text = State()
    waiting_question_score = State()
    waiting_answer_a = State()
    waiting_answer_b = State()
    waiting_answer_c = State()
    waiting_answer_d = State()
    waiting_correct_answer = State()


async def is_teacher(user_id: int) -> bool:
    # Администраторы могут использовать функции учителя
    if is_admin(user_id):
        return True
    user = await db.get_user(user_id)
    if not user:
        return False
    # Обработка обеих структур БД
    if len(user) >= 9:  # Старая структура: индекс роли = 6
        return user[6] == "teacher"
    else:  # Новая структура: индекс роли = 5
        return user[5] == "teacher"


@router.message(Command("teacher"))
async def teacher_menu(msg: types.Message):
    if not await is_teacher(msg.from_user.id):
        await msg.answer("❌ У вас нет доступа. Вы не учитель.")
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📝 Мои тесты", callback_data="teacher_tests")],
        [types.InlineKeyboardButton(text="➕ Создать тест", callback_data="teacher_new_test")],
        [types.InlineKeyboardButton(text="📊 Результаты", callback_data="teacher_results")]
    ])
    
    await msg.answer("👨‍🏫 Меню учителя:", reply_markup=kb)


@router.callback_query(F.data == "teacher_tests")
async def show_teacher_tests(callback: types.CallbackQuery):
    if not await is_teacher(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    tests = await db.get_tests_by_teacher(callback.from_user.id)
    
    if not tests:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="➕ Создать тест", callback_data="teacher_new_test")],
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back" if is_admin(callback.from_user.id) else "student_menu")]
        ])
        await callback.message.edit_text("📝 У вас нет тестов.", reply_markup=kb)
    else:
        text = "📝 *Ваши тесты:*\n\n"
        for test in tests:
            test_id, discipline_id, teacher_id, name, description, max_score, created_at = test
            text += f"• **{name}** (макс {max_score} баллов)\n"
            text += f"  Описание: {description or 'нет'}\n\n"
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="➕ Создать еще", callback_data="teacher_new_test")],
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back" if is_admin(callback.from_user.id) else "student_menu")]
        ])
        
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    
    await callback.answer()


@router.callback_query(F.data == "teacher_new_test")
async def new_test(callback: types.CallbackQuery, state: FSMContext):
    if not await is_teacher(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    disciplines = await db.get_all_disciplines()
    
    if not disciplines:
        await callback.answer("❌ Сначала администратор должен создать дисциплины!", show_alert=True)
        return
    
    # Показываем выбор дисциплины
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=disc[1], callback_data=f"teacher_select_disc_{disc[0]}")]
        for disc in disciplines
    ])
    
    await callback.message.edit_text("Выберите дисциплину для теста:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("teacher_select_disc_"))
async def select_discipline(callback: types.CallbackQuery, state: FSMContext):
    discipline_id = int(callback.data.split("_")[-1])
    
    # Проверяем, что дисциплина существует
    disc = await db.get_discipline(discipline_id)
    if not disc:
        await callback.answer("❌ Дисциплина не найдена!", show_alert=True)
        return
    
    await state.update_data(discipline_id=discipline_id, teacher_id=callback.from_user.id)
    await callback.message.edit_text("Введите название теста:")
    await callback.answer()
    await state.set_state(TeacherStates.waiting_test_name)


@router.message(TeacherStates.waiting_test_name)
async def process_test_name(msg: types.Message, state: FSMContext):
    test_name = msg.text.strip()
    
    if not test_name:
        await msg.answer("❌ Название не может быть пустым.")
        return
    
    await state.update_data(test_name=test_name)
    await msg.answer("Введите описание теста (или пропустите):")
    await state.set_state(TeacherStates.waiting_test_description)


@router.message(TeacherStates.waiting_test_description)
async def process_test_description(msg: types.Message, state: FSMContext):
    description = msg.text.strip() if msg.text.lower() != "пропустить" else ""
    
    await state.update_data(test_description=description)
    await msg.answer("Введите максимальный балл за тест (по умолчанию 100):")
    await state.set_state(TeacherStates.waiting_test_max_score)


@router.message(TeacherStates.waiting_test_max_score)
async def process_test_max_score(msg: types.Message, state: FSMContext):
    try:
        max_score = int(msg.text.strip()) if msg.text.strip() else 100
    except ValueError:
        await msg.answer("❌ Введите число.")
        return
    
    data = await state.get_data()
    
    # Создаем тест
    test_id = await db.add_test(
        data["discipline_id"],
        data["teacher_id"],
        data["test_name"],
        data["test_description"],
        max_score
    )
    
    await state.update_data(test_id=test_id, questions_count=0)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Добавить вопрос", callback_data="teacher_add_question")],
        [types.InlineKeyboardButton(text="✅ Завершить", callback_data="teacher_finish_test")]
    ])
    
    await msg.answer(f"✅ Тест '{data['test_name']}' создан!\n\nДобавьте вопросы:", reply_markup=kb)
    await state.clear()
    await state.update_data(test_id=test_id, discipline_id=data["discipline_id"], teacher_id=data["teacher_id"], test_name=data["test_name"], questions_count=0)


@router.callback_query(F.data == "teacher_add_question")
async def add_question(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите текст вопроса:")
    await callback.answer()
    await state.set_state(TeacherStates.waiting_question_text)


@router.message(TeacherStates.waiting_question_text)
async def process_question_text(msg: types.Message, state: FSMContext):
    question_text = msg.text.strip()
    
    if not question_text:
        await msg.answer("❌ Вопрос не может быть пустым.")
        return
    
    await state.update_data(question_text=question_text)
    await msg.answer("Введите количество баллов за правильный ответ на этот вопрос:")
    await state.set_state(TeacherStates.waiting_question_score)


@router.message(TeacherStates.waiting_question_score)
async def process_question_score(msg: types.Message, state: FSMContext):
    try:
        score = int(msg.text.strip())
    except ValueError:
        await msg.answer("❌ Введите число.")
        return
    
    await state.update_data(question_score=score)
    await msg.answer("Введите вариант ответа A:")
    await state.set_state(TeacherStates.waiting_answer_a)


@router.message(TeacherStates.waiting_answer_a)
async def process_answer_a(msg: types.Message, state: FSMContext):
    await state.update_data(answer_a=msg.text.strip())
    await msg.answer("Введите вариант ответа B:")
    await state.set_state(TeacherStates.waiting_answer_b)


@router.message(TeacherStates.waiting_answer_b)
async def process_answer_b(msg: types.Message, state: FSMContext):
    await state.update_data(answer_b=msg.text.strip())
    await msg.answer("Введите вариант ответа C:")
    await state.set_state(TeacherStates.waiting_answer_c)


@router.message(TeacherStates.waiting_answer_c)
async def process_answer_c(msg: types.Message, state: FSMContext):
    await state.update_data(answer_c=msg.text.strip())
    await msg.answer("Введите вариант ответа D:")
    await state.set_state(TeacherStates.waiting_answer_d)


@router.message(TeacherStates.waiting_answer_d)
async def process_answer_d(msg: types.Message, state: FSMContext):
    await state.update_data(answer_d=msg.text.strip())
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="A", callback_data="correct_A")],
        [types.InlineKeyboardButton(text="B", callback_data="correct_B")],
        [types.InlineKeyboardButton(text="C", callback_data="correct_C")],
        [types.InlineKeyboardButton(text="D", callback_data="correct_D")]
    ])
    
    await msg.answer("Выберите правильный ответ:", reply_markup=kb)


@router.callback_query(F.data.startswith("correct_"))
async def process_correct_answer(callback: types.CallbackQuery, state: FSMContext):
    correct_answer = callback.data.split("_")[1]
    
    data = await state.get_data()
    
    # Создаем вопрос
    question_id = await db.add_question(
        data["test_id"],
        data["question_text"],
        data["question_score"],
        correct_answer
    )
    
    # Добавляем варианты ответов
    await db.add_answer(question_id, data["answer_a"], "A")
    await db.add_answer(question_id, data["answer_b"], "B")
    await db.add_answer(question_id, data["answer_c"], "C")
    await db.add_answer(question_id, data["answer_d"], "D")
    
    questions_count = data.get("questions_count", 0) + 1
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Добавить еще вопрос", callback_data="teacher_add_question")],
        [types.InlineKeyboardButton(text="✅ Завершить тест", callback_data="teacher_finish_test")]
    ])
    
    await callback.message.edit_text(f"✅ Вопрос {questions_count} добавлен!\n\nЧто дальше?", reply_markup=kb)
    await callback.answer()
    
    await state.update_data(questions_count=questions_count)


@router.callback_query(F.data == "teacher_finish_test")
async def finish_test(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    test_name = data.get("test_name", "Тест")
    questions_count = data.get("questions_count", 0)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back" if is_admin(callback.from_user.id) else "student_menu")]
    ])
    
    await callback.message.edit_text(f"✅ Тест '{test_name}' завершен!\n\nВсего вопросов: {questions_count}", reply_markup=kb)
    await callback.answer()
    await state.clear()


@router.callback_query(F.data == "teacher_results")
async def show_results(callback: types.CallbackQuery):
    if not await is_teacher(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    tests = await db.get_tests_by_teacher(callback.from_user.id)
    
    if not tests:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back" if is_admin(callback.from_user.id) else "student_menu")]
        ])
        await callback.message.edit_text("📊 Результаты пока нет.", reply_markup=kb)
        await callback.answer()
        return
    
    # TODO: Реализовать отображение результатов
    text = "📊 *Результаты студентов:*\n\n"
    for test in tests:
        test_id = test[0]
        test_name = test[3]
        rating = await db.get_test_rating(test_id)
        
        if rating:
            text += f"📋 **{test_name}**\n"
            for i, (student_id, first_name, last_name, score) in enumerate(rating[:5], 1):
                text += f"  {i}. {first_name} {last_name} - {score} баллов\n"
            text += "\n"
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back" if is_admin(callback.from_user.id) else "student_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()
