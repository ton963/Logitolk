import base64
import io
import os
import threading
from socket import socket, AF_INET, SOCK_STREAM

from customtkinter import *
from tkinter import filedialog
from PIL import Image

# Вікно реєстрації
class RegisterWindow(CTk):
    def __init__(self):
        super().__init__()
        self.username = None
        self.title('Приєднатися до сервера')
        self.geometry('300x350')

        CTkLabel(self, text='Вхід в LogiTalk', font=('Arial', 20, 'bold')).pack(pady=30)
        self.name_entry = CTkEntry(self, placeholder_text="Введіть ім'я")
        self.name_entry.pack(pady=5, padx=20, fill='x')

        self.host_entry = CTkEntry(self, placeholder_text='Хост:')
        self.host_entry.pack(pady=5, padx=20, fill='x')
        
        self.port_entry = CTkEntry(self, placeholder_text='Порт:')
        self.port_entry.pack(pady=5, padx=20, fill='x')

        self.submit_button = CTkButton(self, text='Приєднатися', command=self.start_chat)
        self.submit_button.pack(pady=10)

        self.error_label = CTkLabel(self, text="", text_color="red")
        self.error_label.pack(pady=5)

    def start_chat(self):
        self.username = self.name_entry.get().strip()
        host = self.host_entry.get().strip() or 'localhost'
        port_str = self.port_entry.get().strip() or '8082'

        if not self.username:
            self.error_label.configure(text="Будь ласка, введіть ім'я")
            return

        try:
            port = int(port_str)
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((host, port))
            
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.send(hello.encode('utf-8'))

            self.destroy() 

            win = MainWindow(self.sock, self.username)
            win.mainloop()

        except Exception as e:
            self.error_label.configure(text=f"Помилка підключення: {e}")


# Головне вікно

class MainWindow(CTk):
    def __init__(self, sock, username): 
        super().__init__()

        self.sock = sock
        self.username = username

        self.geometry('600x500')
        self.title("Chat Client")

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
            threading.Thread(target=self.recv_message, daemon=True).start()
            self.add_message(f"[SYSTEM] Ви увійшли як: {self.username}")
        except Exception as e:
            self.add_message(f"Помилка запуску потоку: {e}")

    def toggle_menu(self):
        if self.is_menu_open:
            self.menu_width = 60
            self.is_menu_open = False
            self.menu_button.configure(text='▶️')
            for widget in self.menu_frame.winfo_children():
                 if widget != self.menu_button:
                    widget.destroy()
            self.menu_button.place(x=5, y=5) 
        else:
            self.menu_width = 200
            self.is_menu_open = True
            self.menu_button.configure(text='◀️')
            self.show_menu_widgets()
        
        self.menu_frame.configure(width=self.menu_width)
        self.redraw_ui()

    def show_menu_widgets(self):
        CTkLabel(self.menu_frame, text='Ваш нік:').pack(pady=(50, 10), padx=10) 
        self.name_entry = CTkEntry(self.menu_frame, placeholder_text="Ваш нік...")
        self.name_entry.insert(0, self.username) 
        self.name_entry.pack(pady=5, padx=10)
        CTkButton(self.menu_frame, text="Зберегти", command=self.save_name).pack(pady=5, padx=10)

    def save_name(self):
        new_name = self.name_entry.get().strip()
        if new_name and new_name != self.username:
            old_name = self.username
            self.username = new_name
            self.add_message(f"[SYSTEM] Ваш нік змінено на: {self.username}")
        elif not new_name:
             self.add_message("[SYSTEM] Ім'я не може бути порожнім.")


    def redraw_ui(self):
        """Оновлює позиції після зміни розміру меню"""
        self.chat_field.place(x=self.menu_width + 10, y=10)
        self.message_entry.place(x=self.menu_width + 10, y=400)
        self.open_img_button.place(x=self.menu_width + 395, y=400)
        self.send_button.place(x=self.menu_width + 450, y=400)
        
        chat_width = 600 - self.menu_width - 20 
        entry_width = chat_width - 105 
        
        self.chat_field.configure(width=chat_width)
        self.message_entry.configure(width=entry_width)


    def add_message(self, text, img=None):
        frame = CTkFrame(self.chat_field, fg_color='#333333')
        frame.pack(pady=5, padx=5, anchor='w', fill='x')
        
        wrap = 580 - self.menu_width - 40

        if img:
            CTkLabel(frame, text=text, image=img, compound='top',
                     text_color='white', wraplength=wrap, justify='left').pack(padx=10, pady=5, anchor='w')
        else:
            CTkLabel(frame, text=text, text_color='white',
                     wraplength=wrap, justify='left').pack(padx=10, pady=5, anchor='w')
        
        self.chat_field._parent_canvas.yview_moveto(1.0)


    def send_message(self):
        msg = self.message_entry.get()
        if msg:
            try:
                self.sock.sendall(f"TEXT@{self.username}@{msg}\n".encode())
            except Exception as e:
                self.add_message(f" Помилка надсилання повідомлення: {e}")
        self.message_entry.delete(0, END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    self.add_message("[SYSTEM] З'єднання з сервером втрачено.")
                    break
                buffer += chunk.decode('utf-8', errors='ignore')

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except Exception as e:
                self.add_message(f"[SYSTEM] Помилка отримання: {e}")
                break
        self.sock.close()

    def handle_line(self, line):
        if not line:
            return
        
        print(f"DEBUG: Отримано рядок: {line[:100]}...") 
        
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
                
                pil_img.thumbnail((300, 300)) 
                
                ctk_img = CTkImage(pil_img, size=pil_img.size)
                self.add_message(f"{author} надіслав(ла) зображення: {filename}", img=ctk_img)
            except Exception as e:
                self.add_message(f"Помилка відображення зображення: {e}")
        else:
            if line.strip():
                self.add_message(line)

    def open_image(self):
        file_name = filedialog.askopenfilename(filetypes=[("Зображення", "*.png;*.jpg;*.jpeg;*.gif")])
        if not file_name:
            return
        try:
            with open(file_name, "rb") as f:
                raw = f.read()
            
            if len(raw) > 5 * 1024 * 1024:
                self.add_message("[SYSTEM] Помилка: Файл занадто великий (макс. 5MB).")
                return

            b64_data = base64.b64encode(raw).decode()
            short_name = os.path.basename(file_name)
            data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
            
            self.sock.sendall(data.encode())

        except Exception as e:
            self.add_message(f"Не вдалося надіслати зображення: {e}")


if __name__ == "__main__":
    app = RegisterWindow()
    app.mainloop()
