from collections.abc import Callable, Coroutine
from typing import Any
from fastapi import Request, Response, WebSocket
from fastapi_boot.core import HTTPMiddleware
from test_project.app1.src.shared import MiddlewareCounter


@HTTPMiddleware
async def counter_plus_one_http_middleware(requets: Request, call_next: Callable[[Request], Coroutine[Any, Any, Response]]):
    MiddlewareCounter.count += 1
    return await call_next(requets)


async def counter_plus_one_http_middleware1(requets: Request, call_next: Callable[[Request], Coroutine[Any, Any, Response]]):
    MiddlewareCounter.count += 1
    return await call_next(requets)


async def counter_plus_one_http_middleware2(requets: Request, call_next: Callable[[Request], Coroutine[Any, Any, Response]]):
    MiddlewareCounter.count += 1
    return await call_next(requets)


async def counter_minus_one_websocket_middleware(ws: WebSocket, call_next: Callable[[WebSocket], Coroutine[Any, Any, None]]):
    MiddlewareCounter.count -= 1
    await call_next(ws)
