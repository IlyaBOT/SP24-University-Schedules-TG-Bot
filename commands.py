from schedule import (
    get_schedule_for_today,
    get_current_week,
    get_schedule_for_day,
    switch_current_week,
    upper_week_schedule,
    lower_week_schedule,
    format_pair,
    format_schedule,
)
from time_utils import get_current_and_next_pair
from datetime import datetime, timedelta
from aiogram.enums import ParseMode
from aiogram import types, Bot
import sqlite3
import logging
import re
from notifications import send_daily_notification
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from functools import lru_cache
from config import MAIN_ADMIN_ID



@lru_cache(maxsize=1)
def get_schedule_for_today_cached():
    return get_schedule_for_today()

@lru_cache(maxsize=7)  # Кэшируем на 7 дней
def get_schedule_for_day_cached(day: str, week_type: str):
    return get_schedule_for_day(day, week_type)


async def send_pairs(message: types.Message):
    try:
        schedule = get_schedule_for_today()

        if isinstance(schedule, str):
            response = "Сегодня выходной, пар нет."
        elif isinstance(schedule, list):
            response = format_schedule(schedule) or "Сегодня пар нет."
        else:
            response = "Не удалось получить расписание."

        await message.reply(response, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Ошибка в send_pairs: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.")

async def send_current_week(message: types.Message):
    current_week = get_current_week()
    if current_week == "upper":
        response = "Сейчас верхняя неделя\\."
    else:
        response = "Сейчас нижняя неделя\\."
    await message.reply(response, parse_mode=ParseMode.MARKDOWN_V2)


async def change_week(message: types.Message):
    if not message.from_user or message.from_user.id != MAIN_ADMIN_ID:
        await message.reply("Эта команда доступна только главному администратору.")
        return

    try:
        current_week = switch_current_week()
        get_schedule_for_today_cached.cache_clear()
        week_name = "верхняя" if current_week == "upper" else "нижняя"
        await message.reply(
            f"Неделя переключена. Теперь используется {week_name} неделя. "
            "Изменение сохранено."
        )
    except Exception as e:
        logging.error(f"Ошибка в change_week: {e}", exc_info=True)
        await message.reply("Не удалось переключить неделю. Попробуйте позже.")


async def send_nearest_pair(message: types.Message):
    try:
        schedule = get_schedule_for_today_cached()

        if isinstance(schedule, str):
            response = "Сегодня выходной, пар нет."
        elif isinstance(schedule, list):
            current_pair, next_pair = get_current_and_next_pair(schedule)

            if current_pair:
                response = f"Сейчас идёт пара:\n{format_pair(current_pair)}"
            elif next_pair:
                response = f"Ближайшая пара:\n{format_pair(next_pair)}"
            else:
                response = "Пары закончились на сегодня."
        else:
            response = "Не удалось получить расписание."

        await message.reply(response, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Ошибка в send_nearest_pair: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.")


async def send_day_schedule(message: types.Message):
    try:
        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            await message.reply("Используйте: /day день недели (верхняя/нижняя)")
            return

        day = args[1].strip().capitalize()
        week_type = args[2].strip().lower()

        schedule = get_schedule_for_day(day, week_type)

        if isinstance(schedule, str):
            response = schedule
        elif isinstance(schedule, list):
            formatted_schedule = format_schedule(schedule)
            response = (
                f"Расписание на {day} ({week_type} неделя):\n\n{formatted_schedule}"
                if formatted_schedule
                else f"В {day} пар нет."
            )
        else:
            response = "Ошибка получения расписания."

        await message.reply(response, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Ошибка в send_day_schedule: {e}")
        await message.reply("Произошла ошибка. Проверьте правильность ввода.")


async def send_tomorrow_schedule(message: types.Message):
    try:
        tomorrow = datetime.today() + timedelta(days=1)
        days_mapping = {
            "Monday": "Понедельник",
            "Tuesday": "Вторник",
            "Wednesday": "Среда",
            "Thursday": "Четверг",
            "Friday": "Пятница",
            "Saturday": "Суббота",
            "Sunday": "Воскресенье"
        }
        tomorrow_day_ru = days_mapping.get(tomorrow.strftime("%A"), "Неизвестный день")

        current_week = get_current_week(tomorrow=True)
        week_type = "верхняя" if current_week == "upper" else "нижняя"

        if tomorrow_day_ru in ["Суббота", "Воскресенье"]:
            response = "Завтра выходной, пар нет."
        else:
            schedule = get_schedule_for_day(tomorrow_day_ru, week_type)

            if isinstance(schedule, str):
                response = "Завтра пар нет."
            elif isinstance(schedule, list):
                response = format_schedule(schedule) or "Завтра пар нет."
            else:
                response = "Не удалось получить расписание."

        await message.reply(response, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Ошибка в send_tomorrow_schedule: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.")


async def send_weekly_schedule(message: types.Message):
    current_week = get_current_week()
    schedule = upper_week_schedule if current_week == "upper" else lower_week_schedule
    response = "Расписание на текущую неделю:\n\n"

    for day, pairs in schedule.items():
        if day in ["Суббота", "Воскресенье"]:
            continue

        response += f"<b>{day}:</b>\n"
        if isinstance(pairs, list):
            response += (format_schedule(pairs, separator="\n") or "Пар нет.") + "\n\n"
        else:
            response += pairs + "\n\n"

    await message.reply(response, parse_mode=ParseMode.HTML)

REMINDER_TIME_PATTERN = re.compile(r"^(?:[01]?\d|2[0-3]):[0-5]\d$")


def _reminder_target(message: types.Message):
    if message.chat.type == "private":
        return "user_settings", "user_id", message.from_user.id, "user"
    return "group_settings", "group_id", message.chat.id, "group"


async def set_reminder(message: types.Message, scheduler: AsyncIOScheduler, bot: Bot):
    args = (message.text or "").split(maxsplit=1)
    if len(args) != 2 or not REMINDER_TIME_PATTERN.fullmatch(args[1].strip()):
        await message.answer("Используйте: /reminder_set 7:30")
        return

    hour, minute = map(int, args[1].strip().split(":"))
    notification_time = f"{hour}:{minute:02d}"
    table, id_column, target_id, target_type = _reminder_target(message)
    job_id = f"{target_type}_{target_id}"

    try:
        with sqlite3.connect("user_settings.db") as conn:
            conn.execute(
                f"""
                INSERT INTO {table} ({id_column}, notification_time)
                VALUES (?, ?)
                ON CONFLICT({id_column}) DO UPDATE
                SET notification_time = excluded.notification_time
                """,
                (target_id, notification_time),
            )

        scheduler.add_job(
            send_daily_notification,
            CronTrigger(hour=hour, minute=minute),
            args=[bot, target_id],
            id=job_id,
            replace_existing=True,
        )
        await message.answer(
            f"Напоминание установлено на {notification_time}. "
            "В это время бот будет отправлять расписание дня."
        )
    except Exception as e:
        logging.error(f"Ошибка в set_reminder: {e}", exc_info=True)
        await message.answer("Не удалось установить напоминание. Попробуйте позже.")


async def show_reminder(message: types.Message):
    table, id_column, target_id, _ = _reminder_target(message)

    try:
        with sqlite3.connect("user_settings.db") as conn:
            result = conn.execute(
                f"SELECT notification_time FROM {table} WHERE {id_column} = ?",
                (target_id,),
            ).fetchone()

        if result:
            await message.answer(
                f"Напоминание установлено на {result[0]}. "
                "В это время бот отправит расписание дня."
            )
        else:
            await message.answer("Напоминание не установлено.")
    except Exception as e:
        logging.error(f"Ошибка в show_reminder: {e}", exc_info=True)
        await message.answer("Не удалось получить информацию о напоминании.")


async def test_reminder(message: types.Message, bot: Bot):
    """Отправляет расписание сейчас, не изменяя сохранённое напоминание."""
    await send_daily_notification(bot, message.chat.id)

async def send_next_week_schedule(message: types.Message):
    current_week = get_current_week()
    schedule = lower_week_schedule if current_week == "upper" else upper_week_schedule
    response = "Расписание на следующую неделю:\n\n"

    for day, pairs in schedule.items():
        if day in ["Суббота", "Воскресенье"]:
            continue

        response += f"<b>{day}:</b>\n"
        if isinstance(pairs, list):
            response += (format_schedule(pairs, separator="\n") or "Пар нет.") + "\n\n"
        else:
            response += pairs + "\n\n"

    await message.reply(response, parse_mode=ParseMode.HTML)

async def cmd_id(message: types.Message):
    # Получаем ID пользователя и ID чата (если в группе)
    user_id = message.from_user.id
    chat_id = message.chat.id if message.chat else "Личное сообщение"

    # Формируем сообщение
    response = f"Ваш ID: {user_id}\nID чата: {chat_id}"

    # Отправляем ответ пользователю
    await message.reply(response)
