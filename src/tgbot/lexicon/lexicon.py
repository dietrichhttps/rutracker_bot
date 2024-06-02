LEXICON: dict[str, str] = {
    'forward': '>>',
    'backward': '<<',
    '/start': 'Это рутрекер-бот\nОн умеет скачивать торрент-файлы с рутрекера\n\n'
              'Чтобы посмотреть список доступных '
              'команд - набери /help',
    '/help':  'Доступные команды:\n\n/login - авторизоваться в рутрекере\n'
              '/status - статус пользователя\n/settings - настройки бота\n'
              '/get_torrent - поиск и скачивание торрент-файла'
}

LEXICON_COMMANDS: dict[str, str] = {
    '/login': 'Авторизоваться в рутрекере',
    '/status': 'Статус пользователя',
    '/get_torrent': 'Скачать торрент',
    '/settings': 'Настройки бота',
    '/help': 'Справка'
}

LEXICON_SETTINGS = {
    'list': 'список',
    'card': 'карточки',
    'seeds': 'по сидам',
    'leeches': 'по личерам',
    'downloads': 'по скачиваниям',
    'register': 'по дате добавления',
    'desc': 'по убыванию',
    'asc': 'по возрастанию'
}
