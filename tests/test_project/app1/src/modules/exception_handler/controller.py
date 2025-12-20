from fastapi_boot.core import Controller
from test_project.app1.src.modules.exception_handler.exception import NotFoundException


@Controller('/exception_handler').get('')
def fn():
    raise NotFoundException()
