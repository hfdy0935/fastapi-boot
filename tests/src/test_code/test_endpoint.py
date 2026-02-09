from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response, AsyncClient
import pytest


def test_cbv(test_app1_client: TestClient):
    resp: Response = test_app1_client.get('/cbv')
    assert resp.status_code == 200
    assert resp.json() == {'code': 0, 'msg': 'cbv_get'}

    resp: Response = test_app1_client.post(
        '/cbv/prefix1/prefix2/prefix3/prefix4/prefix5/prefix6/prefix7'
    )
    assert resp.status_code == 200
    assert resp.json() == {'code': 0, 'msg': 'cbv_prefix_post'}


@pytest.mark.anyio
async def test_fbv(test_app1_async_client: AsyncClient):
    resp: Response = await test_app1_async_client.put('/fbv')
    assert resp.status_code == 200
    assert resp.json() == {'code': 0, 'msg': 'fbv_put'}


def test_websocket(app_instance: FastAPI):
    client = TestClient(app_instance)
    with client.websocket_connect('/app1/websocket') as websocket:
        data = websocket.receive_json()
        assert data == {"msg": "Hello WebSocket"}
