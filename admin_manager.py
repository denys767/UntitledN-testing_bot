import json
import os
from config import ADMIN_IDS, ADMINS_DB

# Глобальный список администраторов (включает конфиг + динамически добавленных)
all_admins = set(ADMIN_IDS)

def load_admins():
    """Загрузить администраторов из файла"""
    global all_admins
    if os.path.exists(ADMINS_DB):
        try:
            with open(ADMINS_DB, 'r') as f:
                saved_admins = json.load(f)
                all_admins = set(ADMIN_IDS) | set(saved_admins)
        except:
            all_admins = set(ADMIN_IDS)
    else:
        all_admins = set(ADMIN_IDS)

def save_admins():
    """Сохранить администраторов в файл"""
    # Сохраняем только динамически добавленных (исключая из конфига)
    dynamic_admins = list(all_admins - set(ADMIN_IDS))
    with open(ADMINS_DB, 'w') as f:
        json.dump(dynamic_admins, f)

def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь администратором"""
    return user_id in all_admins

async def add_admin(user_id: int) -> bool:
    """Добавить администратора"""
    if user_id not in all_admins:
        all_admins.add(user_id)
        save_admins()
        return True
    return False

async def get_all_admins():
    """Получить всех администраторов"""
    return list(all_admins)

# Загружаем администраторов при импорте модуля
load_admins()
