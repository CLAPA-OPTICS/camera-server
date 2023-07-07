import mvsdk
import asyncio
import numpy as np

class Camera(object):
	def __init__(self):
		super(Camera, self).__init__()
		self.pFrameBuffer = 0
		self.quit = False
		#self.buffer = asyncio.Queue()
		self.main()

	def main(self):
		# 枚举相机
		DevList = mvsdk.CameraEnumerateDevice()
		nDev = len(DevList)
		if nDev < 1:
			print("No camera was found!")
			return

		for i, DevInfo in enumerate(DevList):
			print("{}: {} {}".format(i, DevInfo.GetFriendlyName(), DevInfo.GetPortType()))
		i = 0 if nDev == 1 else int(input("Select camera: "))
		DevInfo = DevList[i]
		print(DevInfo)

		# 打开相机
		hCamera = 0
		try:
			hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
		except mvsdk.CameraException as e:
			print("CameraInit Failed({}): {}".format(e.error_code, e.message) )
			return

		self.hCamera = hCamera

		# 获取相机特性描述
		cap = mvsdk.CameraGetCapability(hCamera)

		# 判断是黑白相机还是彩色相机
		monoCamera = (cap.sIspCapacity.bMonoSensor != 0)

		# 黑白相机让ISP直接输出MONO数据，而不是扩展成R=G=B的24位灰度
		if monoCamera:
			mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
		else:
			mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)

		# 相机模式切换成连续采集
		mvsdk.CameraSetTriggerMode(hCamera, 0)

		# 手动曝光，曝光时间30ms
		mvsdk.CameraSetAeState(hCamera, 0)
		mvsdk.CameraSetExposureTime(hCamera, 30 * 1000)

		# Set Type
		#mvsdk.CameraPause(self.hCamera)
		#temp = mvsdk.CameraSetMediaType(hCamera, 1)
		#if temp != 0:
		#	self.CameraDepth = mvsdk.CameraGetMediaType(hCamera)
		#else:
		#	self.CameraDepth = 1

		ret = mvsdk.CameraSetMediaType(hCamera, 1)
		if ret == 0:
			self.isRawData = True
		#cap = mvsdk.CameraGetCapability(hCamera)

		# 让SDK内部取图线程开始工作
		mvsdk.CameraPlay(hCamera)

		# 计算RGB buffer所需的大小，这里直接按照相机的最大分辨率来分配
		FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)

		# 分配RGB buffer，用来存放ISP输出的图像
		# 备注：从相机传输到PC端的是RAW数据，在PC端通过软件ISP转为RGB数据（如果是黑白相机就不需要转换格式，但是ISP还有其它处理，所以也需要分配这个buffer）
		self.pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)

	def release(self):
		# 关闭相机
		mvsdk.CameraUnInit(self.hCamera)
		# 释放帧缓存
		mvsdk.CameraAlignFree(self.pFrameBuffer)

	def get_frame(self):
		hCamera = self.hCamera
		pFrameBuffer = self.pFrameBuffer
		pRawData, FrameHead = mvsdk.CameraGetImageBuffer(hCamera, 200)
		'''
		if len(self.stack)> 0:
			self.stack.pop()
			mvsdk.CameraSaveImage(hCamera, './raw_16', pRawData, FrameHead, mvsdk.FILE_RAW_16BIT, 100)
			apiData = {
				"width": 1280, #FrameHead.iWidth
				"height": 960, #FrameHead.iHeight
				"depth": "8bit" if self.isRawData else "12bit",
				}
			with open('./config.yml', 'w', encoding='utf-8') as f:
				yaml.dump(data=apiData, stream=f, allow_unicode=True)
		'''
		mvsdk.CameraImageProcess(hCamera, pRawData, pFrameBuffer, FrameHead)
		mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)
		
		# 此时图片已经存储在pFrameBuffer中，对于彩色相机pFrameBuffer=RGB数据，黑白相机pFrameBuffer=8位灰度数据
		# 把pFrameBuffer转换成opencv的图像格式以进行后续算法处理
		frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer)
		frame = np.frombuffer(frame_data, dtype=np.uint8)
		frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3) )
		return frame

	### Save RAW Data ###
	def raw_frame(self):
		hCamera = self.hCamera
		#pFrameBuffer = self.pFrameBuffer
		pRawData, FrameHead = mvsdk.CameraGetImageBuffer(hCamera, 200)
		mvsdk.CameraSaveImage(hCamera, '.cache/raw_16',
			pRawData, FrameHead, mvsdk.FILE_RAW_16BIT, 100)
		mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)
		frame = np.fromfile(".cache/raw_16.RAW", dtype = "uint16").reshape(FrameHead.iHeight, 
							FrameHead.iWidth, 1)/2**4
		frame = np.asarray(frame[::-1, :], dtype=np.uint16)
		return frame

	######
	async def run(self):
		while True:
			await self.buffer.put(self.get_frame())
	
	######
	async def from_buffer(self):
		await self.buffer.get()

'''
def reconstruct():
	with open('./config.yml', 'r', encoding='utf-8') as f:
		config = yaml.load(f.read(), Loader=yaml.FullLoader)

	frame = np.fromfile("raw_16.RAW", dtype = "uint16").reshape(config["height"], 
						config["width"], 1)/2**8
	
	frame = np.asarray(frame[::-1, :], dtype=np.uint16)
	return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
'''
