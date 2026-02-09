from fastapi import FastAPI, WebSocket
from fastapi_boot.core import Controller, Get, Prefix, Post, WS


@Controller('/cbv')
class EndpointController:
    @Get()
    def func1(self):
        return {'code': 0, 'msg': 'cbv_get'}

    @Prefix('/prefix1')
    class _:
        @Prefix('/prefix2')
        class _:
            @Prefix('/prefix3')
            class _:
                @Prefix('/prefix4')
                class _:
                    @Prefix('/prefix5')
                    class _:
                        @Prefix('/prefix6')
                        class _:
                            @Prefix('/prefix7')
                            class _:
                                @Post()
                                async def func2(self):
                                    return {'code': 0, 'msg': 'cbv_prefix_post'}


@Controller('/fbv').put('')
async def func3():
    return {'code': 0, 'msg': 'fbv_put'}


@Controller('/websocket')
class WebSocketController:
    @WS()
    async def func4(self, websocket: WebSocket):
        await websocket.accept()
        await websocket.send_json({"msg": "Hello WebSocket"})
        await websocket.close()


endpoint_controllers = [EndpointController, func3, WebSocketController]
