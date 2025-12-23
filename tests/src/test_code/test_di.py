from httpx import AsyncClient
import pytest


@pytest.mark.anyio
async def test_book_cnt(test_app1_async_client: AsyncClient):
    # get cnt
    resp = await test_app1_async_client.get('/book/cnt')
    assert resp.status_code == 200
    assert resp.json() == 4

    # get exists
    resp = await test_app1_async_client.get('/book/三国演义')
    assert resp.status_code == 200
    sanguoyanyi = resp.json()
    assert sanguoyanyi['name'] == '三国演义'
    assert sanguoyanyi['author'] == '罗贯中'
    assert sanguoyanyi['price'] == 100

    # get not exists
    assert (await test_app1_async_client.get('/book/三国志')).status_code == 404

    # update success
    resp = await test_app1_async_client.put('/book', json={
        'name': sanguoyanyi['name'],
        'author': sanguoyanyi['author'],
        'price': sanguoyanyi['price']+10
    })
    assert resp.status_code == 200

    resp = await test_app1_async_client.get('/book/三国演义')
    assert resp.status_code == 200
    assert resp.json()['price'] == sanguoyanyi['price']+10

    # update fail
    resp = await test_app1_async_client.put('/book', json={
        'name': sanguoyanyi['name'],
        'author': sanguoyanyi['author'],
        'price': -1
    })
    assert resp.status_code == 422

    # create
    resp = await test_app1_async_client.post('/book', json={
        'name': '聊斋志异',
        'author': '蒲松龄',
        'price': 130
    })
    assert resp.status_code == 200

    resp = await test_app1_async_client.get('/book/聊斋志异')
    assert resp.status_code == 200
    liaozhaizhiyi = resp.json()
    assert liaozhaizhiyi['name'] == '聊斋志异'
    assert liaozhaizhiyi['author'] == '蒲松龄'
    assert liaozhaizhiyi['price'] == 130

    resp = await test_app1_async_client.get('/book/cnt')
    assert resp.status_code == 200
    assert resp.json() == 5

    # delete
    resp = await test_app1_async_client.delete('/book/西游记')
    assert resp.status_code == 200

    resp = await test_app1_async_client.get('/book/cnt')
    assert resp.status_code == 200
    assert resp.json() == 4
