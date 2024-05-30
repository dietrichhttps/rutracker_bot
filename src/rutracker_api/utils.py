import urllib.parse

from bs4 import BeautifulSoup, NavigableString, Tag
from requests import Response, Session

from rutracker_api.enums import Url
from rutracker_api.exceptions import AuthorizationException
from utils.general_logging import get_logger

logger = get_logger(__name__)


def format_size(size_in_bytes):
    size_in_kilobytes = size_in_bytes / (1024)
    if size_in_kilobytes < 1024:
        return f"{round(size_in_kilobytes)} KB"
    size_in_megabytes = size_in_bytes / (1024 * 1024)
    if size_in_megabytes < 1024:
        return f"{round(size_in_megabytes, 1)} MB"
    size_in_gigabytes = size_in_bytes / (1024 * 1024 * 1024)
    if size_in_gigabytes < 1024:
        return f"{round(size_in_gigabytes, 2)} GB"
    size_in_terabytes = size_in_bytes / (1024 * 1024 * 1024 * 1024)
    return f"{round(size_in_terabytes, 3)} TB"


def generate_magnet(hash, tracker=None, title=None, url=None):
    params = {"xt": "urn:btih:" + hash}
    if tracker:
        params["tr"] = tracker
    if title:
        params["dn"] = title
    if url:
        params["as"] = url
    return "magnet:?" + urllib.parse.urlencode(params)


def is_autorized(response: Response, username: str) -> bool:
    soup = BeautifulSoup(response.text, 'html.parser')
    logged_in_username = soup.find('a', {'id': 'logged-in-username'})

    if 'profile.php?mode=register' in response.url:
        raise AuthorizationException('Ошибка авторизации. Проверьте логин и пароль.')
    if not logged_in_username or logged_in_username.text != username:
        raise AuthorizationException('Ошибка авторизации. Признаки успешного входа не найдены.')
    return True


def is_captcha(response: Response) -> Tag | NavigableString | None:
    soup = BeautifulSoup(response.text, 'html.parser')
    captcha_tag = soup.find('img', {'src': lambda x: x and 'captcha' in x})
    if captcha_tag:
        return captcha_tag
    return False


def save_captcha(session: Session,
                captcha_tag: Tag | NavigableString | None) -> bool:
    if captcha_tag:
        captcha_url = Url.HOST.value + '/' + captcha_tag['src']
        captcha_response = session.get(captcha_url)
        with open('src/rutracker-api/captcha/captcha.jpg', 'wb') as file:
            file.write(captcha_response.content)
        logger.info('CAPTCHA сохранена как captcha.jpg')


def get_captcha():
    with open('src/rutracker-api/captcha/captcha.jpg', 'rb') as file:
        return file.read()
