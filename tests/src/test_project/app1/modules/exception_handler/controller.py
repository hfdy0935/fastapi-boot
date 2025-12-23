from fastapi_boot.core import Controller
from src.test_project.app1.modules.exception_handler.exception import NotFoundException


@Controller('/exception_handler').get('')
def fn():
    raise NotFoundException()
