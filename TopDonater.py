from aiogram import types


# Функция для чтения данных из текстового файла и форматирования
async def read_update_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # Чтение строк из файла
            lines = file.readlines()

            # Формирование сообщения в виде списка
            update_message = "Список всех донатеров:\n\n"  # Поменял местами эмодзи
            for idx, line in enumerate(lines, start=1):
                update_message += f"{idx}. {line.strip()}\n\n"

            return update_message
    except Exception as e:
        return f"Ошибка при чтении файла: {e}"

# Обработчик команды /update
async def TopDonater_cmd(message: types.Message):
    file_path = "TopDonater.txt"  # Путь к твоему текстовому файлу с обновлениями

    update_message = await read_update_from_file(file_path)

    # Отправка сообщения с обновлениями
    await message.reply(update_message)

