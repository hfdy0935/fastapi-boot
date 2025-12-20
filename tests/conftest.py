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
def test_app1_client():
    client = TestClient(app, base_url='http://test/app1')
    yield client


@pytest.fixture(scope='module')
def test_app2_client():
    client = TestClient(app, base_url='http://test/app2')
    yield client


@pytest.fixture(scope='module')
def test_app1_async_client():
    ac = AsyncClient(transport=ASGITransport(
        app=app), base_url="http://test1/app1")
    yield ac


@pytest.fixture(scope='module')
def test_app2_async_client():
    ac = AsyncClient(transport=ASGITransport(
        app=app), base_url="http://test1/app2")
    yield ac


@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_db():
    await Tortoise.init(
        db_url='sqlite://:memory:',
        modules={'models': [
            'test_project.app1.src.modules.tortoise_utils.model']}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise._drop_databases()
