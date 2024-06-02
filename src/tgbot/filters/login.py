from aiogram.filters import BaseFilter
from aiogram.types import Message


class UsernameFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        # Добавьте свою логику проверки username
        # Например, проверка длины и допустимых символов
        username = message.text
        if 3 <= len(username) <= 20 and username.isalnum() and not username.startswith('/'):
            return True
        return False


class PasswordFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        # Добавьте свою логику проверки password
        # Например, проверка длины и сложности пароля
        password = message.text
        if len(password) >= 8 and not password.startswith('/'):
            return True
        return False
