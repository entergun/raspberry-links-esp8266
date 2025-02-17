import cv2
import numpy as np
import requests  # 用于发送HTTP请求到ESP8266
from requests.exceptions import RequestException  # 导入异常处理模块
import time  # 导入时间模块用于延时
import os  # 用于环境变量设置

# 设置环境变量来抑制Qt警告
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"

"""
这个程序用于通过摄像头检测红色和蓝色物体，
并根据检测结果向ESP8266发送控制指令来控制舵机运动
"""

# 颜色阈值（HSV格式）
red_lower = np.array([0, 120, 70])
red_upper = np.array([10, 255, 255])
blue_lower = np.array([100, 150, 50])
blue_upper = np.array([130, 255, 255])

MIN_CONTOUR_AREA = 1000  # 设置最小轮廓面积阈值，用于过滤噪声
ESP8266_URL = "http://192.168.137.134"  # ESP8266的IP地址，移除@符号
REQUEST_TIMEOUT = 2.0  # 增加超时时间到2秒，给舵机动作留出足够时间
COMMAND_INTERVAL = 1.5  # 增加命令发送间隔到1.5秒，因为舵机需要时间完成动作
last_command_time = 0  # 上次发送命令的时间

# 初始化摄像头
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("错误：无法打开摄像头")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 设置分辨率宽度
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # 设置分辨率高度
cap.set(cv2.CAP_PROP_FPS, 30)  # 设置帧率
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 设置缓冲区大小为1，减少延迟

# 创建窗口并设置属性
cv2.namedWindow('Frame', cv2.WINDOW_AUTOSIZE)
cv2.moveWindow('Frame', 0, 0)  # 将窗口移动到屏幕左上角


def send_command(command):
    """发送HTTP请求到ESP8266，带有超时和错误处理"""
    global last_command_time
    current_time = time.time()

    # 检查是否达到发送间隔时间
    if current_time - last_command_time < COMMAND_INTERVAL:
        return False

    try:
        # 设置超时时间和重试次数
        url = f"{ESP8266_URL}/{command}"  # URL格式：http://192.168.137.134/up 或 http://192.168.137.134/down
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={'Connection': 'close'}  # 添加连接关闭头
        )
        if response.status_code == 200:  # 检查响应状态码
            print(f"发送请求成功: {url}")  # 打印成功信息
            last_command_time = current_time
            return True
        else:
            print(f"请求失败，状态码: {response.status_code}")  # 打印失败信息
            return False
    except RequestException as e:
        print(f"发送命令失败: {str(e)}")  # 打印具体错误信息
        return False


while True:
    # 清空缓冲区，只读取最新帧
    for _ in range(int(cap.get(cv2.CAP_PROP_BUFFERSIZE))):  # 将浮点数转换为整数
        cap.grab()
    ret, frame = cap.read()  # 读取最新帧

    if not ret:
        print("无法获取摄像头画面")  # 添加错误提示
        break

    # 缩放图像以提高处理速度
    frame = cv2.resize(frame, (320, 240))  # 将图像缩小一半处理
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 检测红色
    red_mask = cv2.inRange(hsv, red_lower, red_upper)
    red_contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 检测蓝色
    blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
    blue_contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 判断颜色并发送指令
    red_detected = False
    blue_detected = False

    # 检查红色物体
    for contour in red_contours:
        if cv2.contourArea(contour) > MIN_CONTOUR_AREA:  # 只有当轮廓面积大于阈值时才认为检测到红色
            red_detected = True
            break

    # 检查蓝色物体
    for contour in blue_contours:
        if cv2.contourArea(contour) > MIN_CONTOUR_AREA:  # 只有当轮廓面积大于阈值时才认为检测到蓝色
            blue_detected = True
            break

    if red_detected:
        if send_command("up"):  # 发送抬头指令给ESP8266
            print("Red detected, send UP command")  # 在终端打印检测到红色的信息
    elif blue_detected:
        if send_command("down"):  # 发送低头指令给ESP8266
            print("Blue detected, send DOWN command")  # 在终端打印检测到蓝色的信息

    # 显示实时画面（可选）
    cv2.imshow('Frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
