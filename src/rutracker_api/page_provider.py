from .utils import get_captcha, get_profile_url, is_autorized, search_captcha
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
        self.headers = {
            'User-Agent': Url.USER_AGENT.value
        }
        self.profile_url = None

    def search_captcha(self):
        captcha_img_url = search_captcha(self.session.get(Url.LOGIN_URL.value, headers=self.headers))
        if captcha_img_url:
            return get_captcha(self.session, captcha_img_url)

    def login(self, username, password, captcha=None):
        login_url = Url.LOGIN_URL.value

        # Параметры логина
        payload = {
            'login_username': username,
            'login_password': password,
            'login_captcha': captcha,
            'login': 'Вход'
        }

        # Отправка POST-запроса для логина
        response = self.session.post(login_url, data=payload, headers=self.headers)

        # Проверка успешной авторизации
        if is_autorized(response, username):
            self.authorized = True
            self.profile_url = get_profile_url(response)
            return 'success'

    def search(self, query, sort, order, page):
        if not self.authorized:
            raise NotAuthorizedException

        search_url = f"{self.base_url}tracker.php"

        params = {
            'nm': query,
            's': sort,
            'o': order,
            'start': (page - 1) * 50
        }

        response = self.session.get(search_url, params=params,
                                    headers=self.headers)
        if response.status_code != 200:
            raise ServerException(f"Ошибка выполнения поиска: {response.status_code}")

        return response.text

    def torrent_file(self, topic_id):
        if not self.authorized:
            raise NotAuthorizedException

        download_url = f"{Url.DOWNLOAD_URL.value}?t={topic_id}"

        response = self.session.get(download_url, headers=self.headers)
        if response.status_code != 200:
            raise ServerException(f"Ошибка загрузки торрент-файла: {response.status_code}")

        return response.content
