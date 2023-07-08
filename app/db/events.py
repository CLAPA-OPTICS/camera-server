import asyncio
from fastapi import FastAPI
from loguru import logger
#import sqlite3
from ..core.settings.app import AppSettings

async def connect_to_db(app: FastAPI) -> None:
    logger.info("Connecting to Asyncio queue")

    #app.state.pool = asyncio.Queue(100)
    #app.state.db = sqlite3.connect('.cache/config.db')

    logger.info("Connection established")

    #while True:
    #    await app.state.pool.put(app.state.camera.get_frame())
    
    logger.info("Connection finished")

async def close_db_connection(app: FastAPI) -> None:
    logger.info("Closing connection to database")

    await app.state.camera.release()
    await app.state.pool.join()

    logger.info("Connection closed")
