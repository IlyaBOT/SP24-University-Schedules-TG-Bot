import logging
import html
from datetime import datetime
from aiogram import Bot, types
from aiogram.enums import ParseMode
from schedule import format_schedule, get_schedule_for_today, get_current_week


async def send_welcome(message: types.Message):
    await message.answer("Привет! Я бот расписания группы СП-24.")

async def send_daily_notification(bot: Bot, chat_id: int):
    try:
        logging.info(f"Функция send_daily_notification вызвана для чата {chat_id}.")

        # Получаем текущий день недели и тип недели
        today = datetime.today()
        day_of_week = today.weekday()
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        current_day = days[day_of_week]
        current_week = get_current_week()

        # Преобразуем "upper" и "lower" в "верхняя" и "нижняя"
        week_type = "верхняя" if current_week == "upper" else "нижняя"

        # Проверяем, является ли день выходным
        if current_day in ["Суббота", "Воскресенье"]:
            response = (
                "Доброе утречко, друзья, сегодня такой хороший день.. "
                "Выходной! Желаю всем хорошо провести этот день!"
            )
        else:
            header = (
                f"Доброе утречко, сегодня у нас {current_day} "
                f"и {week_type} неделька!\n\nСписок пар:\n"
            )

            schedule = get_schedule_for_today()
            if isinstance(schedule, list):
                response = header + (format_schedule(schedule) or "Сегодня пар нет.")
            else:
                response = header + html.escape(schedule)

        # Отправляем сообщение в указанный чат
        try:
            logging.info(f"Попытка отправить сообщение в чат {chat_id}.")
            await bot.send_message(chat_id, text=response, parse_mode=ParseMode.HTML)
            logging.info(f"Сообщение отправлено в чат {chat_id}.")
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение в чат {chat_id}: {e}")
    except Exception as e:
        logging.error(f"Ошибка в send_daily_notification: {e}")
