from typing import Callable

from fastapi import FastAPI
from loguru import logger

from .settings.app import AppSettings
from ..db.events import close_db_connection, connect_to_db

from .Camera import Camera

def create_start_app_handler(app: FastAPI) -> Callable:  # type: ignore
    async def start_app() -> None:
        app.state.camera = Camera()
        #app.state.camera.start()
        await connect_to_db(app)

    return start_app

def create_stop_app_handler(app: FastAPI) -> Callable:  # type: ignore
    @logger.catch
    async def stop_app() -> None:
        await close_db_connection(app)

    return stop_app
