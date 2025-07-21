import cv2
import socket
import struct
import numpy as np
from pynput import keyboard

def receive_video_frames(server_socket):
    payload_size = struct.calcsize("!Q")  # Using unsigned long long in network byte order
    try:
        while True:
            packed_msg_size = server_socket.recv(payload_size)
            if not packed_msg_size:
                break

            msg_size = struct.unpack("!Q", packed_msg_size)[0]
            frame_data = b''
            while len(frame_data) < msg_size:
                packet = server_socket.recv(msg_size - len(frame_data))
                if not packet:
                    return  # Connection has been lost
                frame_data += packet

            frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
            cv2.imshow('Client Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cv2.destroyAllWindows()
        server_socket.close()

def send_key_data(server_socket, key_data):
    message_size = struct.pack("!Q", len(key_data))
    server_socket.sendall(message_size + key_data)

def on_press(key, server_socket):
    try:
        # Filter for characters and convert to string, encode to bytes
        if hasattr(key, 'char') and key.char:
            key_data = key.char.encode()
            send_key_data(server_socket, key_data)
    except Exception as e:
        print(f"Error sending key data: {e}")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect(('192.168.31.217', 8050))  # IP and port of the server

    listener = keyboard.Listener(on_press=lambda key: on_press(key, server_socket))
    listener.start()

    receive_video_frames(server_socket)

    listener.stop()

if __name__ == '__main__':
    main()
