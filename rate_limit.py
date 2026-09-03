import asyncio
import logging
import math
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message


class CommandRateLimitMiddleware(BaseMiddleware):
    """Ограничивает частоту команд отдельно для каждого пользователя."""

    def __init__(
        self,
        command_cooldown: int = 30,
        all_cooldown: int = 60,
        warning_lifetime: float = 5,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.command_cooldown = command_cooldown
        self.all_cooldown = all_cooldown
        self.warning_lifetime = warning_lifetime
        self._clock = clock
        self._last_used: dict[tuple[int, str], float] = {}
        self._deletion_tasks: set[asyncio.Task] = set()
        self._lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if not event.text or not event.text.startswith("/") or not event.from_user:
            return await handler(event, data)

        command = event.text.split(maxsplit=1)[0].split("@", maxsplit=1)[0].lower()
        is_all_command = command == "/all"
        bucket = "all" if is_all_command else "commands"
        cooldown = self.all_cooldown if is_all_command else self.command_cooldown
        key = (event.from_user.id, bucket)
        now = self._clock()

        async with self._lock:
            last_used = self._last_used.get(key)
            remaining = cooldown - (now - last_used) if last_used is not None else 0
            if remaining <= 0:
                self._last_used[key] = now

        if remaining > 0:
            await self._warn_user(
                event,
                math.ceil(remaining),
                is_all_command,
            )
            return None

        return await handler(event, data)

    async def _warn_user(
        self,
        message: Message,
        remaining_seconds: int,
        is_all_command: bool,
    ) -> None:
        if is_all_command:
            warning = (
                "Команду /all можно использовать не чаще одного раза в минуту. "
                f"Попробуйте снова через {remaining_seconds} сек."
            )
        else:
            warning = (
                "Команды можно использовать не чаще одного раза в 30 секунд. "
                f"Попробуйте снова через {remaining_seconds} сек."
            )

        sent_warning = await message.reply(warning)
        deletion_task = asyncio.create_task(self._delete_warning(sent_warning))
        self._deletion_tasks.add(deletion_task)
        deletion_task.add_done_callback(self._deletion_tasks.discard)

    async def _delete_warning(self, warning: Message) -> None:
        await asyncio.sleep(self.warning_lifetime)
        try:
            await warning.delete()
        except TelegramAPIError as error:
            logging.info("Не удалось удалить предупреждение о rate limit: %s", error)
