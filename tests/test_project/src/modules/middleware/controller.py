from fastapi import WebSocket
from fastapi_boot.core import Controller, Get, Prefix, WS, use_http_middleware, use_ws_middleware
from test_project.src.modules.middleware.middleware import counter_plus_one_http_middleware, counter_minus_one_websocket_middleware


@Controller('/middleware')
class MiddlewareController:
    @Get('/global_only')
    def fn1(self):
        return 'ok'

    @Prefix()
    class _:
        _ = use_http_middleware(
            counter_plus_one_http_middleware, counter_plus_one_http_middleware)
        __ = use_ws_middleware(
            counter_minus_one_websocket_middleware, only_message=True)

        @Get('/global_local2')
        def fn2(self):
            return 'ok'

        @WS('/websocket')
        async def fn3(self, websocket: WebSocket):
            await websocket.accept()
            await websocket.send_json({"msg": "Hello WebSocket"})
            await websocket.close()
