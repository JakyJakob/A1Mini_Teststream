import socket
import ssl
import struct
import time
import tkinter as tk
from PIL import Image, ImageTk
import threading
import io

class A1Streamer:
    def __init__(self, root):
        self.root = root
        self.root.title("Bambu A1 Mini Streamer Pro")
        self.root.geometry("800x650")
        self.root.configure(bg="#121212")

        # Config (wird in der GUI eingegeben)
        self.ip_var = tk.StringVar(value="192.168.178.82")
        self.code_var = tk.StringVar(value="ACCESS_CODE")

        self.setup_ui()
        self.running = False

    def setup_ui(self):
        header = tk.Frame(self.root, bg="#1a1a1a", pady=10)
        header.pack(fill="x")
        
        tk.Label(header, text="IP:", fg="white", bg="#1a1a1a").pack(side="left", padx=5)
        tk.Entry(header, textvariable=self.ip_var, width=15).pack(side="left", padx=5)
        tk.Label(header, text="Code:", fg="white", bg="#1a1a1a").pack(side="left", padx=5)
        tk.Entry(header, textvariable=self.code_var, width=12, show="*").pack(side="left", padx=5)
        
        self.btn = tk.Button(header, text="START", command=self.toggle, bg="#28a745", fg="white")
        self.btn.pack(side="left", padx=20)

        self.canvas = tk.Label(self.root, bg="black")
        self.canvas.pack(expand=True, fill="both", pady=10)

    def toggle(self):
        if not self.running:
            self.running = True
            self.btn.config(text="STOP", bg="red")
            threading.Thread(target=self.stream_logic, daemon=True).start()
        else:
            self.running = False
            self.btn.config(text="START", bg="#28a745")

    def stream_logic(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        while self.running:
            try:
                with socket.create_connection((self.ip_var.get(), 6000), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=self.ip_var.get()) as ssock:
                        # Auth-Paket nach synman/bambu-go2rtc (0x44 Bytes)
                        username = b"bblp".ljust(32, b'\x00')
                        password = self.code_var.get().encode().ljust(32, b'\x00')
                        auth = struct.pack("<IIII32s32s", 68, 0x3000, 0, 0, username, password)
                        ssock.sendall(auth)

                        buffer = b""
                        while self.running:
                            while len(buffer) < 16:
                                chunk = ssock.recv(32768)
                                if not chunk: break
                                buffer += chunk
                            
                            payload_size = struct.unpack("<I", buffer[:4])[0]
                            buffer = buffer[16:]
                            
                            while len(buffer) < payload_size:
                                buffer += ssock.recv(32768)
                            
                            img_data = buffer[:payload_size]
                            buffer = buffer[payload_size:]

                            if img_data.startswith(b'\xff\xd8'):
                                img = Image.open(io.BytesIO(img_data))
                                # Seitenverhältnis beibehalten beim Resizen
                                img.thumbnail((800, 600))
                                photo = ImageTk.PhotoImage(img)
                                self.canvas.config(image=photo)
                                self.canvas.image = photo
            except:
                time.sleep(2)

if __name__ == "__main__":
    root = tk.Tk()
    app = A1Streamer(root)
    root.mainloop()
