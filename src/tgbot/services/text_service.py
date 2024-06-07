import datetime
import math
import re


def generate_search_results_summary(search_results_info: dict) -> str:
    text = (
        f"Всего найдено: {search_results_info['count']}\n"
        f"Всего страниц: {search_results_info['total_pages']}\n"
        f'Торрентов в странице: {len(search_results_info['result'])}'
    )
    return text


def get_torrent_info_text(torrent_info: dict) -> str:
    text = (
        f"Название: {torrent_info['title'][:50]}\n"
        f"Автор: {torrent_info['author']}\n"
        f"Категория: {torrent_info['category']}\n"
        f"Размер: {convert_size(torrent_info['size'])}\n"
        f"Сиды: {torrent_info['seeds']}\n"
        f"Личи: {torrent_info['leeches']}\n"
        f"Скачиваний: {torrent_info['downloads']}\n"
        f"Добавлен: {format_timestamp(torrent_info['registered'])}"
    )
    return text


def get_user_info_text(user_info: dict | None = None) -> str:
    if user_info:
        stats = user_info['Статистика отданного']
        text = (
            f"Авторизован: да\n"
            f"Роль: {user_info['Роль']}\n"
            f"Стаж: {user_info['Стаж']}\n"
            f"Зарегистрирован: {user_info['Зарегистрирован']}\n\n\n"
            f"Статистика раздач:\n\n"
            f"Сегодня: {stats['Сегодня']}\n"
            f"Вчера: {stats['Вчера']}\n"
            f"Всего: {stats['Всего']}\n"
            f"На редких: {stats['На редких']}\n"
        )
    else:
        text = 'Авторизован: нет\n\n/login'
    return text


def find_snippet_from_search_term(title: str, search_term: str,
                                  max_length: int) -> str:
    # Преобразуем все в нижний регистр для нечувствительного к регистру поиска
    title_lower = title.lower()
    search_term_lower = search_term.lower()

    # Ищем все слова в названии
    words = re.findall(r'\b\w+\b', title_lower)

    # Проходим по словам и ищем наиболее подходящее слово для поиска
    for word in words:
        if search_term_lower in word:
            # Если нашли слово, то определяем его
            # начальную позицию в оригинальном названии
            start_index = title_lower.find(word)
            end_index = start_index + max_length
            if end_index > len(title):
                end_index = len(title)
            return title[start_index:end_index]

    # Если ничего не нашли, возвращаем первые max_length символов
    return title[:max_length]


def format_timestamp(timestamp: int) -> str:
    """Преобразует Unix timestamp в читаемый формат даты и времени"""
    date_time = datetime.datetime.fromtimestamp(timestamp)
    return date_time.strftime('%Y-%m-%d %H:%M:%S')


def convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"