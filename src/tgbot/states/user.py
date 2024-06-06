from aiogram.fsm.state import State, StatesGroup


class LoginFSM(StatesGroup):
    send_username = State()
    send_password = State()
    send_captcha = State()
    submit = State()


class TorrentFSM(StatesGroup):
    send_torrent_name = State()
    search_settings_page = State()
    watch_results_page_card = State()
    watch_results_page_list = State()
    display_mode_page = State()
    order_page = State()
    sort_page = State()
    category_page = State()
    choose_torrent = State()


class StatusFSM(StatesGroup):
    status = State()


class HelpFSM(StatesGroup):
    help = State()
