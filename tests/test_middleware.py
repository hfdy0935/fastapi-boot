from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest

from test_project.src.shared import MiddlewareCounter


@pytest.mark.anyio
async def test_middleware(test_client: TestClient, test_async_client: AsyncClient):
    init_count = MiddlewareCounter.count

    # global http middleware
    resp = await test_async_client.get('/middleware/global_only')
    assert resp.status_code == 200
    assert MiddlewareCounter.count == init_count+1
    init_count += 1

    # global + local http middleware*2
    resp = await test_async_client.get('/middleware/global_local2')
    assert resp.status_code == 200
    assert MiddlewareCounter.count == init_count+3  # 两次local
    init_count += 3

    # websocket middleware
    with test_client.websocket_connect('/middleware/websocket') as websocket:
        data = websocket.receive_json()
        assert data == {"msg": "Hello WebSocket"}
        assert MiddlewareCounter.count == init_count-1
        init_count -= 1
