from fastapi_boot.core import provide_app
from .demo.controller import SubAppController

app = provide_app(controllers=[SubAppController])
