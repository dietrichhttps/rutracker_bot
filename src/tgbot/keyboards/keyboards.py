from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_submit_kb() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(
            text="Отправить",
            callback_data="submit"
        )
    )
    return kb_builder.as_markup()


def create_torrents_kb(results: dict) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []
    torrents = results.get('result')

    for torrent in torrents:
        text = (
            f"Название: {torrent['title'][:20]}"
            f"Автор: {torrent['author']}\n"
            f"Категория: {torrent['category']}\n"
            f"Сиды: {torrent['seeds']}\n"
            f"Личи: {torrent['leeches']}\n"
            f"Скачиваний: {torrent['downloads']}"
        )
        torrent_info_btn = InlineKeyboardButton(
            text=text,
            callback_data=f'torrent_{torrent['topic_id']}'
        )
        dwnld_btn = InlineKeyboardButton(
            text='Скачать',
            callback_data=torrent['url'])
        buttons.append(torrent_info_btn)
    kb_builder.row(*buttons, width=1)
    return kb_builder.as_markup()
