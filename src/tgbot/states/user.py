from aiogram.fsm.state import State, StatesGroup


class LoginFSM(StatesGroup):
    send_username = State()
    send_password = State()
    send_captcha = State()
    submit = State()


class TorrentFSM(StatesGroup):
    send_torrent_name = State()
    choose_torrent = State()


class SettingsFSM(StatesGroup):
    main = State()
    display_mode = State()
    order = State()
    sort = State()


class StatusFSM(StatesGroup):
    status = State()


class HelpFSM(StatesGroup):
    help = State()
