import socket

HOST = '127.0.0.1'
PORT = 8266

def start_mock():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Mock ESP8266 listening on {HOST}:{PORT}...")
        
        while True:
            conn, addr = s.accept()
            with conn:
                try:
                    data = conn.recv(1024)
                    if not data:
                        continue
                    
                    # ESP8266 typical HTTP response
                    response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: text/html\r\n"
                        "Server: ESP8266WebServer/1.0\r\n"
                        "Connection: close\r\n"
                        "\r\n"
                        "<html><body><h1>Hello from ESP8266 Sensor Node!</h1></body></html>"
                    )
                    conn.sendall(response.encode('utf-8'))
                except Exception:
                    pass

if __name__ == "__main__":
    start_mock()
