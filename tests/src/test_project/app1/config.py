from typing import Final


class TortoiseConfig:
    db_url: Final[str] = 'sqlite://:memory:'
    modules: Final[list[str]] = [
        'src.test_project.app1.modules.tortoise_utils.model']
