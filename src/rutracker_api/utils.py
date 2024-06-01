import os
import urllib.parse

from bs4 import BeautifulSoup
from requests import Response, Session

from rutracker_api.enums import Path
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
    a_tag = soup.find('a', {'id': 'logged-in-username'})

    if 'profile.php?mode=register' in response.url:
        raise AuthorizationException('Ошибка авторизации. Проверьте логин и пароль.')
    if not a_tag or a_tag.text != username:
        raise AuthorizationException('Ошибка авторизации. Признаки успешного входа не найдены.')
    return True


def get_profile_url(response: Response):
    soup = BeautifulSoup(response.text, 'html.parser')
    a_tag = soup.find('a', {'id': 'logged-in-username'})
    url = a_tag['href']
    if url:
        return url
    return None


def search_captcha(response: Response) -> str | None:
    soup = BeautifulSoup(response.text, 'html.parser')
    captcha_tag = soup.find('img', {'src': lambda x: x and 'captcha' in x})
    if captcha_tag:
        img_url = captcha_tag['src']
        return img_url
    return None


def get_captcha(session: Session, img_url: str) -> str:
    if img_url:
        captcha_response = session.get(img_url)
        logger.info('CAPTCHA сохранена в буффер')
        return captcha_response.content


# Функция для извлечения информации
def extract_user_info(response: Response):
    soup = BeautifulSoup(response.text, 'html.parser')

    user_info = {}

    # Извлечение роли
    role = soup.find('th', text='Роль:').find_next_sibling('td').text.strip()
    user_info['Роль'] = role

    # Извлечение стажа
    experience = soup.find('th', text='Стаж:').find_next_sibling('td').text.strip()
    user_info['Стаж'] = experience

    # Извлечение даты регистрации
    registration_date = soup.find('th', text='Зарегистрирован:').find_next_sibling('td').text.strip()
    user_info['Зарегистрирован'] = registration_date

    # Извлечение статистики отданного
    traffic_stats = soup.find('th', text='Статистика отданного:').find_next_sibling('td')
    stats = {
        'Сегодня': traffic_stats.find('td', {'id': 'uploaded_day'}).text.strip(),
        'Вчера': traffic_stats.find('td', {'id': 'up_yesterday'}).text.strip(),
        'Всего': traffic_stats.find('td', {'id': 'uploaded_total'}).text.strip(),
        'На редких': traffic_stats.find('td', {'id': 'up_rare_total'}).text.strip()
    }
    user_info['Статистика отданного'] = stats

    return user_info
