from typing import Union
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from rutracker_api.main import RutrackerApi

from tgbot.settings.settings import DisplaySetting, SearchSetting
from tgbot.keyboards import keyboards
from tgbot.services.text_service import (generate_search_results_summary,
                                         get_torrent_info_text)
from tgbot.states.user import TorrentFSM
from tgbot.services import mappings


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
            reply_markup=keyboards.create_watch_results_kb(
                current_page=current_page,
                total_pages=total_pages,
                is_card=True
            )
        )
        await state.update_data(
            watch_results_current_page_card=current_page,
            watch_results_total_pages_card=total_pages
            )
        await state.set_state(TorrentFSM.watch_results_page_card)
    elif display_mode == 'list':
        await callback.message.edit_text(
            text='Результаты поиска',
            reply_markup=keyboards.create_watch_results_kb(
                torrents=torrents,
                current_page=current_page,
                torrents_in_page=torrents_in_page,
                total_pages=total_pages,
                search_term=state_data.get('query'),
                is_list=True
            )
        )
        await state.update_data(
            watch_results_current_page_list=current_page,
            watch_results_total_pages_list=total_pages,
            )
        await state.set_state(TorrentFSM.watch_results_page_list)


async def update_search_settings_page(
        update: Union[Message, CallbackQuery],
        search_results_info: dict,
        search_params: dict,
        display_params: dict,
        search_settings_current_page: int,
        search_settings_total_pages: int) -> None:
    """"Возвращает пользователю страницу настроек поиска"""
    if isinstance(update, Message):
        await update.answer(
            text=generate_search_results_summary(search_results_info),
            reply_markup=keyboards.create_search_settings_kb(
                search_params, display_params,
                search_settings_current_page,
                search_settings_total_pages
            )
        )
    else:
        await update.message.edit_text(
            text=generate_search_results_summary(search_results_info),
            reply_markup=keyboards.create_search_settings_kb(
                search_params, display_params,
                search_settings_current_page,
                search_settings_total_pages
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
    state_data = await state.get_data()

    prev_page = await get_page(state, is_current=True)
    total_pages = await get_page(state, is_total=True)

    if selected_page:
        new_page = selected_page
    else:
        new_page = prev_page + 1 if is_forward else prev_page - 1
    condition = 0 < new_page <= total_pages

    if not condition:
        await callback.answer()
        return

    if current_state in ['TorrentFSM:watch_results_page_card',
                         'TorrentFSM:watch_results_page_list']:
        display_mode = current_state.split(':')[1].split('_')[-1]
        await update_watch_results_page(callback, state, new_page,
                                        total_pages, display_mode)
    elif current_state == 'TorrentFSM:search_settings_page':
        query = state_data['query']
        search_results_info = await update_search_request(
            query, search_settings, api, page=new_page)
        torrents = search_results_info.get('result')
        search_params = state_data.get('search_params')
        display_params = state_data.get('display_params')
        await state.update_data(search_results_info=search_results_info,
                                torrents=torrents,
                                search_settings_current_page=new_page)
        await update_search_settings_page(callback, search_results_info,
                                          search_params, display_params,
                                          new_page, total_pages)


async def handle_enter_pages_menu_common(callback: CallbackQuery,
                                         state: FSMContext) -> int:
    """Универсальная функция для обработки
    кнопки перехода в меню выбора текущей страницы"""
    total_pages = await get_page(state, is_total=True)

    await callback.message.edit_text(
        text='Выберите номер страницы',
        reply_markup=keyboards.create_enter_pages_page_kb(total_pages)
    )


async def get_page(state,
                   is_current: bool | None = None,
                   is_total: bool | None = None
                   ) -> int:
    """"Возвращает номер текущей или кол-во всех страницочень приятная тат"""
    current_state = await state.get_state()
    state_data = await state.get_data()

    # Извлечение второй части состояния (например, 'watch_results_page_card')
    state_key = current_state.split(':')[1]

    # Получение соответствующей переменной из маппинга
    if is_current:
        page_var = mappings.state_current_page_mappings.get(state_key)
    elif is_total:
        page_var = mappings.state_total_page_mappings.get(state_key)

    if page_var is None:
        raise ValueError(f"Unknown state: {current_state}")

    return state_data.get(page_var)
