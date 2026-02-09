import uvicorn

# 可以直接运行
if __name__ == '__main__':
    uvicorn.run('src.test_project.app:app', reload=True)
