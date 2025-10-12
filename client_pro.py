import base64
import io
import os
import threading
from socket import socket, AF_INET, SOCK_STREAM

from customtkinter import *
from tkinter import filedialog
from PIL import Image


class MainWindow(CTk):
    def __init__(self):
        super().__init__()

        self.geometry('600x500')
        self.title("Chat Client")
        self.username = "Artem"

        self.menu_width = 60
        self.menu_frame = CTkFrame(self, width=self.menu_width, height=500)
        self.menu_frame.place(x=0, y=0)
        self.is_menu_open = False

        self.menu_button = CTkButton(self, text='▶️', width=30, command=self.toggle_menu)
        self.menu_button.place(x=5, y=5)

        self.chat_field = CTkScrollableFrame(self, width=480, height=380)
        self.chat_field.place(x=self.menu_width + 10, y=10)

        self.message_entry = CTkEntry(self, placeholder_text='Введіть повідомлення:', width=380, height=40)
        self.message_entry.place(x=self.menu_width + 10, y=400)

        self.open_img_button = CTkButton(self, text='📂', width=50, height=40, command=self.open_image)
        self.open_img_button.place(x=self.menu_width + 395, y=400)

        self.send_button = CTkButton(self, text='➡️', width=50, height=40, command=self.send_message)
        self.send_button.place(x=self.menu_width + 450, y=400)

        try:
            img = Image.open('Screenshot_1.png')
            self.add_message("Демонстрація зображення:", CTkImage(img, size=(300, 300)))
        except Exception as e:
            self.add_message(f"Не вдалося завантажити демо-зображення: {e}")

        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('localhost', 8082))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.send(hello.encode('utf-8'))
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"Не вдалося підключитися до сервера: {e}")

    def toggle_menu(self):
        if self.is_menu_open:
            self.menu_width = 60
            self.is_menu_open = False
            self.menu_button.configure(text='▶️')
            for widget in self.menu_frame.winfo_children():
                widget.destroy()
        else:
            self.menu_width = 200
            self.is_menu_open = True
            self.menu_button.configure(text='◀️')
            self.show_menu_widgets()
        self.menu_frame.configure(width=self.menu_width)
        self.redraw_ui()

    def show_menu_widgets(self):
        CTkLabel(self.menu_frame, text='Ваш нік:').pack(pady=10)
        self.name_entry = CTkEntry(self.menu_frame, placeholder_text="Ваш нік...")
        self.name_entry.pack(pady=5)
        CTkButton(self.menu_frame, text="Зберегти", command=self.save_name).pack(pady=5)

    def save_name(self):
        new_name = self.name_entry.get().strip()
        if new_name:
            self.username = new_name
            self.add_message(f"Ваш новий нік: {self.username}")

    def redraw_ui(self):
        """Оновлює позиції після зміни розміру меню"""
        self.chat_field.place(x=self.menu_width + 10, y=10)
        self.message_entry.place(x=self.menu_width + 10, y=400)
        self.open_img_button.place(x=self.menu_width + 395, y=400)
        self.send_button.place(x=self.menu_width + 450, y=400)

    def add_message(self, text, img=None):
        frame = CTkFrame(self.chat_field, fg_color='#333333')
        frame.pack(pady=5, anchor='w')
        wrap = 450

        if img:
            CTkLabel(frame, text=text, image=img, compound='top',
                     text_color='white', wraplength=wrap, justify='left').pack(padx=10, pady=5)
        else:
            CTkLabel(frame, text=text, text_color='white',
                     wraplength=wrap, justify='left').pack(padx=10, pady=5)

    def send_message(self):
        msg = self.message_entry.get()
        if msg:
            self.add_message(f"{self.username}: {msg}")
            try:
                self.sock.sendall(f"TEXT@{self.username}@{msg}\n".encode())
            except:
                self.add_message("⚠️ Помилка надсилання повідомлення.")
        self.message_entry.delete(0, END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode('utf-8', errors='ignore')

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except:
                break
        self.sock.close()

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0]

        if msg_type == "TEXT" and len(parts) >= 3:
            author, message = parts[1], parts[2]
            self.add_message(f"{author}: {message}")
        elif msg_type == "IMAGE" and len(parts) >= 4:
            author, filename, b64_img = parts[1], parts[2], parts[3]
            try:
                img_data = base64.b64decode(b64_img)
                pil_img = Image.open(io.BytesIO(img_data))
                ctk_img = CTkImage(pil_img, size=(300, 300))
                self.add_message(f"{author} надіслав(ла) зображення: {filename}", img=ctk_img)
            except Exception as e:
                self.add_message(f"Помилка відображення зображення: {e}")
        else:
            self.add_message(line)

    def open_image(self):
        file_name = filedialog.askopenfilename()
        if not file_name:
            return
        try:
            with open(file_name, "rb") as f:
                raw = f.read()
            b64_data = base64.b64encode(raw).decode()
            short_name = os.path.basename(file_name)
            data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
            self.sock.sendall(data.encode())
            self.add_message(f"{self.username} надіслав(ла) зображення:", CTkImage(Image.open(file_name), size=(300, 300)))
        except Exception as e:
            self.add_message(f"Не вдалося надіслати зображення: {e}")


if __name__ == "__main__":
    win = MainWindow()
    win.mainloop()