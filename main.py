#!/usr/bin/env python3

import logging
import asyncio
from functools import partial
from aiogram import types
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand

from TopDonater import TopDonater_cmd
from bot_init import bot, dp
from config import TOKEN_API
from commands import send_pairs, send_current_week, send_nearest_pair, send_day_schedule, send_tomorrow_schedule, \
    show_reminder, send_weekly_schedule, set_reminder, test_reminder, send_next_week_schedule, cmd_id, \
    switch_week
from scheduler import scheduler, start_scheduler
from notifications import send_daily_notification, send_welcome
from TagAll import tag_all_members, MemberTrackerMiddleware, cleanup_inactive_members
from commands_info import commands_info
from rate_limit import CommandRateLimitMiddleware

# Регистрация обработчиков
dp.message.middleware(CommandRateLimitMiddleware())
dp.message.register(send_welcome, CommandStart())
dp.message.register(send_pairs, Command("pairs", ignore_case=True))
dp.message.register(send_current_week, Command("week", ignore_case=True))
dp.message.register(switch_week, Command("switchweek", ignore_case=True))
dp.message.register(send_nearest_pair, Command("pair", ignore_case=True))
dp.message.register(send_day_schedule, Command("pairday", ignore_case=True))
dp.message.register(send_tomorrow_schedule, Command("tomorrow", ignore_case=True))
dp.message.register(send_weekly_schedule, Command("allweek", ignore_case=True))
dp.message.register(show_reminder, Command("reminder", ignore_case=True))
dp.message.register(partial(test_reminder, bot=bot), Command("reminder_test", ignore_case=True))
dp.message.register(
    partial(set_reminder, scheduler=scheduler, bot=bot),
    Command("reminder_set", ignore_case=True),
)
dp.message.register(send_next_week_schedule, Command("nextweek"))
dp.message.register(tag_all_members, Command("all", ignore_case=True))
dp.message.register(cmd_id, Command("id", ignore_case=True))
dp.message.register(TopDonater_cmd, Command("top", ignore_case=True))


#Инициализация фоновых задач
dp.update.middleware(MemberTrackerMiddleware())
@dp.startup()
async def on_startup():
    await bot.set_my_commands([
        BotCommand(command=command.removeprefix("/"), description=description)
        for command, description in commands_info.items()
    ])
    logging.info("Меню команд Telegram синхронизировано.")
    asyncio.create_task(cleanup_inactive_members())
    logging.info("Фоновая задача очистки неактивных участников запущена.")

async def main():
    try:
        # Загружаем задачи из базы данных
        start_scheduler(bot)

        # Запускаем бота
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка в main: {e}")
    finally:
        # Останавливаем планировщик при завершении программы
        if scheduler.running:
            scheduler.shutdown()
        await bot.session.close()  # Закрываем сессию бота


if __name__ == '__main__':
    asyncio.run(main())
