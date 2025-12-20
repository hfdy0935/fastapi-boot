from httpx import AsyncClient
import pytest


@pytest.mark.anyio
async def test_middleware(test_app1_async_client: AsyncClient):
    # clear
    resp = await test_app1_async_client.delete('/user/all')
    assert resp.status_code == 200

    # get cnt
    resp = await test_app1_async_client.get('/user/all')
    assert resp.status_code == 200
    init_cnt = len(resp.json()['data'])

    # create
    resp = await test_app1_async_client.post('/user', json={
        'id': 1,
        'name': 'zhangsan',
        'age': 20
    })
    assert resp.status_code == 200
    assert resp.json()['data'] == 1

    resp = await test_app1_async_client.get('/user/all')
    assert resp.status_code == 200
    assert len(resp.json()['data']) == init_cnt + 1

    # get by name
    resp = await test_app1_async_client.get('/user', params={
        'name': 'zhangsan'
    })
    assert resp.status_code == 200
    user = resp.json()['data'][0]
    assert user['name'] == 'zhangsan'
    assert user['age'] == 20

    # delete by name
    resp = await test_app1_async_client.delete('/user', params={
        'name': 'zhangsan'
    })
    assert resp.status_code == 200
    assert resp.json()['data'] == 1
