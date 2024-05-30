from .utils import get_captcha, is_autorized, is_captcha, save_captcha
from .enums import Url
from .exceptions import (
    AuthorizationException,
    NotAuthorizedException,
    RedirectException,
    ServerException,
)
from requests import Session


class PageProvider:
    """This class provides access to the Rutracker forum"""
    def __init__(self, session: Session):
        self.session = session
        self.authorized = False
        self.base_url = 'https://rutracker.org/forum/'

    def login(self, username, password, proxy: str | None = None):
        login_url = f"{self.base_url}login.php"

        # Заголовки, чтобы имитировать браузер
        headers = {
            'User-Agent': Url.USER_AGENT.value
        }

        # Параметры логина
        payload = {
            'login_username': username,
            'login_password': password,
            'login': 'Вход'
        }

        # Отправка POST-запроса для логина
        response = self.session.post(login_url, data=payload, headers=headers)

        # Проверка на наличие капчи
        captcha_tag = is_captcha(response)
        if captcha_tag:
            save_captcha(self.session, captcha_tag)
            captcha_img = get_captcha()
            return captcha_img
        # Проверка успешной авторизации
        if is_autorized(response, username):
            self.authorized = True
            return 'success'

    def search(self, query, sort, order, page):
        if not self.authorized:
            raise NotAuthorizedException

        search_url = f"{self.base_url}tracker.php"

        # Заголовки, чтобы имитировать браузер
        headers = {
            'User-Agent': Url.USER_AGENT.value
        }

        params = {
            'nm': query,
            's': sort,
            'o': order,
            'start': (page - 1) * 50
        }

        response = self.session.get(search_url, params=params, headers=headers)
        if response.status_code != 200:
            raise ServerException(f"Ошибка выполнения поиска: {response.status_code}")

        return response.text

    def torrent_file(self, topic_id):
        if not self.authorized:
            raise NotAuthorizedException

        download_url = f"{Url.DOWNLOAD_URL.value}?t={topic_id}"

        # Заголовки, чтобы имитировать браузер
        headers = {
            'User-Agent': Url.USER_AGENT.value
        }

        response = self.session.get(download_url, headers=headers)
        if response.status_code != 200:
            raise ServerException(f"Ошибка загрузки торрент-файла: {response.status_code}")

        return response.content
