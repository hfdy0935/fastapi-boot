from typing import Final


class TortoiseConfig:
    db_url: Final[str] = 'sqlite://resource/db.sqlite'
    modules: Final[list[str]] = [
        'test_project.src.modules.tortoise_utils.model']
