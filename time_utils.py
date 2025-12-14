from datetime import datetime, timedelta
import logging
import re
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def parse_pair_time(pair_str):
    """Парсит строку с парой и возвращает время начала и конца"""
    try:
        # Используем регулярное выражение для поиска времени
        time_match = re.search(r'(\d{1,2}:\d{2})-(\d{1,2}:\d{2})', pair_str)
        if not time_match:
            return None, None

        start_time_str, end_time_str = time_match.groups()
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
        return start_time, end_time
    except Exception as e:
        logging.error(f"Ошибка парсинга времени в строке '{pair_str}': {e}")
        return None, None


def get_current_and_next_pair(schedule):
    current_pair = None
    next_pair = None
    current_time = datetime.now().time()

    if not isinstance(schedule, list):
        return None, None

    for pair in schedule:
        if "*" in pair:  # Пропускаем специальные отметки
            continue

        start_time, end_time = parse_pair_time(pair)
        if not start_time or not end_time:
            continue

        # Определяем текущую и следующую пару
        if start_time <= current_time <= end_time:
            current_pair = pair
        elif current_time < start_time:
            if next_pair is None:
                next_pair = pair
            else:
                # Сравниваем с уже найденной следующей парой
                next_start, _ = parse_pair_time(next_pair)
                if start_time < next_start:
                    next_pair = pair

    return current_pair, next_pair