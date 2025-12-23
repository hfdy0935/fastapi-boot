import uvicorn
from src.test_project.app import app

# 可以直接运行
if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
