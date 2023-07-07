import cv2
import asyncio
import numpy as np
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Body, Depends, Response, BackgroundTasks
from fastapi.responses import StreamingResponse, ORJSONResponse
from .Camera import Camera

isAddFrame = False

main = __import__("__main__")

def get_camera():
    camera = Camera()
    camera.start()
    return camera

def get_queue():
    return asyncio.Queue(20)

def add_frame(q: asyncio.Queue, camera: Camera):
    while isAddFrame:
        q.put(camera.get_frame())
    return

class Item(BaseModel):
    name: str
    min: float
    max: float
    
async def generate_frames(type = "8_bits"):
    application = main.app
    camera = application.state.camera
    #global application
    while True:
        # 从视频流中读取帧。
        frame = cv2.cvtColor(camera.get_frame() if type == '8_bits' else camera.raw_frame(), cv2.COLOR_GRAY2BGR)
        # 将帧转换为JPEG格式。
        ret, buffer = cv2.imencode(".jpg", frame)
        # 将JPEG数据转换为字节字符串，并将其作为流响应返回。
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

def get_axis_data(x1, x2):
    application = main.app
    camera = application.state.camera
    data = camera.raw_frame()
    shape_1 = data.shape[1]
    index_1 = np.arange(shape_1)
    
    data_1 = np.sum(data[int(x1/100*shape_1 - 1):int(x2/100*shape_1 - 1)], axis = 0)
    data_1 = data_1/np.nanmax(data_1)
    #index_0 = np.arange(data.shape[0])
    #data_0 = np.sum(data, axis = 1)
    return [{"index_0": index_1[i], "axis_0": data_1[i]} for i in range(index_1.shape[0])]

'''
def get_axis_data():
    application = main.app
    camera = application.state.camera
    data = camera.raw_frame()
    shape_1 = data.shape[1]
    index_1 = np.arange(shape_1)
    
    data_1 = np.sum(data, axis = 0)
    data_1 = data_1/np.nanmax(data_1)
    #index_0 = np.arange(data.shape[0])
    #data_0 = np.sum(data, axis = 1)
    return [{"index_0": index_1[i], "axis_0": data_1[i]} for i in range(index_1.shape[0])]
'''

def set_exposure_time(time: float):
    application = main.app
    camera = application.state.camera
    camera.CameraSetExposureTime(time)
    return

router = APIRouter()

@router.get("/frame")
async def get_8_bits_img():
    """将视频流作为流响应返回。"""
    data = generate_frames("8_bits")
    return StreamingResponse(data,
                    media_type="multipart/x-mixed-replace;boundary=frame")

@router.get("/raw_frame")
async def get_12_bits_img():
    """将视频流作为流响应返回。"""
    data = generate_frames("12_bits")
    return StreamingResponse(data,
                    media_type="multipart/x-mixed-replace;boundary=frame")

# 一维投影。
@router.get("/get_projection", response_class=ORJSONResponse)
def get_projection(x1: float = 0.0, x2: float = 100.0):
    """将视频流作为流响应返回。"""
    data = get_axis_data(x1, x2)
    return ORJSONResponse(data)

# 设置相机曝光。
@router.post("/set_exposure_time", response_class=ORJSONResponse)
def get_projection(time: float = 0.0):
    """将视频流作为流响应返回。"""
    set_exposure_time(time)
    return

'''
# 定义一个FastAPI路由, 用于处理视频流请求。
@router.get("/get_projection", response_class=ORJSONResponse)
def get_projection():
    """将视频流作为流响应返回。"""
    data = get_axis_data()
    return ORJSONResponse(data)
'''

@router.get("/start")
def start():
    app = main.app
    app.state.camera.start()
    #camera.start()
    return

@router.get("/close")
def close():
    app = main.app
    app.state.camera.release()
    #camera.release()
    return

@router.get("/start_sample")
def start_sample(backgroundtasks: BackgroundTasks, 
                 q: asyncio.Queue = Depends(get_queue),
                 camera: Camera = Depends(get_camera)):
    global isAddFrame
    isAddFrame = True
    backgroundtasks.add_task(add_frame, q, camera)
    return

@router.get("/start_sample")
def start_sample():
    global isAddFrame
    isAddFrame = False
    return

async def generate_frames(q: asyncio.Queue = Depends(get_queue),
                          type = "8_bits"):
    application = main.app
    camera = application.state.camera
    #global application
    while isAddFrame:
        # 从视频流中读取帧。
        frame = cv2.cvtColor(q.get(), cv2.COLOR_GRAY2BGR)
        # 将帧转换为JPEG格式。
        ret, buffer = cv2.imencode(".jpg", frame)
        # 将JPEG数据转换为字节字符串，并将其作为流响应返回。
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")