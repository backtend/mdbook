import socket
import struct
import cv2
import numpy as np

def start_controller():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 9999))
    
    # 鼠标点击事件回调
    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # 发送点击坐标给受控端
            client_socket.send(f"{x},{y}".encode())

    cv2.namedWindow('Remote Desktop')
    cv2.setMouseCallback('Remote Desktop', on_mouse)

    data = b""
    payload_size = struct.calcsize(">L")

    try:
        while True:
            # 1. 接收图片长度
            while len(data) < payload_size:
                data += client_socket.recv(4096)
            
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]

            # 2. 接收图片内容
            while len(data) < msg_size:
                data += client_socket.recv(4096)
            
            frame_data = data[:msg_size]
            data = data[msg_size:]

            # 3. 解码并显示
            frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            cv2.imshow('Remote Desktop', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cv2.destroyAllWindows()
        client_socket.close()

if __name__ == "__main__":
    start_controller()