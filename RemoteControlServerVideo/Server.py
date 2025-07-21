import cv2
import socket
import pickle
import struct
import threading

def handle_client_connection(client_socket):
    payload_size = struct.calcsize("L")
    try:
        while True:
            # Receive the message size
            packed_msg_size = client_socket.recv(payload_size)
            if not packed_msg_size:
                break

            msg_size = struct.unpack("L", packed_msg_size)[0]

            # Receive the full message based on the message size
            frame_data = b''
            while len(frame_data) < msg_size:
                packet = client_socket.recv(msg_size - len(frame_data))
                if not packet:
                    return  # Connection has been lost
                frame_data += packet

            # Attempt to unpickle and detect type of data
            try:
                frame = pickle.loads(frame_data)
                cv2.imshow('Server Video', frame)
            except Exception as e:
                try:
                    # Assume it is a key press if it fails to load as a frame
                    key_press = frame_data.decode()
                    print("Key Pressed:", key_press)
                except UnicodeDecodeError:
                    print("Failed to decode non-frame data:", frame_data)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cv2.destroyAllWindows()
        client_socket.close()

# Set up server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('192.168.31.217', 8050))
server_socket.listen(10)
print("Server is listening for incoming connections...")

while True:
    client_socket, client_address = server_socket.accept()
    print(f"[*] Accepted connection from {client_address}")
    threading.Thread(target=handle_client_connection, args=(client_socket,)).start()
