from contextlib import asynccontextmanager
from tortoise import Tortoise

from src.test_project.app1.config import TortoiseConfig

# 启动uvicorn（test、挂载到其他FastAPi实例）时，lifespan不生效


@asynccontextmanager
async def lifespan(_):
    await Tortoise.init(db_url=TortoiseConfig.db_url, modules=dict(models=TortoiseConfig.modules))
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()
