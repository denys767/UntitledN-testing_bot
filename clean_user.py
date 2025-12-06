import sqlite3
import sys

DB = "bot.db"

def delete_user(user_id):
    """Удалить пользователя из базы данных"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    cur.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    
    print(f"✅ Пользователь {user_id} удален из базы данных")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python clean_user.py <user_id>")
        print("Пример: python clean_user.py 632877422")
        sys.exit(1)
    
    user_id = int(sys.argv[1])
    delete_user(user_id)
