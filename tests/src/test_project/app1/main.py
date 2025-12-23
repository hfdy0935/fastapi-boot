from fastapi_boot.core import provide_app


app = provide_app(inject_timeout=10)
