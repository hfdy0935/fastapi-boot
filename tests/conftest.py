import pytest_asyncio
from tortoise import Tortoise
from test_project.main import app
import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope='module')
def app_instance():
    yield app


@pytest.fixture(scope='module')
def test_client():
    client = TestClient(app)
    yield client


@pytest.fixture(scope='module')
def test_async_client():
    ac = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    yield ac


@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_db():
    await Tortoise.init(
        db_url='sqlite://:memory:',
        modules={'models': ['test_project.src.modules.tortoise_utils.model']}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise._drop_databases()
