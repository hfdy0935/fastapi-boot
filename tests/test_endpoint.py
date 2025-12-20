from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response, AsyncClient
import pytest


def test_cbv(test_client: TestClient):
    resp: Response = test_client.get('/cbv')
    assert resp.status_code == 200
    assert resp.json() == {
        'code': 0,
        'msg': 'cbv_get'
    }

    resp: Response = test_client.post('/cbv/prefix')
    assert resp.status_code == 200
    assert resp.json() == {
        'code': 0,
        'msg': 'cbv_prefix_post'
    }


@pytest.mark.anyio
async def test_fbv(test_async_client: AsyncClient):
    resp: Response = await test_async_client.put('/fbv')
    assert resp.status_code == 200
    assert resp.json() == {
        'code': 0,
        'msg': 'fbv_put'
    }

    resp: Response = await test_async_client.delete('/fbv')
    assert resp.status_code == 200
    assert resp.json() == {
        'code': 0,
        'msg': 'fbv_delete'
    }


def test_websocket(app_instance: FastAPI):
    client = TestClient(app_instance)
    with client.websocket_connect('/websocket') as websocket:
        data = websocket.receive_json()
        assert data == {"msg": "Hello WebSocket"}
