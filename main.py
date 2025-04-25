import uvicorn
from config.log import setup_logging
async def run_app():
    """
    应用启动函数
    
    步骤：
    1. 初始化日志系统
    2. 配置 uvicorn
    3. 启动服务器
    """
    # 初始化日志系统
    await setup_logging()
    
    # 配置 uvicorn
    config = uvicorn.Config(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # 禁用默认配置
    )
    
    # 启动服务器
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == '__main__':
    import asyncio
    asyncio.run(run_app())
