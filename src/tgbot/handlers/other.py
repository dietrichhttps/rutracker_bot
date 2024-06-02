from aiogram import F, Router
from aiogram.types import Message

other_router = Router()


@other_router.message(~F.text.startswith('/'))
async def send_echo(message: Message):
    await message.answer(f'Это эхо! {message.text}')
