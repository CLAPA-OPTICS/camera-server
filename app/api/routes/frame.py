import cv2
import asyncio
import numpy as np
from pydantic import BaseModel
from starlette.requests import Request
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse, ORJSONResponse
from app.core.Camera import Camera

isAddFrame = False

def get_camera(request: Request) -> Camera:
    application = request.app
    camera = application.state.camera
    return camera

def get_queue() -> asyncio.Queue:
    q = asyncio.Queue(20)
    return q

def add_frame(q: asyncio.Queue, camera: Camera):
    while isAddFrame:
        q.append(camera.get_frame())

class Item(BaseModel):
    name: str
    min: float
    max: float

async def generate_frames(camera: Camera,
                          type = "8_bits"):
    global isAddFrame
    while True:
        # 从视频流中读取帧。
        frame = cv2.cvtColor(camera.get_frame(), cv2.COLOR_GRAY2BGR)
        # 将帧转换为JPEG格式。
        ret, buffer = cv2.imencode(".jpg", frame)
        # 将JPEG数据转换为字节字符串，并将其作为流响应返回。
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
        
def get_axis_data(camera: Camera, 
                  x1: float = 0.0, x2: float = 100.0):
    
    data = camera.raw_frame()
    shape_1 = data.shape[1]
    index_1 = np.arange(shape_1)
    print(int(x1/100*(shape_1 - 1)), int(x2/100*(shape_1 - 1)))
    data_1 = np.sum(data[int(x1/100*(shape_1 - 1)):int(x2/100*(shape_1 - 1))], axis = 0)
    data_1 = data_1/np.nanmax(data_1)
    return [{"index_0": index_1[i], "axis_0": data_1[i]} for i in range(index_1.shape[0])]

def set_exposure_time(camera: Camera, 
                      time: float = 200000):
    camera.CameraSetExposureTime(time)
    return

router = APIRouter()

##################################################################

"""将视频流作为流响应返回。"""
@router.get("/frame")
async def get_8_bits_img(camera: Camera = Depends(get_camera), 
                         type: str = "8_bits"):
    
    data = generate_frames(camera, type)
    return StreamingResponse(data,
                    media_type="multipart/x-mixed-replace;boundary=frame")

# 一维投影。
@router.get("/get_projection", response_class=ORJSONResponse)
def get_projection(camera: Camera = Depends(get_camera), 
                   x1: float = 0.0, x2: float = 100.0):

    data = get_axis_data(camera, x1, x2)
    return ORJSONResponse(data)

# 设置相机曝光。
@router.post("/set_exposure_time", response_class=ORJSONResponse)
def get_projection(camera: Camera = Depends(get_camera),
                   time: float = 0.0):

    global isAddFrame
    isAddFrame = False
    set_exposure_time(camera, time)
    return

@router.get("/start")
def start(camera: Camera = Depends(get_camera)):
    global isAddFrame
    isAddFrame = True
    camera.start()
    return

@router.get("/close")
def close(camera: Camera = Depends(get_camera)):
    global isAddFrame
    isAddFrame = False
    camera.release()
    return

@router.get("/start_sample")
def start_sample(backgroundtasks: BackgroundTasks, 
                 camera: Camera = Depends(get_camera)):
    global isAddFrame
    isAddFrame = True
    backgroundtasks.add_task(add_frame, camera.buffer, camera)
    return

@router.get("/stop_sample")
def stop_sample():
    global isAddFrame
    isAddFrame = False
    return
