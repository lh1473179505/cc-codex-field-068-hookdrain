from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from hookdrain.core import HookDrain

CORE = HookDrain()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):
        return
    def do_POST(self):
        n=int(self.headers.get("Content-Length") or 0)
        raw=self.rfile.read(n) if n else b""
        result="ignored"
        if self.path.rstrip("/") in ("/hook","") and raw:
            import json
            try:
                result=CORE.apply(json.loads(raw))
            except Exception as exc:
                body=json.dumps({"ok":False,"error":str(exc)}).encode()
                self.send_response(400)
                self.send_header("Content-Type","application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers(); self.wfile.write(body)
                return
        body=json.dumps({"ok":True,"result":result}).encode()
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)

def serve(host="127.0.0.1", port=8768):
    httpd=ThreadingHTTPServer((host,port), Handler)
    print(f"hookdrain fixture endpoint on http://{host}:{port}")
    httpd.serve_forever()
