from aiogram import Bot
from aiogram.types import (InlineKeyboardMarkup,
                           InlineKeyboardButton, BotCommand)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.lexicon.lexicon import (LEXICON, LEXICON_COMMANDS,
                                   LEXICON_SEARCH_SETTINGS)
from tgbot.services.text_service import find_snippet_from_search_term


def create_submit_kb() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(
            text="Отправить",
            callback_data="submit"
        )
    )
    return kb_builder.as_markup()


def create_search_settings_kb(search_params: dict,
                              display_params: dict,
                              current_page: int,
                              total_pages: int) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    sort_btn = InlineKeyboardButton(
        text=LEXICON_SEARCH_SETTINGS[search_params['sort']],
        callback_data='sort'
    )
    order_btn = InlineKeyboardButton(
        text=LEXICON_SEARCH_SETTINGS[search_params['order']],
        callback_data='order'
    )
    category_btn = InlineKeyboardButton(
        text=search_params['category'],
        callback_data='category'
    )
    display_mode_btn = InlineKeyboardButton(
        text=LEXICON_SEARCH_SETTINGS[display_params['display_mode']],
        callback_data='display_mode'
    )
    current_page_btn = InlineKeyboardButton(
        text=f'{current_page}/{total_pages}',
        callback_data='select_current_page'
    )
    whatch_results_btn = InlineKeyboardButton(
        text='Посмотреть результаты',
        callback_data='watch_results'
    )
    kb_builder.row(sort_btn, order_btn, width=2)
    kb_builder.row(category_btn, display_mode_btn, width=2)
    kb_builder.row(current_page_btn, width=1)
    kb_builder.row(whatch_results_btn, width=1)
    return kb_builder.as_markup()


# Функция, генерирующая клавиатуру для страницы книги
def create_torrent_card_navigation_kb(*buttons: str) -> InlineKeyboardMarkup:
    # Инициализируем билдер
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(
            text='Отмена',
            callback_data='cancel'
        ),
        InlineKeyboardButton(
            text='Назад',
            callback_data='return'
            ),
        width=2
        )
    kb_builder.row(*[InlineKeyboardButton(
        text=LEXICON[button] if button in LEXICON else button,
        callback_data=button) for button in buttons])
    kb_builder.row(InlineKeyboardButton(text='Скачать',
                                        callback_data='download'))
    return kb_builder.as_markup()


def create_torrent_list_navigation_kb(
        torrents: list, current_page: int,
        torrents_in_page: int,
        total_pages: int, search_term: str) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    torrent_buttons = []
    start_index = (current_page - 1) * torrents_in_page
    end_index = start_index + torrents_in_page
    for torrent in torrents[start_index:end_index]:
        button = InlineKeyboardButton(
            text=find_snippet_from_search_term(
                torrent['title'],
                search_term,
                max_length=50
            ),
            callback_data=f"torrent_{torrent['topic_id']}")
        torrent_buttons.append(button)
    kb_builder.row(*torrent_buttons, width=1)

    navigation_buttons = [
        InlineKeyboardButton(text="<<", callback_data="backward"),
        InlineKeyboardButton(text=f'{current_page}/{total_pages}',
                             callback_data='pages'),
        InlineKeyboardButton(text=">>", callback_data="forward"),
    ]
    kb_builder.row(*navigation_buttons, width=3)
    kb_builder.row(
        InlineKeyboardButton(
            text='Отмена', callback_data='cancel'
        ),
        InlineKeyboardButton(
            text='Назад', callback_data='return'
        )
    )

    return kb_builder.as_markup()


def create_display_mode_settings_kb() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    kb_builder.row(
        InlineKeyboardButton(
            text="Карточками", callback_data="display_card"
        ),
        InlineKeyboardButton(
            text="Списком", callback_data="display_list"
        ),
        width=2
    )
    kb_builder.row(
        InlineKeyboardButton(
            text='Назад', callback_data='return'
        )
    )
    return kb_builder.as_markup()


def create_sort_order_settings_kb() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    kb_builder.row(
        InlineKeyboardButton(
            text="По убыванию", callback_data="order_desc"
        ),
        InlineKeyboardButton(
            text="По возрастанию", callback_data="order_asc"
        ),
        width=2
    )
    kb_builder.row(
        InlineKeyboardButton(
            text='Назад', callback_data='return'
        )
    )
    return kb_builder.as_markup()


def create_sort_type_settings_kb() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    kb_builder.row(
        InlineKeyboardButton(
            text="По cидам", callback_data="sort_seeds"
        ),
        InlineKeyboardButton(
            text="По личерам", callback_data="sort_leeches"
        ),
        InlineKeyboardButton(
            text="По скачиваниям", callback_data="sort_downloads"
        ),
        InlineKeyboardButton(
            text="По дате добавления", callback_data="sort_registered"
        ),
        InlineKeyboardButton(
            text='Назад', callback_data='return'
        ),
        width=1
    )
    return kb_builder.as_markup()


# Функция для настройки кнопки Menu бота
async def set_main_menu(bot: Bot):
    main_menu_commands = [BotCommand(
        command=command,
        description=description
    ) for command, description in LEXICON_COMMANDS.items()]
    await bot.set_my_commands(main_menu_commands)
