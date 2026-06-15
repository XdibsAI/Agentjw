import http.server
import socketserver
import os

PORT = 8080
FILE_PATH = "/home/dibs/agentjw/agentjw_remote.apk"

class ReuseTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if os.path.exists(FILE_PATH):
            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.android.package-archive')
            self.send_header('Content-Disposition', 'attachment; filename="agentjw_remote.apk"')
            self.send_header('Content-Length', os.path.getsize(FILE_PATH))
            self.end_headers()
            with open(FILE_PATH, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "File Not Found")

with ReuseTCPServer(("", PORT), Handler) as httpd:
    print(f"Serving {FILE_PATH} at port {PORT}")
    httpd.serve_forever()
