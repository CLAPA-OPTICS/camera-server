import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware

from app.api.errors.http_error import http_error_handler
from app.api.errors.validation_error import http422_error_handler
from app.api.routes.api import router as api_router
from app.core.config import get_app_settings
from app.core.events import create_start_app_handler, create_stop_app_handler

def get_application() -> FastAPI:
    
    #settings = get_app_settings()

    #settings.configure_logging()

    #global application
    #application = FastAPI(**settings.fastapi_kwargs)
    application = FastAPI()

    #application.add_middleware(
    #    CORSMiddleware,
    #    allow_origins=settings.allowed_hosts,
    #    allow_credentials=True,
    #    allow_methods=["*"],
    #    allow_headers=["*"],
    #)

    origins = ["*"]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # 允许访问的源
        allow_credentials=True,  # 支持 cookie
        allow_methods=["*"],  # 允许使用的请求方法
        allow_headers=["*"]  # 允许携带的 Headers
    )

    application.add_event_handler(
        "startup",
        create_start_app_handler(application),
    )
    application.add_event_handler(
        "shutdown",
        create_stop_app_handler(application),
    )

    application.add_exception_handler(HTTPException, http_error_handler)
    application.add_exception_handler(RequestValidationError, http422_error_handler)

    application.include_router(api_router) #, prefix=settings.api_prefix)

    return application

if __name__ == "__main__":

    app = get_application()

    uvicorn.run(app=app) 