class SearchSetting:
    def __init__(
            self,
            category: str = 'Все категории',
            sort: str = 'seeds',
            order: str = 'desc'
    ) -> None:
        self.category = category
        self.sort = sort
        self.order = order


class DisplaySetting:
    def __init__(
            self,
            display_mode: str = 'card'
    ) -> None:
        self.display_mode = display_mode
