import tkinter as tk
from tkinter import messagebox
import socket
import struct
import numpy as np
import cv2
from PIL import Image, ImageTk
from pynput import keyboard


class DroneClientApp:
    def __init__(self, master):
        self.master = master
        master.title("Drone Client Interface")
        master.geometry("600x500")
        master.configure(bg="#e3f2fd")  # Subtle blue background

        # Custom Button Styles (simulated round)
        self.round_button_style = {"relief": "solid", "bd": 0, "highlightthickness": 0, "bg": "#0288d1", "fg": "white",
                                   "font": ("Arial", 12, "bold")}

        # Status Frame
        self.status_frame = tk.Frame(master, bg="#e3f2fd")
        self.status_frame.pack(pady=10)

        self.status_label = tk.Label(self.status_frame, text="Client Status: Not Connected", bg="#e3f2fd")
        self.status_label.pack()

        # IP Selection Frame
        self.ip_selection_frame = tk.Frame(master, bg="#e3f2fd")
        self.ip_selection_frame.pack(pady=10)

        self.ip_label = tk.Label(self.ip_selection_frame, text="Enter Server IP Address:", bg="#e3f2fd")
        self.ip_label.pack()

        self.server_ip_entry = tk.Entry(self.ip_selection_frame, width=40)
        self.server_ip_entry.pack()

        # Connection Frame
        self.connection_frame = tk.Frame(master, bg="#e3f2fd")
        self.connection_frame.pack(pady=10)

        self.connect_button = tk.Button(self.connection_frame, text="Connect", command=self.connect,
                                        **self.round_button_style)
        self.connect_button.pack(side=tk.LEFT, padx=5)

        self.disconnect_button = tk.Button(self.connection_frame, text="Disconnect", command=self.disconnect,
                                           state=tk.DISABLED, **self.round_button_style)
        self.disconnect_button.pack(side=tk.LEFT, padx=5)

        # Video Display Area
        self.video_label = tk.Label(master)
        self.video_label.pack()

        # Keyboard Listener
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

        # Client Socket
        self.client_socket = None

    def connect(self):
        server_ip = self.server_ip_entry.get().strip()
        if not server_ip:
            messagebox.showwarning("Missing IP", "Please enter the server's IP address.")
            return
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, 8040))
            self.status_label.config(text="Client Status: Connected")
            self.connect_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)
            self.receive_video_frames()
        except Exception as e:
            messagebox.showerror("Connection Failed", str(e))

    def disconnect(self):
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            self.status_label.config(text="Client Status: Disconnected")
            self.connect_button.config(state=tk.NORMAL)
            self.disconnect_button.config(state=tk.DISABLED)
            self.video_label.image = None

    def receive_video_frames(self):
        if self.client_socket:
            payload_size = struct.calcsize("!Q")
            packed_msg_size = self.client_socket.recv(payload_size)
            if not packed_msg_size:
                return

            msg_size = struct.unpack("!Q", packed_msg_size)[0]
            frame_data = b''
            while len(frame_data) < msg_size:
                packet = self.client_socket.recv(msg_size - len(frame_data))
                if not packet:
                    return  # Connection has been lost
                frame_data += packet

            frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            frame = Image.fromarray(frame)
            frame = ImageTk.PhotoImage(frame)
            self.video_label.config(image=frame)
            self.video_label.image = frame

            self.master.after(10, self.receive_video_frames)

    def on_press(self, key):
        try:
            if hasattr(key, 'char') and key.char and self.client_socket:
                key_data = key.char.encode()
                message_size = struct.pack("!Q", len(key_data))
                self.client_socket.sendall(message_size + key_data)
        except Exception as e:
            print(f"Error sending key data: {e}")


def main():
    root = tk.Tk()
    app = DroneClientApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
