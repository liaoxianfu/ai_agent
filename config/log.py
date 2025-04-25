from pathlib import Path
import logging
import asyncio
from loguru import logger
import sys
import os
from .context import request_id_context


class Settings:
    # 项目基础配置
    BASE_DIR = Path(__file__).resolve().parent.parent
    DEBUG = True

    # 日志配置
    LOG_ROTATION = "00:00"  # 每天午夜轮转
    LOG_RETENTION = "30 days"  # 保留30天
    LOG_COMPRESSION = "zip"  # 压缩格式


settings = Settings()


class InterceptHandler(logging.Handler):
    """
    日志拦截处理器：将所有 Python 标准日志重定向到 Loguru

    工作原理：
    1. 继承自 logging.Handler
    2. 重写 emit 方法处理日志记录
    3. 将标准库日志转换为 Loguru 格式
    """

    def emit(self, record: logging.LogRecord) -> None:
        # 尝试获取日志级别名称
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 获取调用帧信息
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # 使用 Loguru 记录日志
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


async def async_makedirs(path: str, exist_ok: bool = True) -> None:
    """
    异步创建目录。

    Args:
        path (str): 要创建的目录路径
        exist_ok (bool): 如果目录已存在，是否忽略错误
    """
    await asyncio.to_thread(os.makedirs, path, exist_ok=exist_ok)


async def setup_logging():
    """
    配置日志系统

    功能：
    1. 控制台彩色输出
    2. 文件日志轮转
    3. 错误日志单独存储
    4. 异步日志记录
    """
    # 步骤1：移除默认处理器
    logger.remove()

    # 步骤2：定义日志格式
    log_format = (
        # 时间信息
        "| <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        # 日志级别，居中对齐
        "<level>{level: ^8}</level> | "
        "<level>{extra[traceid]: <32}</level> | "
        # 进程和线程信息
        "process [<cyan>{process}</cyan>]:<cyan>{thread}</cyan> | "
        # 文件、函数和行号
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        # 日志消息
        "<level>{message}</level> |"
    )

    # 步骤3：配置控制台输出
    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG" if settings.DEBUG else "INFO",
        enqueue=True,  # 启用异步写入
        backtrace=True,  # 显示完整的异常回溯
        diagnose=True,  # 显示变量值等诊断信息
        colorize=True,  # 启用彩色输出
        filter=_filter,
    )

    # 步骤4：创建日志目录
    log_dir = Path(settings.BASE_DIR) / "logs"
    await async_makedirs(str(log_dir))

    # 步骤5：配置常规日志文件
    logger.add(
        str(log_dir / "{time:YYYY-MM-DD}.log"),
        format=log_format,
        level="INFO",
        rotation=settings.LOG_ROTATION,  # 每天轮转
        retention=settings.LOG_RETENTION,  # 保留30天
        compression=settings.LOG_COMPRESSION,  # 压缩旧日志
        encoding="utf-8",
        filter=_filter,
        enqueue=True,  # 异步写入
    )

    # 步骤6：配置错误日志文件
    logger.add(
        str(log_dir / "error_{time:YYYY-MM-DD}.log"),
        format=log_format,
        level="ERROR",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression=settings.LOG_COMPRESSION,
        encoding="utf-8",
        enqueue=True,
        filter=_filter,
    )

    # 步骤7：配置标准库日志
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 步骤8：配置第三方库日志
    for logger_name in [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "uvicorn.asgi",
        "fastapi",
        "fastapi.error",
    ]:
        _logger = logging.getLogger(logger_name)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False

    logger.info("init logger success")


def _filter(record):
    record["extra"] = {"traceid": request_id_context.get("miss_traceid")}
    return True
