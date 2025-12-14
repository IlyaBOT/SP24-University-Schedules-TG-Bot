import logging
import asyncio
from functools import partial
from aiogram import types
from aiogram.filters import Command

from TopDonater import TopDonater_cmd
from bot_init import bot, dp
from config import TOKEN_API
from commands import send_pairs, send_current_week, send_nearest_pair, send_day_schedule, send_tomorrow_schedule, \
    not_list, send_weekly_schedule, set_notification_time, test_notification, send_next_week_schedule, cmd_id
from scheduler import start_scheduler
from notifications import send_daily_notification, send_help
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from TagAll import tag_all_members, MemberTrackerMiddleware, cleanup_inactive_members
from Update import cmd_update

# Инициализация планировщика
scheduler = AsyncIOScheduler()

# Регистрация обработчиков
dp.message.register(send_pairs, Command("pairs", ignore_case=True))
dp.message.register(send_current_week, Command("week", ignore_case=True))
dp.message.register(send_nearest_pair, Command("pair", ignore_case=True))
dp.message.register(send_day_schedule, Command("pairday", ignore_case=True))
dp.message.register(send_tomorrow_schedule, Command("tomorrow", ignore_case=True))
dp.message.register(send_weekly_schedule, Command("allweek", ignore_case=True))
dp.message.register(not_list, Command("not_time", ignore_case=True))
dp.message.register(partial(test_notification, bot=bot), Command("test_not", ignore_case=True))
dp.message.register(partial(set_notification_time, scheduler=scheduler, bot=bot),
                    Command("set_not_time", ignore_case=True))
dp.message.register(send_help, Command("help", ignore_case=True))
dp.message.register(send_next_week_schedule, Command("nextweek"))
dp.message.register(tag_all_members, Command("all", ignore_case=True))
dp.message.register(cmd_id, Command("id", ignore_case=True))
dp.message.register(cmd_update, Command("update", ignore_case=True))
dp.message.register(TopDonater_cmd, Command("top", ignore_case=True))


#Инициализация фоновых задач
dp.update.middleware(MemberTrackerMiddleware())
@dp.startup()
async def on_startup():
    cmd_update
    asyncio.create_task(cleanup_inactive_members())
    logging.info("Фоновая задача очистки неактивных участников запущена.")

async def main():
    try:
        # Запускаем планировщик
        scheduler.start()
        logging.info("Планировщик запущен.")

        # Загружаем задачи из базы данных
        start_scheduler(bot)

        # Запускаем бота
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка в main: {e}")
    finally:
        # Останавливаем планировщик при завершении программы
        scheduler.shutdown()
        await bot.session.close()  # Закрываем сессию бота


if __name__ == '__main__':
    asyncio.run(main())