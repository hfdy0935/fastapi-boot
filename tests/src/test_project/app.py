from fastapi import FastAPI
from src.test_project.app1.main import app as app1
from src.test_project.app2.main import app as app2
from src.test_project.event import lifespan


# 包装app
app = FastAPI(lifespan=lifespan)
app.mount('/app1', app1)
app.mount('/app2', app2)
