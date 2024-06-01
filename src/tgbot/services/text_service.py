def get_torrent_info_text(torrent_info: dict) -> str:
    text = (
        f"Название: {torrent_info['title'][:20]}"
        f"Автор: {torrent_info['author']}\n"
        f"Категория: {torrent_info['category']}\n"
        f"Сиды: {torrent_info['seeds']}\n"
        f"Личи: {torrent_info['leeches']}\n"
        f"Скачиваний: {torrent_info['downloads']}"
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
