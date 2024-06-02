import redis

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from tgbot.filters.login import PasswordFilter, UsernameFilter
from tgbot.lexicon.lexicon import LEXICON
from tgbot.services.text_service import (get_settings_text,
                                         get_torrent_info_text,
                                         get_user_info_text)
from tgbot.settings.settings import Settings
from tgbot.states.user import (LoginFSM, SettingsFSM,
                               TorrentFSM, StatusFSM, HelpFSM)
from tgbot.keyboards import keyboards
from tgbot.config import load_config

from rutracker_api.exceptions import AuthorizationException
from rutracker_api import RutrackerApi
from utils.general_logging import get_logger, setup_logger

config = load_config("bot.ini")
r = redis.Redis(**config.redis.__dict__)
api = RutrackerApi(config.proxy.proxy)
settings = Settings()

setup_logger()
logger = get_logger(__name__)

user_router = Router()


@user_router.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message, state: FSMContext):
    await message.answer(LEXICON['/start'])
    current_state = await state.get_state()
    logger.debug(f'{current_state=}')


@user_router.message(Command(commands='help'))
async def process_help_command(message: Message, state: FSMContext):
    await message.answer(LEXICON['/help'])
    await state.set_state(HelpFSM.help)
    current_state = await state.get_state()
    logger.debug(f'{current_state=}')


@user_router.message(Command(commands='status'))
async def process_status_command(message: Message, state: FSMContext):
    if api.page_provider.authorized:
        user_info = api.status()
        text = get_user_info_text(user_info)
        await message.answer(text)
    else:
        await message.answer(get_user_info_text())
    await state.set_state(StatusFSM.status)
    current_state = await state.get_state()
    logger.debug(f'{current_state=}')


@user_router.message(Command(commands='login'))
async def process_login_command(message: Message, state: FSMContext):
    await message.answer("Пришлите логин")
    await state.set_state(LoginFSM.send_username)
    current_state = await state.get_state()
    logger.debug(f'{current_state=}')


@user_router.message(Command(commands='get_torrent'))
async def process_get_torrent_command(message: Message, state: FSMContext):
    if api.page_provider.authorized:
        await message.answer("Пришлите название искомого контента")
    else:
        await message.answer("Вы не авторизованы /login")
    await state.set_state(TorrentFSM.send_torrent_name)
    current_state = await state.get_state()
    logger.debug(f'{current_state=}')


@user_router.message(Command(commands='settings'))
async def process_settings_command(message: Message, state: FSMContext):
    settings_text_data = {
        'display_mode': settings.display_mode,
        'sort': settings.sort,
        'order': settings.order
    }
    await state.update_data(settings_text_data=settings_text_data)
    await message.answer(
        text=get_settings_text(settings_text_data),
        reply_markup=keyboards.create_settings_main_kb())
    await state.set_state(SettingsFSM.main)
    current_state = await state.get_state()
    logger.debug(f'{current_state=}')


@user_router.callback_query(StateFilter(SettingsFSM),
                            F.data == 'return')
async def process_return_settings_main(callback: CallbackQuery,
                                       state: FSMContext):
    state_data = await state.get_data()
    settings_text_data = state_data.get('settings_text_data')
    await callback.message.edit_text(
        text=get_settings_text(settings_text_data),
        reply_markup=keyboards.create_settings_main_kb())
    await state.set_state(SettingsFSM.main)


@user_router.callback_query(F.data == 'display_mode',
                            StateFilter(SettingsFSM.main))
async def process_display_mode_press(callback: CallbackQuery,
                                     state: FSMContext):
    await callback.message.edit_text("Выберите способ отображения торрентов:",
                                     reply_markup=keyboards.create_settings_display_mode_kb())
    await state.set_state(SettingsFSM.display_mode)


@user_router.callback_query(StateFilter(SettingsFSM.main),
                            F.data == "sort")
async def process_sort_main(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите способ сортировки:",
                                     reply_markup=keyboards.create_settings_sort_type_kb())
    await state.set_state(SettingsFSM.sort)


@user_router.callback_query(StateFilter(SettingsFSM.main),
                            F.data == "order")
async def process_order_main(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите порядок сортировки:",
                                     reply_markup=keyboards.create_settings_sort_order_kb())
    await state.set_state(SettingsFSM.order)


@user_router.callback_query(StateFilter(SettingsFSM.display_mode),
                            F.data.in_(["display_list", "display_card"]))
async def update_display_settings(callback: CallbackQuery,
                                  state: FSMContext):
    if callback.data == 'display_list':
        settings.display_mode = 'list'
    else:
        settings.display_mode = 'card'
    await callback.answer('Успешно')


# Общая функция для обработки нажатий на кнопки сортировки
async def update_sort_settings(callback: CallbackQuery, state: FSMContext, sort: str = None, order: str = None):
    if sort:
        settings.sort = sort
    if order:
        settings.order = order
    await callback.answer('Успешно')


# Обработчик для кнопок выбора типа сортировки
@user_router.callback_query(StateFilter(SettingsFSM.sort), F.data.in_(['sort_seeds', 'sort_leeches', 'sort_downloads', 'sort_registered']))
async def process_sort_type_selection(callback: CallbackQuery, state: FSMContext):
    sort_types = {
        'sort_seeds': 'seeds',
        'sort_leeches': 'leeches',
        'sort_downloads': 'downloads',
        'sort_registered': 'registered'
    }
    sort_type = sort_types[callback.data]
    await update_sort_settings(callback, state, sort=sort_type)

# Обработчик для кнопок выбора порядка сортировки
@user_router.callback_query(StateFilter(SettingsFSM.order), F.data.in_(['order_desc', 'order_asc']))
async def process_sort_order_selection(callback: CallbackQuery, state: FSMContext):
    orders = {
        'order_desc': 'desc',
        'order_asc': 'asc'
    }
    order = orders[callback.data]
    await update_sort_settings(callback, state, order=order)


@user_router.message(StateFilter(LoginFSM.send_username), UsernameFilter())
async def process_username_sent(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.answer("Пришлите пароль")
    await state.set_state(LoginFSM.send_password)


@user_router.message(StateFilter(LoginFSM.send_password), PasswordFilter())
async def process_password_sent(message: Message, state: FSMContext):
    # state_data = await state.get_data()
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
async def process_captcha_sent(message: Message, state: FSMContext):
    captcha = message.text
    await state.update_data(captcha=captcha)
    await message.answer(
            text='Подтвердите вход',
            reply_markup=keyboards.create_submit_kb()
        )
    await state.set_state(LoginFSM.submit)


@user_router.callback_query(StateFilter(LoginFSM.submit))
async def process_submit_button(callback: CallbackQuery, state: FSMContext):
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
        await state.clear()
    finally:
        await state.set_state(default_state)


@user_router.message(StateFilter(TorrentFSM.send_torrent_name))
async def process_torrent_request(message: Message, state: FSMContext):
    torrents_info = api.search(
        message.text,
        sort=settings.sort,
        order=settings.order,
    )
    await state.update_data(torrents_info=torrents_info, current_page=1)
    torrents = torrents_info.get('result')
    if torrents_info:
        total_pages = torrents_info.get('total_pages')
        text = get_torrent_info_text(torrents[0])
        if settings.display_mode == 'card':
            await message.answer(
                text=text,
                reply_markup=keyboards.create_torrents_card_kb(
                    'backward',
                    f'1/{total_pages}',
                    'forward'
                )
            )
        else:
            await message.answer(
                text='Результаты поиска',
                reply_markup=keyboards.create_torrents_list_kb(
                    torrents, torrents_info['page'], total_pages, message.text
                )
            )
    else:
        await message.answer("Не нашел, что-то не так.")
    await state.set_state(TorrentFSM.choose_torrent)


@user_router.callback_query(StateFilter(TorrentFSM.choose_torrent),
                            F.data == 'forward')
async def process_forward_press(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()

    torrents_info = state_data.get('torrents_info')
    torrents = torrents_info.get('result')
    total_pages = torrents_info.get('total_pages')

    prev_page = state_data.get('current_page')
    if prev_page >= 0 and prev_page < total_pages:
        current_page = prev_page + 1
        await state.update_data(current_page=current_page)
        await callback.message.edit_text(
            text=get_torrent_info_text(torrents[current_page - 1]),
            reply_markup=keyboards.create_torrents_card(
                'backward',
                f'{current_page}/{total_pages}',
                'forward'
            )
        )
    else:
        await callback.answer()


@user_router.callback_query(StateFilter(TorrentFSM.choose_torrent),
                            F.data == 'backward')
async def process_backward_press(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()

    torrents_info = state_data.get('torrents_info')
    torrents = torrents_info.get('result')
    total_pages = torrents_info.get('total_pages')

    prev_page = state_data.get('current_page')
    if prev_page > 1 and prev_page <= total_pages:
        current_page = prev_page - 1
        await state.update_data(current_page=current_page)
        await callback.message.edit_text(
            text=get_torrent_info_text(torrents[current_page - 1]),
            reply_markup=keyboards.create_torrents_card(
                'backward',
                f'{current_page}/{total_pages}',
                'forward'
            )
        )
    else:
        await callback.answer()


@user_router.callback_query(StateFilter(TorrentFSM.choose_torrent),
                            F.data == 'cancel')
async def process_cancel_press(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()


@user_router.callback_query(StateFilter(TorrentFSM.choose_torrent),
                            F.data == 'download')
async def process_download_press(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    current_page = state_data.get('current_page')
    torrents_info = state_data.get('torrents_info')
    torrents = torrents_info.get('result')
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
