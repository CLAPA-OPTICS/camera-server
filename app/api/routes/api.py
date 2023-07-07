from fastapi import APIRouter

from . import frame

router = APIRouter()

router.include_router(frame.router, 
                      tags=["get_frames"], 
                      #prefix="/frames/{slug}/bits",
)

router.include_router(frame.router, 
                      tags=["get_axis_data"], 
                      #prefix="/projection/{slug}/direction",
)