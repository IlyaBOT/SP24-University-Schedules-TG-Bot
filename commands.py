from schedule import get_schedule_for_today, get_current_week, get_schedule_for_day, upper_week_schedule, lower_week_schedule
from time_utils import get_current_and_next_pair
from datetime import datetime, timedelta
from aiogram.enums import ParseMode
from aiogram import types, Bot
import sqlite3
import logging
from notifications import send_daily_notification
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from functools import lru_cache



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
            filtered_schedule = []
            for pair in schedule:
                if "*" not in pair:
                    # Разбиваем строку на составляющие
                    parts = pair.split()
                    pair_number = parts[0]
                    pair_name = ' '.join(parts[1:-3])  # Название пары и тип
                    pair_time = f"{parts[-3]} {parts[-2]}"  # Время
                    pair_room = parts[-1]  # Аудитория

                    # Форматируем строку с аудиторией
                    formatted_pair = f"{pair_number} {pair_name} {pair_time} {pair_room}"
                    filtered_schedule.append(formatted_pair)

            response = "\n\n".join(filtered_schedule) if filtered_schedule else "Сегодня пар нет."
        else:
            response = "Не удалось получить расписание."

        await message.reply(response, parse_mode=ParseMode.MARKDOWN)
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


async def send_nearest_pair(message: types.Message):
    try:
        schedule = get_schedule_for_today_cached()

        if isinstance(schedule, str):
            response = "Сегодня выходной, пар нет."
        elif isinstance(schedule, list):
            current_pair, next_pair = get_current_and_next_pair(schedule)

            def format_pair(pair):
                if not pair:
                    return None
                parts = pair.split()
                return f"{parts[0]} {' '.join(parts[1:-3])} {parts[-3]} {parts[-2]} {parts[-1]}"

            if current_pair:
                response = f"Сейчас идёт пара:\n{format_pair(current_pair)}"
            elif next_pair:
                response = f"Ближайшая пара:\n{format_pair(next_pair)}"
            else:
                response = "Пары закончились на сегодня."
        else:
            response = "Не удалось получить расписание."

        await message.reply(response, parse_mode=ParseMode.MARKDOWN)
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
            filtered_schedule = []
            for pair in schedule:
                if "*" not in pair:
                    parts = pair.split()
                    pair_number = parts[0]
                    pair_name = ' '.join(parts[1:-3])
                    pair_time = f"{parts[-3]} {parts[-2]}"
                    pair_room = parts[-1]

                    formatted_pair = f"{pair_number} {pair_name} {pair_time} {pair_room}"
                    filtered_schedule.append(formatted_pair)

            response = (f"Расписание на {day} ({week_type} неделя):\n\n" +
                        "\n\n".join(filtered_schedule) if filtered_schedule else f"В {day} пар нет.")
        else:
            response = "Ошибка получения расписания."

        await message.reply(response, parse_mode=ParseMode.MARKDOWN)
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
                filtered_schedule = []
                for pair in schedule:
                    if "*" not in pair:
                        parts = pair.split()
                        formatted_pair = f"{parts[0]} {' '.join(parts[1:-3])} {parts[-3]} {parts[-2]} {parts[-1]}"
                        filtered_schedule.append(formatted_pair)

                response = "\n\n".join(filtered_schedule) if filtered_schedule else "Завтра пар нет."
            else:
                response = "Не удалось получить расписание."

        await message.reply(response, parse_mode=ParseMode.MARKDOWN)
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

        response += f"*{day}:*\n"
        if isinstance(pairs, list):
            filtered_pairs = []
            for pair in pairs:
                if "*" not in pair:
                    parts = pair.split()
                    formatted_pair = f"{parts[0]} {' '.join(parts[1:-3])} {parts[-3]} {parts[-2]} {parts[-1]}"
                    filtered_pairs.append(formatted_pair)

            response += "\n".join(filtered_pairs) + "\n\n"
        else:
            response += pairs + "\n\n"

    await message.reply(response, parse_mode=ParseMode.MARKDOWN)

async def set_notification_time(message: types.Message, scheduler: AsyncIOScheduler, bot: Bot):
    try:
        # Получаем аргумент команды
        args = message.text.split()
        if len(args) < 2:
            raise ValueError("Что-то пошло не так, попробуйте /set_not_time 07:30 / never")

        time = args[1]  # Получаем время из команды
        user_id = message.from_user.id
        chat_id = message.chat.id

        # Обработка команды "never"
        if time.lower() == "never":
            # Удаляем задачу из планировщика
            for job in scheduler.get_jobs():
                if job.args[1] == (user_id if message.chat.type == "private" else chat_id):
                    job.remove()
                    logging.info(f"Задача для {'пользователя' if message.chat.type == 'private' else 'группы'} {user_id if message.chat.type == 'private' else chat_id} удалена.")

            # Удаляем запись из базы данных
            with sqlite3.connect("user_settings.db") as conn:
                cursor = conn.cursor()
                if message.chat.type == "private":  # Личные сообщения
                    cursor.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
                else:  # Группа
                    cursor.execute("DELETE FROM group_settings WHERE group_id = ?", (chat_id,))
                conn.commit()

            await message.answer("Уведомления отключены.")
            return

        # Проверяем, что время введено в формате HH:MM
        if not time.replace(":", "").isdigit() or len(time) != 5 or time[2] != ":":
            raise ValueError("Некорректный формат времени. Используйте HH:MM или 'never' для отключения уведомлений.")

        # Разбираем время на часы и минуты
        hour, minute = map(int, time.split(":"))
        logging.info(f"Время разобрано: {hour}:{minute}")

        # Используем контекстный менеджер для работы с базой данных
        with sqlite3.connect("user_settings.db") as conn:
            cursor = conn.cursor()

            # Определяем, вызвана ли команда в группе или в личных сообщениях
            if message.chat.type == "private":  # Личные сообщения
                # Удаляем старое время уведомлений для пользователя
                cursor.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
                # Добавляем новое время уведомлений
                cursor.execute("""
                    INSERT INTO user_settings (user_id, notification_time)
                    VALUES (?, ?)
                """, (user_id, time))

                # Удаляем старую задачу из планировщика, если она существует
                for job in scheduler.get_jobs():
                    if job.args[1] == user_id:  # Проверяем, что задача относится к этому пользователю
                        job.remove()

                # Добавляем новую задачу в планировщик
                scheduler.add_job(
                    send_daily_notification,
                    CronTrigger(hour=hour, minute=minute),
                    args=[bot, user_id],  # Передаём ID пользователя
                    id=f"user_{user_id}"  # Уникальный идентификатор задачи
                )

            else:  # Группа
                # Удаляем старое время уведомлений для группы
                cursor.execute("DELETE FROM group_settings WHERE group_id = ?", (chat_id,))
                # Добавляем новое время уведомлений
                cursor.execute("""
                    INSERT INTO group_settings (group_id, notification_time)
                    VALUES (?, ?)
                """, (chat_id, time))

                # Удаляем старую задачу из планировщика, если она существует
                for job in scheduler.get_jobs():
                    if job.args[1] == chat_id:  # Проверяем, что задача относится к этой группе
                        job.remove()

                # Добавляем новую задачу в планировщик
                scheduler.add_job(
                    send_daily_notification,
                    CronTrigger(hour=hour, minute=minute),
                    args=[bot, chat_id],  # Передаём ID группы
                    id=f"group_{chat_id}"  # Уникальный идентификатор задачи
                )

            # Сохраняем изменения в базе данных
            conn.commit()

        await message.answer(f"Время уведомлений установлено на {time}.")
    except Exception as e:
        logging.error(f"Ошибка в set_notification_time: {e}", exc_info=True)
        # Отправляем пользователю одно сообщение об ошибке
        await message.answer("Что-то пошло не так, попробуйте /set_not_time 07:30 / never")

async def test_notification(message: types.Message, bot: Bot):
    try:
        chat_id = message.chat.id  # Получаем ID чата
        await send_daily_notification(bot, chat_id)  # Передаём bot и chat_id
    except Exception as e:
        logging.error(f"Ошибка в test_notification: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

async def not_list(message: types.Message):
    try:
        chat_id = message.chat.id  # ID чата (группы или пользователя)
        user_id = message.from_user.id  # ID пользователя

        # Определяем, вызвана ли команда в группе или в личных сообщениях
        if message.chat.type == "private":  # Личные сообщения
            # Получаем настройки уведомлений для пользователя
            conn = sqlite3.connect("user_settings.db")
            cursor = conn.cursor()
            cursor.execute("SELECT notification_time FROM user_settings WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()

            if result:
                notification_time = result[0]
                await message.answer(f"Ваше время уведомлений: {notification_time}")
            else:
                await message.answer("У вас не настроено время уведомлений.")

        else:  # Группа
            # Получаем настройки уведомлений для группы
            conn = sqlite3.connect("user_settings.db")
            cursor = conn.cursor()
            cursor.execute("SELECT notification_time FROM group_settings WHERE group_id = ?", (chat_id,))
            result = cursor.fetchone()
            conn.close()

            if result:
                notification_time = result[0]
                await message.answer(f"Время уведомлений для этой группы: {notification_time}")
            else:
                await message.answer("Для этой группы не настроено время уведомлений.")

    except Exception as e:
        logging.error(f"Ошибка в not_list: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

async def send_next_week_schedule(message: types.Message):
    current_week = get_current_week()
    schedule = lower_week_schedule if current_week == "upper" else upper_week_schedule
    response = "Расписание на следующую неделю:\n\n"

    for day, pairs in schedule.items():
        if day in ["Суббота", "Воскресенье"]:
            continue

        response += f"*{day}:*\n"
        if isinstance(pairs, list):
            filtered_pairs = []
            for pair in pairs:
                if "*" not in pair:
                    parts = pair.split()
                    formatted_pair = f"{parts[0]} {' '.join(parts[1:-3])} {parts[-3]} {parts[-2]} {parts[-1]}"
                    filtered_pairs.append(formatted_pair)

            response += "\n".join(filtered_pairs) + "\n\n"
        else:
            response += pairs + "\n\n"

    await message.reply(response, parse_mode=ParseMode.MARKDOWN)

async def cmd_id(message: types.Message):
    # Получаем ID пользователя и ID чата (если в группе)
    user_id = message.from_user.id
    chat_id = message.chat.id if message.chat else "Личное сообщение"

    # Формируем сообщение
    response = f"Ваш ID: {user_id}\nID чата: {chat_id}"

    # Отправляем ответ пользователю
    await message.reply(response)