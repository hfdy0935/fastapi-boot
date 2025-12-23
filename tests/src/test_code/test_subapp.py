from httpx import AsyncClient
import pytest


@pytest.mark.anyio
async def test_middleware(test_app1_async_client: AsyncClient, test_app2_async_client: AsyncClient):
    resp = await test_app1_async_client.get('/hello')
    assert resp.status_code == 200
    assert resp.json() == 'world from subapp1'

    resp = await test_app2_async_client.get('/hello')
    assert resp.status_code == 200
    assert resp.json() == 'world from subapp2'
