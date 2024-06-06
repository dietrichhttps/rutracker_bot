import redis

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from tgbot.filters.login import PasswordFilter, UsernameFilter
from tgbot.lexicon.lexicon import LEXICON
from tgbot.services.repository import (get_search_settings_callback_data,
                                       update_display_params,
                                       update_search_params)
from tgbot.services.text_service import get_user_info_text
from tgbot.settings.settings import DisplaySetting, SearchSetting
from tgbot.states.user import LoginFSM, TorrentFSM, StatusFSM, HelpFSM
from tgbot.keyboards import keyboards
from tgbot.config import load_config

from rutracker_api.exceptions import AuthorizationException
from rutracker_api import RutrackerApi
from tgbot.utils.utils import (handle_display_settings_change,
                               handle_enter_pages_menu_common,
                               handle_pagination_button_common,
                               handle_search_settings_change,
                               update_search_request,
                               update_search_settings_page,
                               update_watch_results_page)

from utils.general_logging import get_logger, setup_logger

config = load_config("bot.ini")
r = redis.Redis(**config.redis.__dict__)
api = RutrackerApi(config.proxy.proxy)
search_settings = SearchSetting()
display_settings = DisplaySetting()
search_settings_callback_data = get_search_settings_callback_data()

setup_logger()
logger = get_logger(__name__)

user_router = Router()


async def log_current_state(state):
    current_state = await state.get_state()
    logger.debug(f'{current_state=}')


@user_router.message(CommandStart(), StateFilter(default_state))
async def handle_start_command(message: Message, state: FSMContext):
    await message.answer(LEXICON['/start'])
    await log_current_state(state)


@user_router.message(Command(commands='help'))
async def handle_help_command(message: Message, state: FSMContext):
    await message.answer(LEXICON['/help'])
    await state.set_state(HelpFSM.help)
    await log_current_state(state)


@user_router.message(Command(commands='status'))
async def handle_status_command(message: Message, state: FSMContext):
    if api.page_provider.authorized:
        user_info = api.status()
        text = get_user_info_text(user_info)
        await message.answer(text)
    else:
        await message.answer(get_user_info_text())
    await state.set_state(StatusFSM.status)
    await log_current_state(state)


@user_router.message(Command(commands='login'))
async def handle_login_command(message: Message, state: FSMContext):
    await message.answer("Пришлите логин")
    await state.set_state(LoginFSM.send_username)
    await log_current_state(state)


@user_router.message(Command(commands='get_torrent'))
async def handle_get_torrent_command(message: Message, state: FSMContext):
    if api.page_provider.authorized:
        await message.answer("Пришлите название искомого контента")
    else:
        await message.answer("Вы не авторизованы /login")
    await state.set_state(TorrentFSM.send_torrent_name)
    await log_current_state(state)


@user_router.message(StateFilter(LoginFSM.send_username), UsernameFilter())
async def handle_username_input(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.answer("Пришлите пароль")
    await state.set_state(LoginFSM.send_password)


@user_router.message(StateFilter(LoginFSM.send_password))
async def handle_password_input(message: Message, state: FSMContext):
    captcha = api.search_captcha()
    await state.update_data(captcha=captcha)
    if captcha:
        await message.answer_photo(BufferedInputFile(captcha, 'captcha.jpg'),
                                   caption='Введите капчу')
        await state.set_state(LoginFSM.send_captcha)
    else:
        await state.set_state(LoginFSM.submit)
        await message.answer(
            text='Подтвердите вход',
            reply_markup=keyboards.create_submit_kb()
        )
    await state.update_data(password=message.text)


@user_router.message(StateFilter(LoginFSM.send_captcha))
async def handle_captcha_input(message: Message, state: FSMContext):
    captcha = message.text
    await state.update_data(captcha=captcha)
    await message.answer(
            text='Подтвердите вход',
            reply_markup=keyboards.create_submit_kb()
        )
    await state.set_state(LoginFSM.submit)


@user_router.callback_query(StateFilter(LoginFSM.submit), F.data == 'submit')
async def handle_submit_button(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    username, password = state_data.get('username'), state_data.get('password')
    captcha = state_data.get('captcha', None)
    try:
        login_res = api.login(username, password, captcha)
        if login_res == 'success':
            await callback.answer('Вы успешно авторизовались!')
            await callback.answer()
    except AuthorizationException:
        await callback.answer('Логин или пароль неверны')
    finally:
        await callback.message.delete()
        await state.clear()


@user_router.message(StateFilter(TorrentFSM.send_torrent_name))
async def handle_torrent_search_request(message: Message, state: FSMContext):
    query = message.text
    search_results_info = await update_search_request(
        query, search_settings, api
    )
    torrents = search_results_info['result']
    search_params = update_search_params(search_settings)
    display_params = update_display_params(display_settings)
    search_settings_current_page = search_results_info.get('page')
    search_settings_total_pages = search_results_info.get('total_pages')

    await update_search_settings_page(
        message, search_results_info, search_params, display_params,
        search_settings_current_page,
        search_settings_total_pages
    )
    await state.update_data(
        search_results_info=search_results_info,
        torrents=torrents,
        search_params=search_params,
        display_params=display_params,
        query=query,
        search_settings_current_page=search_settings_current_page,
        search_settings_total_pages=search_settings_total_pages,
    )
    await state.set_state(TorrentFSM.search_settings_page)
    await log_current_state(state)


@user_router.callback_query(F.data == 'display_mode',
                            StateFilter(TorrentFSM.search_settings_page))
async def handle_display_mode_button(callback: CallbackQuery,
                                     state: FSMContext):
    await callback.message.edit_text(
        "Выберите способ отображения торрентов:",
        reply_markup=keyboards.create_display_mode_settings_kb())
    await state.set_state(TorrentFSM.display_mode_page)


@user_router.callback_query(StateFilter(TorrentFSM.search_settings_page),
                            F.data == "sort")
async def handle_sort_button(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите способ сортировки:",
        reply_markup=keyboards.create_sort_type_settings_kb())
    await state.set_state(TorrentFSM.sort_page)


@user_router.callback_query(StateFilter(TorrentFSM.search_settings_page),
                            F.data == "order")
async def handle_order_button(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите порядок сортировки:",
        reply_markup=keyboards.create_sort_order_settings_kb()
        )
    await state.set_state(TorrentFSM.order_page)


@user_router.callback_query(StateFilter(TorrentFSM.search_settings_page),
                            F.data == 'watch_results')
async def handle_watch_results_button(callback: CallbackQuery,
                                      state: FSMContext):
    state_data = await state.get_data()
    torrents = state_data.get('torrents')
    if torrents:
        if display_settings.display_mode == 'card':
            current_page = 1
            total_pages = len(torrents)
            await update_watch_results_page(
                callback, state, current_page, total_pages, 'card')
        elif display_settings.display_mode == 'list':
            torrents_in_page = 10
            current_page = 1
            total_pages = int(len(torrents) / torrents_in_page)
            await update_watch_results_page(
                callback, state, current_page, total_pages, 'list')
    await log_current_state(state)


@user_router.callback_query(StateFilter(TorrentFSM), F.data == 'forward')
async def handle_forward_button(callback: CallbackQuery, state: FSMContext):
    await handle_pagination_button_common(callback, state, is_forward=True,
                                          search_settings=search_settings,
                                          api=api)


@user_router.callback_query(StateFilter(TorrentFSM), F.data == 'backward')
async def handle_backward_button(callback: CallbackQuery, state: FSMContext):
    await handle_pagination_button_common(callback, state, is_forward=False,
                                          search_settings=search_settings,
                                          api=api)


@user_router.callback_query(StateFilter(TorrentFSM),
                            F.data == 'pages')
async def handle_enter_pages_menu_button(callback: CallbackQuery,
                                         state: FSMContext):
    await handle_enter_pages_menu_common(callback, state)


@user_router.callback_query(StateFilter(TorrentFSM),
                            F.data.startswith('select_current_page'))
async def handle_select_current_page_button(callback: CallbackQuery,
                                            state: FSMContext):
    selected_page = int(callback.data.split(':')[1])
    await handle_pagination_button_common(
        callback, state, selected_page=selected_page,
        search_settings=search_settings,
        api=api
        )


@user_router.callback_query(
        StateFilter(TorrentFSM),
        F.data.in_(search_settings_callback_data + ['return']))
async def handle_return_search_settings_page(callback: CallbackQuery,
                                             state: FSMContext):
    is_search_settings_changed = await handle_search_settings_change(
        callback, state, search_settings)
    is_display_settings_changed = await handle_display_settings_change(
        callback, state, display_settings)

    state_data = await state.get_data()
    search_results_info = state_data.get('search_results_info')
    search_settings_current_page = state_data.get(
        'search_settings_current_page'
    )
    search_settings_total_pages = state_data.get(
        'search_settings_total_pages'
    )
    search_params = state_data.get('search_params')
    display_params = state_data.get('display_params')

    if is_search_settings_changed:
        search_results_info = await update_search_request(
            state_data['query'], search_settings, api
        )
        search_params = update_search_params(search_settings)
        search_settings_current_page = 1
        await state.update_data(
            search_results_info=search_results_info,
            search_params=search_params,
            torrents=search_results_info['result'],
            search_settings_current_page=search_settings_current_page
        )
        await callback.answer('Успешно')
    if is_display_settings_changed:
        display_params = update_display_params(display_settings)
        await state.update_data(display_params=display_params)
        await callback.answer('Успешно')

    await update_search_settings_page(
        callback, search_results_info, search_params,
        display_params,
        search_settings_current_page,
        search_settings_total_pages
    )
    await state.set_state(TorrentFSM.search_settings_page)
    log_current_state(state)


@user_router.callback_query(StateFilter(TorrentFSM.choose_torrent),
                            F.data == 'cancel')
async def handle_cancel_button(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()


@user_router.callback_query(StateFilter(TorrentFSM.watch_results_page_card),
                            F.data == 'download')
async def handle_download_button(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_page = state_data.get('watch_results_current_page_card')
    torrents = state_data.get('torrents')
    topic_id = torrents[current_page - 1].topic_id
    torrent_title = torrents[current_page - 1].title
    torrent_file = api.download(topic_id)

    if torrent_file:
        await callback.message.answer_document(
            BufferedInputFile(torrent_file,
                              filename=f'{torrent_title}.torrent')
        )
    else:
        await callback.message.answer("Не удалось скачать")
    await callback.answer()
    log_current_state(state)
