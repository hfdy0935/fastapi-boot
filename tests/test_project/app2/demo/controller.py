from fastapi_boot.core import Controller, Get


@Controller('/hello')
class _:
    @Get()
    def fn(self):
        return 'world from subapp2'
