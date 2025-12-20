from tortoise import Tortoise

from test_project.src.config import TortoiseConfig
from fastapi_boot.core import Lifespan


# test环境不启动uvicorn，lifespan不生效
@Lifespan
async def lifespan(_):
    await Tortoise.init(db_url=TortoiseConfig.db_url, modules=dict(models=TortoiseConfig.modules))
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()
