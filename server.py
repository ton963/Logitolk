import socket
import threading

HOST = '0.0.0.0'
PORT = 8082

clients = []
clients_lock = threading.Lock() 

def broadcast(data):
    """Надсилає дані всім підключеним клієнтам."""
    with clients_lock:
        for client in list(clients):
            try:
                client.sendall(data)
            except (socket.error, ConnectionResetError, BrokenPipeError):
                print(f"Broadcast: Клієнт {client.getpeername()} від'єднався, видаляємо.")
                try:
                    clients.remove(client)
                    client.close() 
                except ValueError:
                    pass 
            except Exception as e:
                print(f"*** Broadcast: Невідома помилка при відправці: {e}")


def handle_client(client_socket):
    global clients
    try:
        client_addr = client_socket.getpeername()
        print(f"Обробка клієнта: {client_addr}")
    except Exception as e:
        print(f"Не вдалося отримати адресу клієнта: {e}")
        client_addr = "невідома адреса"

    try:
        while True:
            data = client_socket.recv(4096)
            
            if not data:
                print(f"Клієнт {client_addr} коректно від'єднався (recv_empty).")
                break
            
            print(f"Отримано від {client_addr}: {data.decode('utf-8', errors='ignore')[:70]}...") # Логуємо
            broadcast(data)
            
    except (socket.error, ConnectionResetError, BrokenPipeError):
        print(f"Клієнт {client_addr} раптово від'єднався (connection_error).")
    except Exception as e:
        print(f"*** Критична помилка в handle_client для {client_addr}: {e}")
    finally:
        with clients_lock:
            if client_socket in clients:
                print(f"Видаляємо {client_addr} зі списку.")
                clients.remove(client_socket)
        
        client_socket.close()
        print(f"З'єднання з {client_addr} закрито.")


def main():
    global clients
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
    except Exception as e:
        print(f"*** Не вдалося запустити сервер на {HOST}:{PORT}. Помилка: {e}")
        return

    server_socket.listen(5)
    print(f"Сервер запущено на {HOST}:{PORT}")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"\nПідключився новий клієнт: {addr}")
            
            with clients_lock:
                clients.append(client_socket)

            t = threading.Thread(target=handle_client, args=(client_socket,))
            t.daemon = True
            t.start()
            
    except KeyboardInterrupt:
        print("\nСервер зупиняється...")
    finally:
        with clients_lock:
            for client in clients:
                client.close()
        server_socket.close()
        print("Сервер зупинено.")

if __name__ == "__main__":
    main()
