import tkinter as tk
from tkinter import scrolledtext
import socket
import struct
import threading
import psutil
from djitellopy import Tello

class DroneServerApp:
    def __init__(self, master):
        self.master = master
        master.title("Drone Server Interface")
        master.geometry("600x400")
        master.configure(bg="#e3f2fd")  # Subtle blue background

        # Custom Button Styles (simulated round)
        self.round_button_style = {"relief": "solid", "bd": 0, "highlightthickness": 0, "bg": "#0288d1", "fg": "white", "font": ("Arial", 12, "bold")}

        # Status Frame
        self.status_frame = tk.Frame(master, bg="#e3f2fd")
        self.status_frame.pack(pady=10)

        self.status_label = tk.Label(self.status_frame, text="Server Status: Not Started", bg="#e3f2fd")
        self.status_label.pack()

        # IP Selection Frame
        self.ip_selection_frame = tk.Frame(master, bg="#e3f2fd")
        self.ip_selection_frame.pack(pady=10)

        self.ip_label = tk.Label(self.ip_selection_frame, text="Select IP Address to Host On:", bg="#e3f2fd")
        self.ip_label.pack()

        self.available_ips = self.get_ipv4_addresses()
        self.selected_ip = tk.StringVar(value=self.available_ips[0] if self.available_ips else "No IPs found")
        self.ip_dropdown = tk.OptionMenu(self.ip_selection_frame, self.selected_ip, *self.available_ips)
        self.ip_dropdown.pack()

        # Server Active Indicator
        self.server_indicator = tk.Canvas(self.status_frame, width=20, height=20, bg="#e3f2fd", highlightthickness=0)
        self.indicator_circle = self.server_indicator.create_oval(2, 2, 18, 18, fill="red")  # Red by default (inactive)
        self.server_indicator.pack()

        # Button Frame
        self.button_frame = tk.Frame(master, bg="#e3f2fd")
        self.button_frame.pack(pady=10)

        self.start_button = tk.Button(self.button_frame, text="Start Server", command=self.start_server, **self.round_button_style)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(self.button_frame, text="Stop Server", command=self.stop_server, state=tk.DISABLED, **self.round_button_style)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Log Area
        self.log_area = scrolledtext.ScrolledText(master, height=15, state='disabled')
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # Server and drone initialization
        self.server_socket = None
        self.drone = Tello()
        self.drone.connect()
        self.drone.streamon()

    def log_message(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + '\n')
        self.log_area.config(state=tk.DISABLED)
        self.log_area.yview(tk.END)

    def get_ipv4_addresses(self):
        try:
            interfaces = psutil.net_if_addrs()
            ipv4_addresses = []

            for interface_name, addresses in interfaces.items():
                for address in addresses:
                    if address.family == socket.AF_INET:
                        ipv4_addresses.append(address.address)

            return ipv4_addresses
        except Exception as e:
            return []

    def start_server(self):
        try:
            selected_ip = self.selected_ip.get()
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((selected_ip, 8040))
            self.server_socket.listen(10)
            self.log_message(f"Server is listening for incoming connections on {selected_ip}...")
            threading.Thread(target=self.accept_clients, daemon=True).start()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="Server Status: Running")
            self.server_indicator.itemconfig(self.indicator_circle, fill="green")
        except Exception as e:
            self.log_message(f"Failed to start server: {str(e)}")
            self.status_label.config(text="Server Status: Error")
            self.server_indicator.itemconfig(self.indicator_circle, fill="red")

    def stop_server(self):
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
            self.log_message("Server stopped.")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="Server Status: Not Started")
            self.server_indicator.itemconfig(self.indicator_circle, fill="red")

    def accept_clients(self):
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                self.log_message(f"Client connected: {addr}")
                frame_read = self.drone.get_frame_read()
                threading.Thread(target=self.send_video_frames, args=(client_socket, frame_read)).start()
                threading.Thread(target=self.receive_commands, args=(client_socket,)).start()
        except Exception as e:
            self.log_message(f"Error accepting clients: {str(e)}")

    def send_video_frames(self, client_socket, frame_read):
        try:
            while True:
                frame = frame_read.frame
                if frame is None:
                    self.log_message("Could not read frame from camera.")
                    break
                _, buffer = cv2.imencode('.jpg', frame)
                serialized_frame = buffer.tobytes()
                message_size = struct.pack("!Q", len(serialized_frame))
                client_socket.sendall(message_size + serialized_frame)
        except socket.error as e:
            self.log_message(f"Socket error in sending frames: {str(e)}")
        finally:
            client_socket.close()
            self.log_message("Video capture and socket closed after sending frames.")

    def receive_commands(self, client_socket):
        payload_size = struct.calcsize("!Q")
        try:
            while True:
                packed_msg_size = client_socket.recv(payload_size)
                if not packed_msg_size:
                    self.log_message("Client has disconnected.")
                    break

                msg_size = struct.unpack("!Q", packed_msg_size)[0]
                command_data = b''
                while len(command_data) < msg_size:
                    packet = client_socket.recv(msg_size - len(command_data))
                    if not packet:
                        self.log_message("Connection lost during command reception.")
                        return  # Connection has been lost
                    command_data += packet

                self.execute_drone_command(command_data.decode())
        finally:
            client_socket.close()
            self.log_message("Socket closed after receiving commands.")

        def execute_drone_command(self, command):
            drone_actions = {
                'o': self.drone.takeoff,
                'l': self.drone.land,
                'w': lambda: self.drone.move_forward(30),
                's': lambda: self.drone.move_back(30),
                'a': lambda: self.drone.move_left(30),
                'd': lambda: self.drone.move_right(30),
                'i': lambda: self.drone.move_up(30),
                'k': lambda: self.drone.move_down(30)
            }
            action = drone_actions.get(command)
            if action:
                action()
                self.log_message(f"Executed drone command: {command}")
            else:
                self.log_message(f"Unknown command: {command}")

def main():
    root = tk.Tk()
    app = DroneServerApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()

