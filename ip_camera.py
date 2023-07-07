import cv2
import asyncio
import uvicorn
import numpy as np
from Camera import Camera
from fastapi import FastAPI, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse, ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware

# 创建一个FastAPI应用程序。
app = FastAPI()
# 2、声明一个 源 列表；重点：要包含跨域的客户端 源
origins = ["*"]

# 3、配置 CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许访问的源
    allow_credentials=True,  # 支持 cookie
    allow_methods=["*"],  # 允许使用的请求方法
    allow_headers=["*"]  # 允许携带的 Headers
)

# 定义一个辅助函数，用于从RTSP源读取视频流。
async def generate_frames(type = "8_bits"):
    while True:
        # 从视频流中读取帧。
        frame = cv2.cvtColor(camera.get_frame() if type == '8_bits' else camera.raw_frame(), cv2.COLOR_GRAY2BGR)
        # 将帧转换为JPEG格式。
        ret, buffer = cv2.imencode(".jpg", frame)
        # 将JPEG数据转换为字节字符串，并将其作为流响应返回。
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

'''
async def generate_frames_12_bits():
	while True:
		#camera.stack.append(1)
		#camera.get_frame()
		#frame=reconstruct()
		frame = cv2.cvtColor(camera.raw_frame(), cv2.COLOR_GRAY2BGR)
		ret, buffer = cv2.imencode(".jpg", frame)
		yield (b"--frame\r\n"
			   b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
'''

def get_axis_data():
    data = camera.raw_frame()
    index_1 = np.arange(data.shape[1])
    data_1 = np.sum(data, axis = 0)
    data_1 = data_1/np.nanmax(data_1)
    #index_0 = np.arange(data.shape[0])
    #data_0 = np.sum(data, axis = 1)
    return [{"index_0": index_1[i], "axis_0": data_1[i]} for i in range(index_1.shape[0])]

# 定义一个FastAPI路由，用于处理视频流请求。
@app.get("/get_8_bits_img")
async def get_8_bits_img():
    """将视频流作为流响应返回。"""
    return StreamingResponse(generate_frames("8_bits"),
                    media_type="multipart/x-mixed-replace;boundary=frame")

# 定义一个FastAPI路由，用于处理视频流请求。
@app.get("/get_12_bits_img")
async def get_12_bits_img():
    """将视频流作为流响应返回。"""
    return StreamingResponse(generate_frames("12_bits"),
                    media_type="multipart/x-mixed-replace;boundary=frame")

# 定义一个FastAPI路由，用于处理视频流请求。
@app.get("/get_projection", response_class=ORJSONResponse)
async def get_projection():
    """将视频流作为流响应返回。"""
    data = get_axis_data()
    return ORJSONResponse(data)

'''
# 定义一个FastAPI路由, 用于呈现网站页面。
@app.get("/")
async def root():
	html = open("python_demo\index.html", 'r').read()
	return Response(content=html, media_type="text/html")
'''

# 定义一个FastAPI路由，用于呈现网站页面。
@app.get("/clean")
async def root():
    global camera 
    camera.release()
    camera.main()
    return

if __name__ == '__main__':
    camera = Camera()
    #asyncio.run(camera.run())
    uvicorn.run(app=app) #, reload=True, host="127.0.0.1", port=8000)
    camera.release()
