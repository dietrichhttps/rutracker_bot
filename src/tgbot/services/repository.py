from typing import List

from tgbot.settings.settings import DisplaySetting, SearchSetting


class Repo:
    """Db abstraction layer"""

    def __init__(self, conn):
        self.conn = conn

    # users
    async def add_user(self, user_id) -> None:
        """Store user in DB, ignore duplicates"""
        # await self.conn.execute(
        #     "INSERT INTO tg_users(userid) VALUES $1 ON CONFLICT DO NOTHING",
        #     user_id,
        # )
        return

    async def list_users(self) -> List[int]:
        """List all bot users"""
        return [
            # row[0]
            # async for row in self.conn.execute(
            #     "select userid from tg_users",
            # )
        ]


def update_search_params(search_settings: SearchSetting):
    search_params = {
        'sort': search_settings.sort,
        'order': search_settings.order,
        'category': search_settings.category,
    }
    return search_params


def update_display_params(display_settings: DisplaySetting):
    display_params = {
        'display_mode': display_settings.display_mode,
    }
    return display_params


def get_search_settings_callback_data() -> list[str]:
    watch_res_callback_data = [
        'display_mode', 'sort', 'order', 'sort_seeds', 'sort_leeches',
        'sort_downloads', 'sort_registered', 'order_desc', 'order_asc',
        'display_list', 'display_card'
    ]

    return watch_res_callback_data
