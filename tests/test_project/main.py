from fastapi import FastAPI
import uvicorn
from test_project.app1.main import app as app1
from test_project.app2.main import app as app2

app = FastAPI()
app.mount('/app1', app1)
app.mount('/app2', app2)

if __name__ == '__main__':
    uvicorn.run('test_project.main:app', reload=True)
