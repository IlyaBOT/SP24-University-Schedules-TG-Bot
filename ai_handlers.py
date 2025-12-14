from aiogram import types, Router, F
from bot_init import bot
import re

router = Router()

@router.message(F.text)  # Фильтр: обрабатываем только текстовые сообщения
async def handle_message(message: types.Message):
    # Определяем регулярное выражение внутри функции
    command_pattern = re.compile(
        r"\b(?:г[эе]д[эе]|гдэ|где)\b.*\b(?:пара|паро|пора|поро)\b[?]?",
        re.IGNORECASE
    )

    text = message.text  # Получаем текст сообщения

    # Проверяем, соответствует ли текст регулярному выражению
    if command_pattern.search(text):
        await message.reply("Используй /pair и жди пока начнётся твоя паро. ")
    # Добавляйте другие команды здесь