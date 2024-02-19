from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
import socket
import json
from threading import Thread
from datetime import datetime

HTTP_PORT = 8000
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        # Сама маршрутизація у нас виконана за допомогою вкладених інструкцій if.
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    # Для відповіді браузеру ми використовуємо метод send_html_file:
    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    # Функція для надсилання статичних ресурсів
    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def save_json(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    # Завантаження вмісту файлу, якщо він існує
    try:
        with open("storage/data.json", "r") as file:
            json_data = json.load(file)
    except:
        json_data = {}
    print(json_data)
    try:
        parse_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        json_data[time] = parse_dict
        print(json_data)
        with open('storage/data.json', 'w', encoding='utf-8') as file:
            json.dump(json_data, file, ensure_ascii=False, indent=4)
    except ValueError:
        print("Errorr")


def run_socket(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(1024)
            print(f"Socket received {address}: {data.decode()}")
            save_json(data)

    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        sock.close()


def run_http(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = (HTTP_HOST, HTTP_PORT)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    server = Thread(target=run_http)
    server.start()

    server_socket = Thread(target=run_socket, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()