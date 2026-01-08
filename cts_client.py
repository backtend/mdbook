
import socket
import struct
import cv2
import numpy as np
import pyautogui
from mss import mss

# 关闭 PyAutoGUI 的安全故障保险（可选）
pyautogui.FAILSAFE = False

def start_agent():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('127.0.0.1', 9999))
    server_socket.listen(1)
    print("受控端已启动，等待连接...")

    conn, addr = server_socket.accept()
    print(f"控制端 {addr} 已连接")

    with mss() as sct:
        # 仅截取屏幕的一部分（例如 800x600），防止同一台电脑运行时的“套娃”效应太严重
        monitor = {"top": 0, "left": 0, "width": 800, "height": 600}
        
        try:
            while True:
                # 1. 截屏并压缩
                img = np.array(sct.grab(monitor))
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 50])
                data = buffer.tobytes()

                # 2. 发送图片大小和数据
                conn.sendall(struct.pack(">L", len(data)) + data)

                # 3. (非阻塞) 接收简单的点击指令: "x,y"
                conn.setblocking(False)
                try:
                    msg = conn.recv(1024).decode()
                    if msg:
                        x, y = map(int, msg.split(','))
                        pyautogui.click(x, y)
                except BlockingIOError:
                    pass
                conn.setblocking(True)

        except Exception as e:
            print(f"断开连接: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    start_agent()