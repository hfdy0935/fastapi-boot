from fastapi import FastAPI, WebSocket
from fastapi_boot.core import Controller, Get, Prefix, Post, WS, on_app_ready


@Controller('/cbv')
class EndpointController:
    @Get()
    def func1(self):
        return {
            'code': 0,
            'msg': 'cbv_get'
        }

    @Prefix('/prefix')
    class _:
        @Post()
        async def func2(self):
            return {
                'code': 0,
                'msg': 'cbv_prefix_post'
            }


@Controller('/fbv').put('')
async def func3():
    return {
        'code': 0,
        'msg': 'fbv_put'
    }


def app_ready_callback(app: FastAPI):
    @app.delete('/fbv')
    def _():
        return {
            'code': 0,
            'msg': 'fbv_delete'
        }


on_app_ready(app_ready_callback)


@Controller('/websocket')
class WebSocketController:
    @WS()
    async def func4(self, websocket: WebSocket):
        await websocket.accept()
        await websocket.send_json({"msg": "Hello WebSocket"})
        await websocket.close()
