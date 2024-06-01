import redis

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from tgbot.filters.login import PasswordFilter, UsernameFilter
from tgbot.lexicon.lexicon import LEXICON
from tgbot.services.text_service import (get_torrent_info_text,
                                         get_user_info_text)
from tgbot.states.user import LoginFSM, TorrentFSM
from tgbot.keyboards.keyboards import (create_pagination_keyboard,
                                       create_submit_kb)
from tgbot.config import load_config

from rutracker_api.exceptions import AuthorizationException
from rutracker_api import RutrackerApi

config = load_config("bot.ini")
r = redis.Redis(**config.redis.__dict__)
api = RutrackerApi(config.proxy.proxy)

user_router = Router()


@user_router.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(LEXICON['/start'])


@user_router.message(Command(commands='help'), StateFilter(default_state))
async def process_help_command(message: Message):
    await message.answer(LEXICON['/help'])


@user_router.message(Command(commands='status'), StateFilter(default_state))
async def process_status_command(message: Message):
    if api.page_provider.authorized:
        user_info = api.status()
        text = get_user_info_text(user_info)
        await message.answer(text)
    else:
        await message.answer(get_user_info_text())


@user_router.message(Command(commands='login'))
async def process_login_command(message: Message, state: FSMContext):
    # captcha = api.search_captcha()
    # if captcha:
    #     await state.update_data(captcha=captcha)

    await message.answer("Пришлите логин")
    await state.set_state(LoginFSM.send_username)


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
            reply_markup=create_submit_kb()
        )
    await state.update_data(password=message.text)


@user_router.message(StateFilter(LoginFSM.send_captcha))
async def process_captcha_sent(message: Message, state: FSMContext):
    captcha = message.text
    await state.update_data(captcha=captcha)
    await message.answer(
            text='Подтвердите вход',
            reply_markup=create_submit_kb()
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


@user_router.message(Command(commands='get_torrent'),
                     StateFilter(default_state))
async def process_get_torrent_command(message: Message, state: FSMContext):
    if api.page_provider.authorized:
        await message.answer("Пришлите название искомого контента")
        await state.set_state(TorrentFSM.send_torrent_name)
    else:
        await message.answer("Вы не авторизованы /login")


@user_router.message(StateFilter(TorrentFSM.send_torrent_name))
async def process_torrent_request(message: Message, state: FSMContext):
    torrents_info = api.search(message.text)
    await state.update_data(torrents_info=torrents_info, current_page=1)
    torrents = torrents_info.get('result')
    if torrents_info:
        total_pages = torrents_info.get('total_pages')
        text = get_torrent_info_text(torrents[0])
        await message.answer(
            text=text,
            reply_markup=create_pagination_keyboard(
                'backward',
                f'1/{total_pages}',
                'forward'
            )
        )
        await state.set_state(TorrentFSM.choose_torrent)
    else:
        await message.answer("Не нашел, что-то не так.")


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
            reply_markup=create_pagination_keyboard(
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
            reply_markup=create_pagination_keyboard(
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
