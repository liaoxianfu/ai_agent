import asyncio
from fastapi import FastAPI

from fastapi import Request, Response
import time
from config.context import request_id_context
from config.log import logger
import uuid
from . import chat
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await asyncio.sleep(1)
    yield
    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)
app.include_router(chat.router)


@app.middleware("http")
async def extra_process(request: Request, call_next):
    start_time = time.time()
    request_id = request.headers.get("x-request-id")
    if request_id is None:
        request_id = uuid.uuid4().hex
    request_id_context.set(request_id)
    response: Response = await call_next(request)
    ptime = time.time() - start_time
    logger.info(
        f"process finished... process time [{int(ptime*1000)}ms]: {response.status_code}-{request.url}"
    )

    return response
