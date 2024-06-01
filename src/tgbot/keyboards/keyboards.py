from aiogram import Bot
from aiogram.types import (InlineKeyboardMarkup,
                           InlineKeyboardButton, BotCommand)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.lexicon.lexicon import LEXICON, LEXICON_COMMANDS


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
def create_pagination_keyboard(*buttons: str) -> InlineKeyboardMarkup:
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


# Функция для настройки кнопки Menu бота
async def set_main_menu(bot: Bot):
    main_menu_commands = [BotCommand(
        command=command,
        description=description
    ) for command, description in LEXICON_COMMANDS.items()]
    await bot.set_my_commands(main_menu_commands)
