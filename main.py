from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import os
import pathlib
from pathlib import Path
from datetime import datetime
import json
from jinja2 import Environment, FileSystemLoader


class HttpHandler(BaseHTTPRequestHandler):

    env = Environment(loader=FileSystemLoader('templates'))

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            static_path = pathlib.Path(pr_url.path[1:])  
            if static_path.exists() and static_path.is_file():
                self.send_static_file(static_path)  
            else:
                self.send_html_file('error.html', 404)

    
    def do_POST(self):
        if self.path == '/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            parsed_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
            
            username = parsed_data.get('name', [''])[0]
            message = parsed_data.get('message', [''])[0]

            timestamp = datetime.now().isoformat()
            entry = {timestamp: {"username": username, "message": message}}

            storage_dir = Path("storage")
            storage_dir.mkdir(exist_ok=True)

            json_file = storage_dir / "data.json"

            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}

            data.update(entry)

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Thank you for your message!</h1>')
        else:
            self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        try:
            with open(filename, 'rb') as fd:
                self.wfile.write(fd.read())
        except FileNotFoundError:
            self.send_html_file('error.html', 404)

    def send_static_file(self, filepath):
        self.send_response(200)
        ext = filepath.suffix
        content_types = {
            '.css': 'text/css',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.js': 'application/javascript',
            '.html': 'text/html',
        }
        self.send_header('Content-type', content_types.get(ext, 'application/octet-stream'))
        self.end_headers()
        try:
            with open(filepath, 'rb') as fd:
                self.wfile.write(fd.read())
        except FileNotFoundError:
            self.send_html_file('error.html', 404)

    def render_read_page(self):
        storage_dir = Path("storage")
        json_file = storage_dir / "data.json"
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                message = json.load(f)
        else:
            message = {}

        template = self.env.get_template('read.html')
        content = template.render(message=message)

        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000) 
    http = server_class(server_address, handler_class)
    try:
        print("Сервер запущено на порту 3000")
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

if __name__ == '__main__':
    run()
