from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest

from src.test_project.shared import MiddlewareCounter


@pytest.mark.anyio
async def test_middleware(
    test_app1_client: TestClient, test_app1_async_client: AsyncClient
):
    init_count = MiddlewareCounter.count

    # local http middleware*2
    resp = await test_app1_async_client.get('/middleware/local')
    assert resp.status_code == 200
    assert MiddlewareCounter.count == init_count + 2  # 两次local
    init_count = MiddlewareCounter.count

    # websocket middleware
    #  /app1不能少
    with test_app1_client.websocket_connect('/app1/middleware/websocket') as websocket:
        data = websocket.receive_json()
        assert data == {"msg": "Hello WebSocket"}
        assert MiddlewareCounter.count == init_count - 1
        init_count = MiddlewareCounter.count
