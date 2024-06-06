from typing import Union
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from rutracker_api.main import RutrackerApi

from tgbot.settings.settings import DisplaySetting, SearchSetting
from tgbot.keyboards import keyboards
from tgbot.services.text_service import (generate_search_results_summary,
                                         get_torrent_info_text)
from tgbot.states.user import TorrentFSM


async def update_watch_results_page(callback: CallbackQuery,
                                    state: FSMContext,
                                    current_page: int,
                                    total_pages: int,
                                    display_mode: str,
                                    torrents_in_page: int | None = 10):
    """Возвращает пользователю страницу с результатами поиска"""
    state_data = await state.get_data()
    torrents = state_data.get('torrents')
    if display_mode == 'card':
        await callback.message.edit_text(
            text=get_torrent_info_text(torrents[current_page - 1]),
            reply_markup=keyboards.create_torrent_card_navigation_kb(
                'backward',
                f'{current_page}/{total_pages}',
                'forward'
            )
        )
        await state.update_data(
            card_current_page=current_page, card_total_pages=total_pages
            )
        await state.set_state(TorrentFSM.watch_results_card_page)
    elif display_mode == 'list':
        await callback.message.edit_text(
            text='Результаты поиска',
            reply_markup=keyboards.create_torrent_list_navigation_kb(
                torrents=torrents, current_page=current_page,
                torrents_in_page=torrents_in_page,
                total_pages=total_pages, search_term=state_data.get('query')
            )
        )
        await state.update_data(
            list_current_page=current_page, list_total_pages=total_pages,
            )
        await state.set_state(TorrentFSM.watch_results_list_page)


async def update_search_settings_page(update: Union[Message, CallbackQuery],
                                      search_results_info: dict,
                                      search_params: dict,
                                      display_params: dict,
                                      global_current_page: int,
                                      global_total_pages: int) -> None:
    """"Возвращает пользователю страницу настроек поиска"""
    if isinstance(update, Message):
        await update.answer(
            text=generate_search_results_summary(search_results_info),
            reply_markup=keyboards.create_search_settings_kb(
                search_params, display_params,
                global_current_page, global_total_pages
            )
        )
    else:
        await update.message.edit_text(
            text=generate_search_results_summary(search_results_info),
            reply_markup=keyboards.create_search_settings_kb(
                search_params, display_params,
                global_current_page, global_total_pages
            )
        )


async def handle_search_settings_change(
        callback: CallbackQuery, state: FSMContext,
        search_settings: SearchSetting) -> bool:
    """Изменяет настройки поиска"""

    current_state = await state.get_state()
    is_search_settings_changed = False

    if current_state == 'TorrentFSM:sort_page' and callback.data != 'return':
        sort_types = {
            'sort_seeds': 'seeds',
            'sort_leeches': 'leeches',
            'sort_downloads': 'downloads',
            'sort_registered': 'registered'
        }
        await update_sort_settings(callback, state,
                                   search_settings,
                                   sort=sort_types[callback.data])
        is_search_settings_changed = True

    elif current_state == 'TorrentFSM:order_page' and callback.data != 'return':
        orders = {
            'order_desc': 'desc',
            'order_asc': 'asc'
        }
        await update_sort_settings(callback, state,
                                   search_settings,
                                   order=orders[callback.data])
        is_search_settings_changed = True

    elif current_state == 'TorrentFSM:category_page' and callback.data != 'return':
        is_search_settings_changed = True
        pass  # Обработка изменений категорий, если потребуется

    return is_search_settings_changed


async def handle_display_settings_change(
        callback: CallbackQuery, state: FSMContext,
        display_settings: DisplaySetting) -> bool:
    """Изменяет настройки отображения результатов поиска"""

    current_state = await state.get_state()
    is_display_settings_changed = False

    if current_state == 'TorrentFSM:display_mode_page' and callback.data != 'return':
        if callback.data == 'display_list':
            display_settings.display_mode = 'list'
            is_display_settings_changed = True
        if callback.data == 'display_card':
            display_settings.display_mode = 'card'
            is_display_settings_changed = True
    return is_display_settings_changed


async def update_sort_settings(callback: CallbackQuery, state: FSMContext,
                               search_settings: SearchSetting,
                               sort: str = None, order: str = None):
    """Изменяет способ и порядок сортировки"""
    if sort:
        search_settings.sort = sort
    if order:
        search_settings.order = order


async def update_search_request(query: str, search_settings: SearchSetting,
                                api: RutrackerApi, page: int = 1) -> tuple:
    """Делает поисковый запрос и возвращает результат"""
    search_results_info = api.search(
        query,
        sort=search_settings.sort,
        order=search_settings.order,
        page=page
    )
    return search_results_info


async def handle_pagination_button_common(
        callback: CallbackQuery,
        state: FSMContext,
        selected_page: int | None = None,
        is_forward: bool | None = None,
        search_settings: SearchSetting | None = None,
        api: RutrackerApi | None = None):
    """Универсальная функция для обработки нажатия кнопок пагинации"""
    current_state = await state.get_state()

    pagination_configs = {
        'TorrentFSM:watch_results_card_page': (
            'card_current_page', 'card_total_pages', 'card'
            ),
        'TorrentFSM:watch_results_list_page': (
            'list_current_page', 'list_total_pages', 'list'
            ),
        'TorrentFSM:search_settings_page': (
            'global_current_page', 'global_total_pages', None
            )
    }

    if current_state in pagination_configs:
        current_page_key, total_pages_key, display_mode = pagination_configs[
            current_state
            ]
        state_data = await state.get_data()
        prev_page = state_data.get(current_page_key)
        total_pages = state_data.get(total_pages_key)

        if selected_page:
            new_page = selected_page
        else:
            new_page = prev_page + 1 if is_forward else prev_page - 1
        condition = 0 < new_page <= total_pages

        if not condition:
            await callback.answer()
            return

        if current_page_key in ['card_current_page', 'list_current_page']:
            await update_watch_results_page(callback, state, new_page,
                                            total_pages, display_mode)
        elif current_page_key == 'global_current_page':
            query = state_data['query']
            search_results_info = await update_search_request(query,
                                                              search_settings,
                                                              api,
                                                              page=new_page)
            torrents = search_results_info.get('result')
            search_params = state_data.get('search_params')
            display_params = state_data.get('display_params')
            await state.update_data(search_results_info=search_results_info,
                                    torrents=torrents,
                                    global_current_page=new_page)
            await update_search_settings_page(callback, search_results_info,
                                              search_params, display_params,
                                              new_page, total_pages)


async def handle_enter_pages_menu_common(callback: CallbackQuery,
                                         state: FSMContext) -> int:
    """Универсальная функция для обработки
    кнопки перехода в меню выбора текущей страницы"""
    current_state = await state.get_state()
    state_data = await state.get_data()

    if current_state == 'TorrentFSM:watch_results_card_page':
        total_pages = state_data.get('card_total_pages')
    elif current_state == 'TorrentFSM:watch_results_list_page':
        total_pages = state_data.get('list_total_pages')
    elif current_state == 'TorrentFSM:search_settings_page':
        total_pages = state_data.get('global_total_pages')

    await callback.message.edit_text(
        text='Выберите номер страницы',
        reply_markup=keyboards.create_enter_pages_page_kb(total_pages)
    )
