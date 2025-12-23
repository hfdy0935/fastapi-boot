from httpx import AsyncClient
import pytest


@pytest.mark.anyio
async def test_exception_handler(test_app1_async_client: AsyncClient):
    resp = await test_app1_async_client.get('/exception_handler')
    assert resp.status_code == 200
    assert resp.json() == {
        'code': 404,
        'msg': 'Not Found'
    }
