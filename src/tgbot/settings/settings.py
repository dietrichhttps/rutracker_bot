class Settings:
    def __init__(
            self,
            display_mode: str = 'card',
            sort: str = 'seeds',
            order: str = 'desc'
    ) -> None:
        self.display_mode = display_mode
        self.sort = sort
        self.order = order
