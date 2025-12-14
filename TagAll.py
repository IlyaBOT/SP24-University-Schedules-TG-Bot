import os
import sqlite3
import logging
from datetime import datetime, timedelta
from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.enums import ParseMode
import asyncio

DB_PATH = 'data/members.db'

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s - %(message)s')

def init_db():
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_members (
            chat_id INTEGER,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            last_activity TIMESTAMP,
            PRIMARY KEY (chat_id, user_id)
        )
    ''')
    conn.commit()
    conn.close()
    logging.info("[DB] База данных group_members инициализирована")


init_db()


class MemberTrackerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        message = getattr(event, 'message', None)
        if not message:
            return await handler(event, data)

        logging.info(f"[Middleware] Получено сообщение в чате {getattr(message.chat, 'id', '???')} типа {getattr(message.chat, 'type', '???')}")
        if message.chat.type not in ('group', 'supergroup'):
            return await handler(event, data)

        user = message.from_user
        chat_id = message.chat.id

        logging.info(f"[Middleware] Обработка пользователя: {user.id} ({user.username})")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO group_members 
            (chat_id, user_id, username, first_name, last_name, last_activity) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            chat_id,
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))

        conn.commit()
        conn.close()
        logging.info(f"[Middleware] Обновлён пользователь {user.id} в чате {chat_id}")
        return await handler(event, data)


async def cleanup_inactive_members():
    """Фоновая задача очистки неактивных участников"""
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                DELETE FROM group_members 
                WHERE last_activity < ?
            ''', (cutoff_date,))
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted_count > 0:
                logging.info(f"[Cleaner] Удалено {deleted_count} неактивных участников")
        except Exception as e:
            logging.error(f"[Cleaner] Ошибка при удалении: {e}")

        await asyncio.sleep(86400)  # раз в сутки


async def tag_all_members(message: types.Message):
    chat_id = message.chat.id

    # Для отладки временно убираем cutoff
    # cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, last_activity
        FROM group_members 
        WHERE chat_id = ?
    ''', (chat_id,))
    members = cursor.fetchall()
    conn.close()

    logging.info(f"[TagAll] Команда от {message.from_user.id} — найдено {len(members)} участников")

    if not members:
        await message.reply("⚠️ Нет участников в базе данных!")
        return

    # Отладочный лог всех записей
    for member in members:
        logging.info(f"[TagAll] Участник: ID={member[0]}, username={member[1]}, имя={member[2]}, активность={member[4]}")

    user_mentions = []
    for user_id, username, first_name, last_name, _ in members:
        name = f"{first_name} {last_name}" if last_name else first_name
        if username:
            user_mentions.append(f"@{username}")
        else:
            user_mentions.append(f'<a href="tg://user?id={user_id}">{name}</a>')

    if len(user_mentions) <= 20:
        await message.reply(
            f"⚠️ ВОССТАНЬТЕ! ⚠️\n{' '.join(user_mentions)}",
            parse_mode=ParseMode.HTML
        )
    else:
        for i in range(0, len(user_mentions), 5):
            batch = user_mentions[i:i + 5]
            await message.reply(
                f"⚠️ ARISE ⚠️\n{' '.join(batch)}",
                parse_mode=ParseMode.HTML
            )
            await asyncio.sleep(1)
