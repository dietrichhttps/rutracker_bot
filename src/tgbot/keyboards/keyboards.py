from aiogram import Bot
from aiogram.types import (InlineKeyboardMarkup,
                           InlineKeyboardButton, BotCommand)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.lexicon.lexicon import LEXICON, LEXICON_COMMANDS
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


# Функция, генерирующая клавиатуру для страницы книги
def create_torrents_card_kb(*buttons: str) -> InlineKeyboardMarkup:
    # Инициализируем билдер
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(
            text='Отмена',
            callback_data='cancel'
        ),
        InlineKeyboardButton(
            text='Скачать',
            callback_data='download'
            ),
        width=2
        )
    # Добавляем в билдер ряд с кнопками
    kb_builder.row(*[InlineKeyboardButton(
        text=LEXICON[button] if button in LEXICON else button,
        callback_data=button) for button in buttons])
    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()


def create_torrents_list_kb(
        torrents: list, page: int,
        total_pages: int, search_term: str) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    torrent_buttons = []
    start_index = (page - 1) * 5
    end_index = start_index + 5
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
        InlineKeyboardButton(text="<<", callback_data=f"page_{page - 1}"),
        InlineKeyboardButton(text=f'{page}/{total_pages}',
                             callback_data='pages'),
        InlineKeyboardButton(text=">>", callback_data=f"page_{page + 1}"),
    ]
    kb_builder.row(*navigation_buttons, width=3)

    return kb_builder.as_markup()


def create_settings_main_kb() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    kb_builder.row(
        InlineKeyboardButton(
            text="Способ отображения торрентов", callback_data="display_mode"
        ),
        InlineKeyboardButton(
            text="Способ сортировки", callback_data="sort"
        ),
        InlineKeyboardButton(
            text="Порядок сортировки", callback_data="order"
        ),
        width=1
    )
    return kb_builder.as_markup()


def create_settings_display_mode_kb() -> InlineKeyboardMarkup:
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


def create_settings_sort_order_kb() -> InlineKeyboardMarkup:
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


def create_settings_sort_type_kb() -> InlineKeyboardMarkup:
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
