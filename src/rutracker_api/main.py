import requests

from .parser import Parser
from .page_provider import PageProvider
from .api_provider import ApiProvider
from typing import Union
from .enums import Sort, Order
from .torrent import Torrent


class RutrackerApi(object):
    def __init__(self, proxy: str):
        self.session = requests.Session()
        self.session.proxies = {
                'http': proxy,
                'https': proxy,
            }
        self.parser = Parser()
        self.page_provider = PageProvider(self.session)
        self.api = ApiProvider(self.session)

    def login(self, username: str, password: str, captcha: str | None = None) -> None:
        """Login Rutracker.org"""

        return self.page_provider.login(username, password, captcha)

    def search_captcha(self):
        return self.page_provider.search_captcha()

    def search(
        self,
        query: str,
        sort: Union[Sort, str] = "desc",
        order: Union[Order, str] = "seeds",
        page: int = 1,
        get_hash: bool = False,
    ) -> dict:
        """Search for torrents. Returns a dictionary with the keys 'count', 'page', 'total_pages' and 'result'"""

        if isinstance(sort, str):
            sort = Sort[sort.upper()].value
        if isinstance(sort, Sort):
            sort = sort.value
        if isinstance(order, str):
            order = Order[order.upper()].value
        if isinstance(order, Order):
            order = order.value

        html = self.page_provider.search(query, sort, order, page)
        results = self.parser.parse_search(html)
        if not get_hash:
            return results
        # get hashes
        ids = [r.topic_id for r in results["result"]]
        hashes = self.api.get_tor_hash(ids)
        for torrent in results["result"]:
            torrent.hash = hashes[str(torrent.topic_id)]
        return results

    def status(self):
        """Returns information about the user"""

        return self.page_provider.status()

    def download(self, topic_id: Union[str, int]) -> bytes:
        """Download a .torrent file. Returns bytes"""

        return self.page_provider.torrent_file(topic_id)

    def topic(self, topic_id: Union[str, int]) -> Torrent:
        """Returns information about the torrent"""

        response = self.api.get_tor_topic_data(topic_id)
        return self.parser.parse_topic(response)
