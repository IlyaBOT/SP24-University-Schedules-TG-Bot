import sqlite3
import html
import re
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path


SETTINGS_DB_PATH = Path(__file__).with_name("user_settings.db")
WEEK_SHIFT_KEY = "week_shift"

SUBJECT_ABBREVIATIONS = {
    "Программирование интерфейсов вычислительных систем": "ПИВС",
    "Компьютерные системы": "КС",
    "Современные технологии программирования": "СТП",
    "Организация и функционирование процессорных устройств": "ОФПУ",
}

PAIR_PATTERN = re.compile(
    r"^(?P<number>\d+\.)\s+(?P<details>.*?)\s+(?P<time>\d{1,2}:\d{2}-\d{1,2}:\d{2})$"
)
SUBJECT_PATTERN = re.compile(
    r"(^| / )(.+? \((?:Лек|Лаб|Пр)\.\))"
)

# Осенний семестр 2026–2027, 3 курс СП-24, из файла «СП-24(26.10).xls».
# Физподготовка во вторник исключена по запросу пользователя.
upper_week_schedule = {
    'Понедельник': [
        '1. Современные технологии программирования (Лаб.) '
        '2 подгруппа Ауд. 4.016 доц. Чередникова О.Ю.   08:00-09:35',
        '2. Психология (Лек.) Ауд. 9.413 + ИИ-24, КИ-24, КСЦ-24 '
        'доц. Павлова Е.В.   09:55-11:30',
        '3. Веб-технологии (Лек.) Ауд. 4.014 + КИ-24 '
        'доц. Завадская Т.В.   11:50-13:25',
    ],
    'Вторник': [],
    'Среда': [
        '1. Программирование интерфейсов вычислительных систем (Пр.) '
        'Ауд. 4.016 асс. Шарибченко Е.И.   08:00-09:35',
        '2. Микроконтроллеры (Лек.) Ауд. 2.234 + КИ-24 '
        'доц. Краснокутский В.А.   09:55-11:30',
    ],
    'Четверг': [
        '2. Компьютерные системы (Лек.) Ауд. 2.234 + КИ-24, КСЦ-24 '
        'ст. преп. Струнилин В.Н.   09:55-11:30',
        '3. Операционные системы (Лек.) Ауд. 2.234 + КИ-24, КСЦ-24 '
        'доц. Чередникова О.Ю.   11:50-13:25',
    ],
    'Пятница': [
        '2. Микроконтроллеры (Лаб.) 1 подгруппа Ауд. 4.040 '
        'доц. Краснокутский В.А.   09:55-11:30',
        '3. Микроконтроллеры (Лаб.) 2 подгруппа Ауд. 4.040 '
        'доц. Краснокутский В.А. / '
        'Организация и функционирование процессорных устройств (Лаб.) '
        '1 подгруппа Ауд. 4.014 ст. преп. Койбаш А.А.   11:50-13:25',
        '4. Организация и функционирование процессорных устройств (Лаб.) '
        '2 подгруппа Ауд. 4.014 ст. преп. Койбаш А.А. / '
        'Современные технологии программирования (Лаб.) '
        '1 подгруппа Ауд. 4.019 доц. Чередникова О.Ю.   13:45-15:20',
    ],
    'Суббота': 'Доброе утречко, друзья, сегодня такой хороший день.. Выходной...! Желаю всем хорошо провести этот день!',
    'Воскресенье': 'Доброе утречко, друзья, сегодня такой хороший день.. Выходной...! Желаю всем хорошо провести этот день!',
}

lower_week_schedule = {
    'Понедельник': [
        '4. Компьютерные системы (Лаб.) 1 подгруппа Ауд. 4.026 '
        'ст. преп. Струнилин В.Н. / '
        'Веб-технологии (Лаб.) 2 подгруппа Ауд. 4.016 '
        'асс. Шубников В.С.   13:45-15:20',
        # Уточнение пользователя: на 5-й паре подгруппы меняются местами.
        '5. Веб-технологии (Лаб.) 1 подгруппа Ауд. 4.016 '
        'асс. Шубников В.С. / '
        'Компьютерные системы (Лаб.) 2 подгруппа Ауд. 4.026 '
        'ст. преп. Струнилин В.Н.   15:30-17:05',
    ],
    'Вторник': [],
    'Среда': [
        '3. Организация и функционирование процессорных устройств (Лек.) '
        'Ауд. 4.035 + КИ-24 доц. Мальчева Р.В.   11:50-13:25',
        '4. Программирование интерфейсов вычислительных систем (Лек.) '
        'Ауд. 4.014 + КИ-24 доц. Завадская Т.В.   13:45-15:20',
    ],
    'Четверг': [
        '1. Микроконтроллеры (Лаб.) 1 подгруппа Ауд. 4.040 '
        'доц. Краснокутский В.А.   08:00-09:35',
        '2. Программирование интерфейсов вычислительных систем (Лаб.) '
        '1 подгруппа Ауд. 4.016 асс. Шарибченко Е.И. / '
        'Микроконтроллеры (Лаб.) 2 подгруппа Ауд. 4.040 '
        'доц. Краснокутский В.А.   09:55-11:30',
        '3. Программирование интерфейсов вычислительных систем (Лаб.) '
        '2 подгруппа Ауд. 4.016 асс. Шарибченко Е.И.   11:50-13:25',
    ],
    'Пятница': [
        '1. Операционные системы (Лаб.) 1 подгруппа Ауд. 4.037 '
        'доц. Чередникова О.Ю.   08:00-09:35',
        '2. Современные технологии программирования (Лек.) '
        'Ауд. 2.233 доц. Чередникова О.Ю.   09:55-11:30',
        '3. Психология (Пр.) Ауд. 8.212 доц. Павлова Е.В.   11:50-13:25',
        '4. Операционные системы (Лаб.) 1) + КСЦ-24 Ауд. 4.037 '
        'асс. Личман А.А.   13:45-15:20',
    ],
    'Суббота': 'Доброе утречко, друзья, сегодня такой хороший день.. Выходной...! Желаю всем хорошо провести этот день!',
    'Воскресенье': 'Доброе утречко, друзья, сегодня такой хороший день.. Выходной...! Желаю всем хорошо провести этот день!',
}


def _format_time_range(time_range: str) -> str:
    """Убирает ведущие нули у часов: 08:00-09:35 -> 8:00-9:35."""
    start, end = time_range.split("-")

    def normalize(value: str) -> str:
        hour, minute = value.split(":")
        return f"{int(hour)}:{minute}"

    return f"{normalize(start)}-{normalize(end)}"


def format_pair(pair: str) -> str | None:
    """Форматирует одну пару для отправки в Telegram с parse_mode=HTML."""
    if "*" in pair:
        return None

    match = PAIR_PATTERN.match(pair.strip())
    if not match:
        return html.escape(pair)

    details = match.group("details")
    for full_name, abbreviation in SUBJECT_ABBREVIATIONS.items():
        details = details.replace(full_name, abbreviation)

    escaped_details = html.escape(details)
    emphasized_details = SUBJECT_PATTERN.sub(r"\1<b>\2</b>", escaped_details)
    time_range = _format_time_range(match.group("time"))

    return f'{match.group("number")} ({time_range}) {emphasized_details}'


def format_schedule(pairs: list[str], separator: str = "\n\n") -> str:
    """Форматирует список пар и пропускает служебные пустые позиции."""
    formatted_pairs = [formatted for pair in pairs if (formatted := format_pair(pair))]
    return separator.join(formatted_pairs)


def _init_week_settings():
    with sqlite3.connect(SETTINGS_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)


def _get_week_shift():
    _init_week_settings()
    with sqlite3.connect(SETTINGS_DB_PATH) as conn:
        row = conn.execute(
            "SELECT value FROM bot_settings WHERE key = ?",
            (WEEK_SHIFT_KEY,),
        ).fetchone()
    return int(row[0]) % 2 if row else 0


def switch_current_week():
    """Переключает чётность недели и сохраняет сдвиг в SQLite."""
    _init_week_settings()
    with sqlite3.connect(SETTINGS_DB_PATH) as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT value FROM bot_settings WHERE key = ?",
            (WEEK_SHIFT_KEY,),
        ).fetchone()
        current_shift = int(row[0]) % 2 if row else 0
        new_shift = 1 - current_shift
        conn.execute(
            """
            INSERT INTO bot_settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (WEEK_SHIFT_KEY, str(new_shift)),
        )

    get_schedule_for_today_cached.cache_clear()
    return get_current_week()


def get_current_week(tomorrow=False):
    today = datetime.today()
    if tomorrow:
        today += timedelta(days=1)  # Переходим на завтра

    week_number = today.isocalendar()[1] + _get_week_shift()
    return "upper" if week_number % 2 == 1 else "lower"


def get_schedule_for_today():
    current_week = get_current_week()
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    current_day = days[datetime.today().weekday()]

    if current_week == "upper":
        return upper_week_schedule.get(current_day, [])
    elif current_week == "lower":
        return lower_week_schedule.get(current_day, [])
    else:
        return upper_week_schedule.get(current_day, [])

def get_schedule_for_day(day: str, week_type: str):
    if week_type == "верхняя":
        return upper_week_schedule.get(day, "В этот день пар нет.")
    elif week_type == "нижняя":
        return lower_week_schedule.get(day, "В этот день пар нет.")
    else:
        return "Неверный тип недели."

@lru_cache(maxsize=1)
def get_schedule_for_today_cached():
    return get_schedule_for_today()
