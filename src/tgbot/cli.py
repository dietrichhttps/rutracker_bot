import asyncio
from tgbot.keyboards.keyboards import set_main_menu
from utils.general_logging import get_logger, setup_logger

from aiogram import Bot, Dispatcher
# from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from aiogram.contrib.fsm_storage.redis import RedisStorage

from src.tgbot.config import load_config
# from handlers.admin import register_admin
from src.tgbot.handlers.user import user_router
from src.tgbot.handlers.other import other_router

setup_logger()
logger = get_logger(__name__)


def create_pool(user, password, database, host, echo):
    raise NotImplementedError  # TODO check your db connector


async def main():
    logger.info("Starting bot")
    config = load_config("/home/aliceglass/Study/developing/tg_bots/my_projects/rutracker_bot/bot.ini")

    # if config.tg_bot.use_redis:
    #     storage = RedisStorage()
    # else:
    #     storage = MemoryStorage()
    # pool = await create_pool(
    #     user=config.db.user,
    #     password=config.db.password,
    #     database=config.db.database,
    #     host=config.db.host,
    #     echo=False,
    # )

    bot = Bot(token=config.tg_bot.token)
    dp = Dispatcher(bot=bot)
    dp.include_router(user_router)
    dp.include_router(other_router)

    # Настраиваем главное меню бота
    await set_main_menu(bot)

    # start
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


def cli():
    """Wrapper for command line"""
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")


if __name__ == '__main__':
    cli()
