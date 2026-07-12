"""
server.py
---------
A tiny backend built with ONLY the Python standard library.

Serves:
    http://localhost:8000/

API:
    POST /api/chat
"""

import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from automotive_ai.chat_gpu_frontend import AutomotiveChatbot

HOST = "localhost"
PORT = 8000

FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "frontend"
)

# Create chatbot ONCE
print("Initializing Automotive Chatbot...")
bot = AutomotiveChatbot()

# In-memory conversation history
HISTORY = []

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}


def _now():
    return datetime.now().strftime("%H:%M")


class AppHandler(BaseHTTPRequestHandler):

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        self.wfile.write(body)

    def _serve_static(self, path):

        if path in ("", "/"):
            path = "/index.html"

        safe_path = os.path.normpath(path.lstrip("/"))
        full_path = os.path.join(FRONTEND_DIR, safe_path)

        if (
            not full_path.startswith(FRONTEND_DIR)
            or not os.path.isfile(full_path)
        ):
            self._send_json(404, {"error": "Not found"})
            return

        ext = os.path.splitext(full_path)[1]
        content_type = CONTENT_TYPES.get(
            ext,
            "application/octet-stream"
        )

        with open(full_path, "rb") as f:
            body = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)

    def do_OPTIONS(self):

        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )
        self.end_headers()

    def do_GET(self):

        if self.path == "/api/history":
            self._send_json(200, {"history": HISTORY})
            return

        self._serve_static(self.path)

    def do_POST(self):

        if self.path != "/api/chat":
            self._send_json(404, {"error": "Unknown endpoint"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            data = json.loads(raw or b"{}")

        except (ValueError, json.JSONDecodeError):
            self._send_json(
                400,
                {"error": "Invalid JSON body."}
            )
            return

        message = data.get("message", "").strip()

        if not message:
            self._send_json(
                400,
                {"error": "Message cannot be empty."}
            )
            return

        try:

            # Call chatbot
            result = bot.chat(message)

            user_entry = {
                "sender": "user",
                "text": message,
                "time": _now()
            }

            bot_entry = {
                "sender": "bot",
                "text": result["answer"],
                "sources": result["sources"],
                "time": _now()
            }

            HISTORY.append(user_entry)
            HISTORY.append(bot_entry)

            self._send_json(
                200,
                {
                    "reply": bot_entry
                }
            )

        except Exception as e:
            self._send_json(
                500,
                {"error": str(e)}
            )

    def log_message(self, fmt, *args):
        print(f"{self.command} {self.path}")


def main():

    server = ThreadingHTTPServer(
        (HOST, PORT),
        AppHandler
    )

    print(f"Server running at http://{HOST}:{PORT}")

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nStopping server...")

    finally:
        print("Closing chatbot...")
        bot.close()
        server.shutdown()


if __name__ == "__main__":
    main()