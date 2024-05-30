from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
import redis

from rutracker_api.exceptions import AuthorizationException
from src.tgbot.states.user import LoginFSM, TorrentFSM
from src.tgbot.keyboards.keyboards import create_submit_kb, create_torrents_kb

from src.rutracker_api import RutrackerApi
from tgbot.config import load_config

config = load_config("/home/aliceglass/Study/developing/tg_bots/my_projects/rutracker_bot/bot.ini")
r = redis.Redis(**config.redis.__dict__)
api = RutrackerApi(config.proxy.proxy)

user_router = Router()

@user_router.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer("Hello, user!")


@user_router.message(Command(commands='login'), StateFilter(default_state))
async def process_login_command(message: Message, state: FSMContext):
    await message.answer("Пришлите логин")
    await state.set_state(LoginFSM.send_username)


@user_router.message(StateFilter(LoginFSM.send_username))
async def process_username_sent(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.answer("Пришлите пароль")
    await state.set_state(LoginFSM.send_password)


@user_router.message(StateFilter(LoginFSM.send_password))
async def process_password_sent(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    await state.set_state(LoginFSM.submit)
    await message.answer(
        text='Подтвердите вход',
        reply_markup=create_submit_kb()
    )


@user_router.callback_query(StateFilter(LoginFSM.submit))
async def process_sumbit_button(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    username, password = state_data.get('username'), state_data.get('password')
    try:
        login_res = api.login(username, password)
        if login_res == 'success':
            await callback.answer('Вы успешно авторизовались!')
            await callback.answer()
        if isinstance(login_res, bytes):
            await callback.message.answer('Введите капчу')
            await callback.message.answer_photo(login_res)
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
        await message.answer("Вы не авторизованы")


@user_router.message(StateFilter(TorrentFSM.send_torrent_name))
async def process_torrent_request(message: Message, state: FSMContext):
    results = api.search(message.text)
    if results:
        await message.answer(
            text='Выберите торренты',
            reply_markup=create_torrents_kb(results)
        )
        await state.set_state(TorrentFSM.choose_torrent)
    else:
        await message.answer("Не нашел, что-то не так.")