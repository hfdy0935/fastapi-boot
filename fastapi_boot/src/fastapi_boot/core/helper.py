from collections.abc import Callable, Coroutine
from typing import Any, Protocol, TypeVar, ParamSpec
from fastapi import Depends, FastAPI, Request, Response, WebSocket
from .const import (
    PropNameConstant,
    UseMiddlewareReturnValuePlaceholder,
    dep_store,
    app_task_store,
    use_dep_record_store,
)
from .model import UseMiddlewareRecord

T = TypeVar('T')


def use_dep(
    dependency: Callable[..., T | Coroutine[Any, Any, T]] | None, use_cache: bool = True
) -> T:
    """作为类变量，用于给Controller中所有直接endpoint添加依赖参数，效果等同于FastAPI的Depends

    >>> Example
    ```python
    def get_ua(request: Request):
        return request.headers.get('user-agent','')

    @Controller('/foo')
    class Foo:
        ua = use_dep(get_ua)

        @Get('/ua')
        def foo(self):
            return self.ua

    ```
    """
    value: T = Depends(dependency=dependency, use_cache=use_cache)
    use_dep_record_store.add(value)
    return value


def _create_use_middleware_return_value(record: UseMiddlewareRecord):
    bp = UseMiddlewareReturnValuePlaceholder()
    setattr(bp, PropNameConstant.USE_MIDDLEWARE, record)
    return bp


def use_http_middleware(
    *dispatches: Callable[
        [Request, Callable[[Request], Coroutine[Any, Any, Response]]], Any
    ],
):
    """给类中所有 **直接** http的endpoint添加http中间件
    root_path: app被mount到其他app时的根路径前缀

    ```python

    from collections.abc import Callable
    from typing import Any
    from fastapi import Request
    from fastapi_boot.core import Controller, use_http_middleware


    async def middleware_foo(request: Request, call_next: Callable[[Request], Any]):
        print('middleware_foo before')
        resp = await call_next(request)
        print('middleware_foo after')
        return resp

    async def middleware_bar(request: Request, call_next: Callable[[Request], Any]):
        print('middleware_bar before')
        resp = await call_next(request)
        print('middleware_bar after')
        return resp

    @Controller('/foo')
    class FooController:
        _ = use_http_middleware(middleware_foo, middleware_bar)

        # 1. middleware_bar before
        # 2. middleware_foo before
        # 3. call endpoint
        # 4. middleware_foo after
        # 5. middleware_bar after

        # ...
    ```

    """
    record = UseMiddlewareRecord(http_dispatches=list(dispatches))
    return _create_use_middleware_return_value(record)


def use_ws_middleware(
    *dispatches: Callable[
        [WebSocket, Callable[[WebSocket], Coroutine[Any, Any, None]]], Any
    ],
    only_message: bool = False,
):
    """给类中所有 **直接** websocket的endpoint添加websocket中间件
    >>> Params
    only_message=False: 只有收到消息会触发，连接等事件不会触发

    >>> Examples:
    ```python

    from collections.abc import Callable
    from typing import Any
    from fastapi import Request, WebSocket
    from fastapi_boot.core import Controller, use_http_middleware, middleware_ws_foo

    async def middleware_ws_foo(websocket: WebSocket, call_next: Callable):
        print('before ws send data foo') # as pos a
        await call_next(websocket)
        print('after ws send data foo') # as pos b

    async def middleware_ws_bar(websocket: WebSocket, call_next: Callable):
        print('before ws send data bar') # as pso c
        await call_next()
        print('after ws send data bar') # as pso d

    async def middleware_bar(request: Request, call_next: Callable[[Request], Any]):
        print('middleware_bar before') # as pos e
        resp = await call_next(request)
        print('middleware_bar after') # as pos f
        return resp


    @Controller('/chat')
    class WsController:
        _ = use_http_middleware(middleware_bar)
        ___ = use_ws_middleware(middleware_ws_bar, middleware_ws_foo, only_message=True)

        @Socket('/chat')
        async def chat(self, websocket: WebSocket):
            try:
                await websocket.accept()
                while True:
                    message = await websocket.receive_text()
                    # a c
                    await self.send_text(message)
                    # d b
            except:
                ...


        # e a c d b f
        @Post('/broadcast')
        async def send_broadcast_msg(self, msg: str = Query()):
            await self.broadcast(msg)
            return 'ok'
    ```

    """
    record = UseMiddlewareRecord(
        ws_dispatches=list(dispatches), ws_only_message=only_message
    )
    return _create_use_middleware_return_value(record)


DispatchFunc = Callable[
    [Request, Callable[[Request], Coroutine[Any, Any, Response]]], Any
]
P = ParamSpec('P')


class DispatchCls(Protocol):
    async def dispatch(self, request: Request, call_next: Callable): ...


def provide_app(
    app: FastAPI | None = None,
    controllers: list[Any] = [],
) -> FastAPI:
    """启动入口

    Args:
        app (FastAPI): FastAPi实例.
        controllers (list[Any], optional): scan_mode关闭时需手动导入Controller，可以传到这里，防止未使用被代码格式化工具移除. Defaults to [].
    Raises:
        e: _description_

    Returns:
        FastAPI: _description_
    """
    app = app or FastAPI()
    # emit controller tasks
    for controller in controllers:
        app_task_store.emit(id(controller), app)
    return app


def inject(tp: type[T], name: str | None = None) -> T:
    return dep_store.inject_dep(tp, name)
