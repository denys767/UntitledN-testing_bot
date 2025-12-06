import sqlite3
import asyncio

DB = "bot.db"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Таблица пользователей
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            grad_year INTEGER,
            specialty TEXT,
            role TEXT DEFAULT 'student',
            banned INTEGER DEFAULT 0
        )
    """)
    
    # Таблица дисциплин (создают админы)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS disciplines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица тестов (создают учителя)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discipline_id INTEGER NOT NULL,
            teacher_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            max_score INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (discipline_id) REFERENCES disciplines(id),
            FOREIGN KEY (teacher_id) REFERENCES users(user_id)
        )
    """)
    
    # Таблица вопросов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            score_value INTEGER NOT NULL,
            correct_answer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES tests(id)
        )
    """)
    
    # Таблица вариантов ответов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            answer_text TEXT NOT NULL,
            answer_key TEXT NOT NULL,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    """)
    
    # Таблица результатов студентов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            test_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            selected_answer TEXT,
            score_earned INTEGER DEFAULT 0,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(user_id),
            FOREIGN KEY (test_id) REFERENCES tests(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    """)
    
    # Таблица для связи учителей с дисциплинами (опционально)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teacher_disciplines (
            teacher_id INTEGER NOT NULL,
            discipline_id INTEGER NOT NULL,
            PRIMARY KEY (teacher_id, discipline_id),
            FOREIGN KEY (teacher_id) REFERENCES users(user_id),
            FOREIGN KEY (discipline_id) REFERENCES disciplines(id)
        )
    """)
    
    conn.commit()
    conn.close()

# ===== USERS =====

async def add_user(user_id, first, last, year, spec, role="student"):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users(user_id, first_name, last_name, grad_year, specialty, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, first, last, year, spec, role))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

async def get_user(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    r = cur.fetchone()
    conn.close()
    return r

async def user_exists(user_id):
    user = await get_user(user_id)
    return user is not None

async def update_role(user_id, role):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET role=? WHERE user_id=?", (role, user_id))
    conn.commit()
    conn.close()

async def ban_user(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET banned=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

async def unban_user(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE users SET banned=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

async def get_all_users():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    r = cur.fetchall()
    conn.close()
    return r

async def get_users_by_role(role):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE role=?", (role,))
    r = cur.fetchall()
    conn.close()
    return r

# ===== DISCIPLINES =====

async def add_discipline(name, description=""):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO disciplines(name, description)
            VALUES (?, ?)
        """, (name, description))
        conn.commit()
        discipline_id = cur.lastrowid
        conn.close()
        return discipline_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

async def get_discipline(discipline_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM disciplines WHERE id=?", (discipline_id,))
    r = cur.fetchone()
    conn.close()
    return r

async def get_all_disciplines():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM disciplines ORDER BY name")
    r = cur.fetchall()
    conn.close()
    return r

async def delete_discipline(discipline_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM disciplines WHERE id=?", (discipline_id,))
    conn.commit()
    conn.close()

# ===== TESTS =====

async def add_test(discipline_id, teacher_id, name, description="", max_score=100):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tests(discipline_id, teacher_id, name, description, max_score)
        VALUES (?, ?, ?, ?, ?)
    """, (discipline_id, teacher_id, name, description, max_score))
    conn.commit()
    test_id = cur.lastrowid
    conn.close()
    return test_id

async def get_test(test_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tests WHERE id=?", (test_id,))
    r = cur.fetchone()
    conn.close()
    return r

async def get_tests_by_discipline(discipline_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tests WHERE discipline_id=? ORDER BY name", (discipline_id,))
    r = cur.fetchall()
    conn.close()
    return r

async def get_tests_by_teacher(teacher_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tests WHERE teacher_id=? ORDER BY name", (teacher_id,))
    r = cur.fetchall()
    conn.close()
    return r

async def delete_test(test_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM tests WHERE id=?", (test_id,))
    conn.commit()
    conn.close()

# ===== QUESTIONS =====

async def add_question(test_id, question_text, score_value, correct_answer):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO questions(test_id, question_text, score_value, correct_answer)
        VALUES (?, ?, ?, ?)
    """, (test_id, question_text, score_value, correct_answer))
    conn.commit()
    question_id = cur.lastrowid
    conn.close()
    return question_id

async def get_question(question_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions WHERE id=?", (question_id,))
    r = cur.fetchone()
    conn.close()
    return r

async def get_questions_by_test(test_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions WHERE test_id=? ORDER BY id", (test_id,))
    r = cur.fetchall()
    conn.close()
    return r

async def delete_question(question_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM questions WHERE id=?", (question_id,))
    conn.commit()
    conn.close()

# ===== ANSWERS =====

async def add_answer(question_id, answer_text, answer_key):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO answers(question_id, answer_text, answer_key)
        VALUES (?, ?, ?)
    """, (question_id, answer_text, answer_key))
    conn.commit()
    answer_id = cur.lastrowid
    conn.close()
    return answer_id

async def get_answers_by_question(question_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM answers WHERE question_id=? ORDER BY answer_key", (question_id,))
    r = cur.fetchall()
    conn.close()
    return r

async def delete_answer(answer_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM answers WHERE id=?", (answer_id,))
    conn.commit()
    conn.close()

# ===== RESULTS =====

async def add_result(student_id, test_id, question_id, selected_answer, score_earned):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO student_results(student_id, test_id, question_id, selected_answer, score_earned)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, test_id, question_id, selected_answer, score_earned))
    conn.commit()
    conn.close()

async def get_student_test_results(student_id, test_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM student_results 
        WHERE student_id=? AND test_id=?
        ORDER BY completed_at
    """, (student_id, test_id))
    r = cur.fetchall()
    conn.close()
    return r

async def get_test_score(student_id, test_id):
    """Получить общую оценку студента по тесту"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(score_earned), 0) FROM student_results
        WHERE student_id=? AND test_id=?
    """, (student_id, test_id))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else 0

async def get_test_max_score(test_id):
    """Получить максимальную оценку за тест"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(score_value), 0) FROM questions WHERE test_id=?", (test_id,))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else 0

async def get_test_rating(test_id):
    """Получить рейтинг студентов по тесту"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT u.user_id, u.first_name, u.last_name, COALESCE(SUM(sr.score_earned), 0) as total_score
        FROM users u
        LEFT JOIN student_results sr ON u.user_id = sr.student_id AND sr.test_id = ?
        WHERE u.role = 'student' AND sr.student_id IS NOT NULL
        GROUP BY u.user_id
        ORDER BY total_score DESC
    """, (test_id,))
    r = cur.fetchall()
    conn.close()
    return r

async def get_student_results_by_discipline(student_id, discipline_id):
    """Получить все результаты студента по дисциплине"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT t.id, t.name, COALESCE(SUM(sr.score_earned), 0) as score, 
               (SELECT COALESCE(SUM(q.score_value), 0) FROM questions q WHERE q.test_id = t.id) as max_score
        FROM tests t
        LEFT JOIN student_results sr ON t.id = sr.test_id AND sr.student_id = ?
        WHERE t.discipline_id = ?
        GROUP BY t.id
    """, (student_id, discipline_id))
    r = cur.fetchall()
    conn.close()
    return r

async def student_started_test(student_id, test_id):
    """Проверить, начал ли студент тест"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM student_results 
        WHERE student_id=? AND test_id=?
    """, (student_id, test_id))
    r = cur.fetchone()
    conn.close()
    return r[0] > 0

# ===== TEACHER DISCIPLINES =====

async def add_teacher_to_discipline(teacher_id, discipline_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO teacher_disciplines(teacher_id, discipline_id)
            VALUES (?, ?)
        """, (teacher_id, discipline_id))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

async def get_teacher_disciplines(teacher_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT d.* FROM disciplines d
        JOIN teacher_disciplines td ON d.id = td.discipline_id
        WHERE td.teacher_id = ?
    """, (teacher_id,))
    r = cur.fetchall()
    conn.close()
    return r
