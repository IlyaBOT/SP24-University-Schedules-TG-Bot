import sqlite3




# Создаём базу данных и таблицу для хранения настроек
def init_db():
    conn = sqlite3.connect("user_settings.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            notification_time TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_settings (
            group_id INTEGER PRIMARY KEY,
            notification_time TEXT
        )
    """)
    conn.commit()
    conn.close()


# Инициализация базы данных при запуске
init_db()