from fastapi import APIRouter

from . import frame

from . import safety

from . import user 

router = APIRouter()

router.include_router(frame.router, 
                      tags=["get_frames"], 
                      #prefix="/frames/{slug}/bits",
)

router.include_router(frame.router, 
                      tags=["get_axis_data"], 
                      #prefix="/projection/{slug}/direction",
)

router.include_router(safety.router, 
                      tags=["safty"], 
                      #prefix="/projection/{slug}/direction",
)

router.include_router(user.router, 
                      tags=["user"], 
                      #prefix="/projection/{slug}/direction",
)