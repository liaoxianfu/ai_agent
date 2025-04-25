from fastapi import APIRouter
from config.log import logger
import asyncio

router = APIRouter()


@router.get("/")
async def root():
    await asyncio.sleep(1)
    logger.info("hello world")
    return {"message": "Hello World"}


__all__ = ["router"]
