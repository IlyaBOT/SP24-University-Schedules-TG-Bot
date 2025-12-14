import logging
from datetime import datetime
from aiogram import Bot, types
from aiogram.enums import ParseMode
from schedule import get_schedule_for_today, get_current_week
from commands_info import commands_info

def escape_markdown(text: str) -> str:
    """Экранирует зарезервированные символы для MarkdownV2."""
    reserved_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in reserved_chars:
        text = text.replace(char, f"\\{char}")
    return text


async def send_help(message: types.Message):
    help_text = "Скромный список доступных команд: \n\n"
    for command, description in commands_info.items():
        help_text += f"{escape_markdown(command)} — {escape_markdown(description)}\n\n"
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN_V2)

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
            # Формируем сообщение для выходных
            response = escape_markdown(
                "Доброе утречко, друзья, сегодня такой хороший день.. Выходной! Желаю всем хорошо провести этот день!"
            )
        else:
            # Формируем заголовок сообщения для рабочих дней
            header = escape_markdown(
                f"Доброе утречко, сегодня у нас {current_day} и {week_type} неделька!\n\nСписок пар:\n"
            )

            # Получаем расписание на сегодня
            schedule = get_schedule_for_today()
            if isinstance(schedule, list):
                filtered_schedule = [escape_markdown(pair) for pair in schedule if "*" not in pair]
                response = header + "\n".join(filtered_schedule) if filtered_schedule else header + "Сегодня пар нет."
            else:
                response = header + escape_markdown(schedule)

        # Отправляем сообщение в указанный чат
        try:
            logging.info(f"Попытка отправить сообщение в чат {chat_id}.")
            await bot.send_message(chat_id, text=response, parse_mode=ParseMode.MARKDOWN_V2)
            logging.info(f"Сообщение отправлено в чат {chat_id}.")
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение в чат {chat_id}: {e}")
    except Exception as e:
        logging.error(f"Ошибка в send_daily_notification: {e}")