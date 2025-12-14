import sqlite3
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
import logging
from notifications import send_daily_notification

# Инициализация базы данных
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

init_db()  # Инициализируем базу данных при запуске

scheduler = AsyncIOScheduler()


def start_scheduler(bot: Bot):
    logging.info("Запуск планировщика...")

    # Задачи для уведомлений в группах
    conn = sqlite3.connect("user_settings.db")
    cursor = conn.cursor()
    cursor.execute("SELECT group_id, notification_time FROM group_settings")
    groups = cursor.fetchall()

    # Задачи для индивидуальных уведомлений пользователей
    cursor.execute("SELECT user_id, notification_time FROM user_settings")
    users = cursor.fetchall()
    conn.close()

    # Добавляем задачи для групп
    for group_id, notification_time in groups:
        hour, minute = map(int, notification_time.split(":"))
        scheduler.add_job(
            send_daily_notification,
            CronTrigger(hour=hour, minute=minute),
            args=[bot, group_id],  # Передаём ID группы
            id=f"group_{group_id}"  # Уникальный идентификатор задачи
        )
        logging.info(f"Добавлена задача для группы {group_id} на {hour}:{minute}")

    # Добавляем задачи для пользователей
    for user_id, notification_time in users:
        hour, minute = map(int, notification_time.split(":"))
        scheduler.add_job(
            send_daily_notification,
            CronTrigger(hour=hour, minute=minute),
            args=[bot, user_id],  # Передаём ID пользователя
            id=f"user_{user_id}"  # Уникальный идентификатор задачи
        )
        logging.info(f"Добавлена задача для пользователя {user_id} на {hour}:{minute}")

    scheduler.start()  # Запускаем планировщик
    logging.info("Планировщик запущен.")