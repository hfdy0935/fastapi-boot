from fastapi_boot.core import provide_app
from .modules.book.controller import BookController
from .modules.endpoint.controller import endpoint_controllers
from .modules.middleware.controller import MiddlewareController
from .modules.subapp.controller import SubAppController
from .modules.tortoise_utils.controller import UserController

app = provide_app(
    controllers=[
        BookController,
        *endpoint_controllers,
        MiddlewareController,
        SubAppController,
        UserController,
    ]
)
