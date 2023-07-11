import cv2

from scipy.ndimage import gaussian_filter
from scipy.signal import find_peaks, peak_widths

import asyncio
import numpy as np
from typing import Union
from loguru import logger
from app.db.schemas import ParamsBase
from starlette.requests import Request
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, ORJSONResponse
from app.core.Camera import Camera

FWHM: list[int] = [0, 0, 0, 0]
isAddFrame: bool = False
isCrossLine: bool = False
left_bound: float = 0.0
right_bound: float = 100.0
axis_list: list[dict] = []

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

async def generate_frames(camera: Camera,
                          type = "8_bits",
                          cmap: int = -1) -> bytes:
    global isAddFrame
    while True:
        # 从视频流中读取帧。
        
        if not isAddFrame:
            break

        data = camera.get_frame() if type == '8_bits' else camera.raw_frame()

        if type == "12_bits":
            data = data >> 4

        global left_bound, right_bound
        calcu_axis_data(data, left_bound, right_bound)

        frame = cv2.cvtColor(data, cv2.COLOR_GRAY2BGR)
        if cmap >=0:
            frame = cv2.applyColorMap(frame, cmap)
        # 将帧转换为JPEG格式。
        ret, buffer = cv2.imencode(".jpg", frame)
        # 将JPEG数据转换为字节字符串，并将其作为流响应返回。
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
        
def calcu_axis_data(data: np.ndarray, 
                  x1: float = 0.0, x2: float = 100.0) -> list[dict]:

    shape_1 = data.shape[1]
    index_1 = np.arange(shape_1)

    data_1 = np.sum(data[int(x1/100*(shape_1 - 1)):int(x2/100*(shape_1 - 1))], axis = 0).flatten()
    data_1 = data_1/np.nanmax(data_1)
    global axis_list 
    axis_list = [{"index_0": index_1[i], "axis_0": data_1[i]} for i in range(index_1.shape[0])]

    peaks, _ = find_peaks(data_1, rel_height = 1.0)
    results_half = peak_widths(data_1, peaks, rel_height = 0.5)
    global FWHM
    FWHM = results_half
    return

def get_axis_data() -> list:
    global axis_list
    global FWHM
    return [axis_list, 
            {"width": FWHM[0], 
            "height": FWHM[1], 
            "x1": FWHM[2], 
            "x2": FWHM[3]}]

def get_fwhm() -> list[int]:
    
    global FWHM
    results_half = FWHM

    return {"width": results_half[0], 
            "height": results_half[1], 
            "x1": results_half[2], 
            "x2": results_half[3]}

'''
def calculate_fwhm(data: np.ndarray, x1: float = 0.0, x2: float = 100.0) -> list[int]:
    shape_1 = data.shape[1]
    data_1 = np.sum(data[int(x1/100*(shape_1 - 1)):int(x2/100*(shape_1 - 1))], axis = 0).flatten()
    data_1 = data_1/np.nanmax(data_1)
    peaks, _ = find_peaks(data_1, rel_height = 1.0)
    results_half = peak_widths(data_1, peaks, rel_height = 0.5)
    return results_half
'''

'''
def set_exposure_time(camera: Camera, 
                      time: float = 200000):
    camera.pause()
    camera.CameraSetExposureTime(time)
    camera.play()
    return
'''


def set_cross_line(camera: Camera, 
                   x: int = 0, 
                   y: int = 0):
    
    x = int(camera.cap.sResolutionRange.iWidthMax/2)
    y = int(camera.cap.sResolutionRange.iHeightMax/2)
    camera.pause()
    camera.CameraSetCrossLine(0, x, y)
    camera.play()
    return

def set_camera_parameters(camera: Camera, 
                          params: ParamsBase):
    
    params_dict = params.dict()

    func_dict = {
        "gain": camera.CameraSetGain,
        "gamma": camera.CameraSetGamma,
        "contrast": camera.CameraSetContrast,
        "exposure_time": camera.CameraSetExposureTime
    }

    camera.pause()
    for param, value in params_dict.items():
        if value is not None:
            logger.info(f"set {param} as {value}")
            func_dict[param](value)
    camera.play()
    return

router = APIRouter()

##################################################################

"""将视频流作为流响应返回。"""
@router.get("/frame")
async def get_8_bits_img(camera: Camera = Depends(get_camera), 
                         type: str = "8_bits", 
                         cmap: int = -1):
    
    data = generate_frames(camera, type, cmap)
    return StreamingResponse(data,
                    media_type="multipart/x-mixed-replace;boundary=frame")

# 一维投影。
@router.get("/get_projection", response_class=ORJSONResponse)
def get_projection(camera: Camera = Depends(get_camera), 
                   x1: float = 0.0, x2: float = 100.0):
    global left_bound, right_bound
    left_bound, right_bound = x1, x2
    data = get_axis_data()
    return ORJSONResponse(data)


# 一维投影。
@router.get("/get_fwhm", response_class=ORJSONResponse)
def get_fwhm_value():

    data = get_fwhm()

    return ORJSONResponse(data)

# Cross Line。
@router.get("/set_cross_line")
def add_cross_line(camera: Camera = Depends(get_camera), 
                   x1: float = 0.0, x2: float = 100.0):

    set_cross_line(camera, x1, x2)
    return

'''
# 设置相机曝光。
@router.post("/set_exposure_time", response_class=ORJSONResponse)
def set_camera_exposure(camera: Camera = Depends(get_camera),
                   time: float = 0.0):

    global isAddFrame
    isAddFrame = False
    set_exposure_time(camera, time)
    return
'''


# 设置相机曝光。
@router.post("/set_camera_parameters")
def set_camera(*,
                camera: Camera = Depends(get_camera),
                params: ParamsBase):

    global isAddFrame
    isAddFrame = False
    set_camera_parameters(camera, params)
    isAddFrame = True
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
def start_sample():
    global isAddFrame
    isAddFrame = True
    return

@router.get("/stop_sample")
def stop_sample():
    global isAddFrame
    isAddFrame = False
    return
