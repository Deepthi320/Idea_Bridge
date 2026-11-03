"""
Idea Bridge - HTTP Web & REST API Server
Provides RESTful API endpoints for ideas, comments, collaborators, and stats,
while serving static frontend files from public/.
"""

import json
import mimetypes
import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import db

PORT = int(os.environ.get("PORT", 8000))
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

class IdeaBridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Concise logging
        print(f"[{self.log_date_time_string()}] {self.command} {self.path} - {format % args}")

    def send_json(self, status_code, payload):
        response_data = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_data)

    def send_error_json(self, status_code, error_message):
        self.send_json(status_code, {"error": error_message})

    def parse_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body_bytes = self.rfile.read(content_length)
        try:
            return json.loads(body_bytes.decode("utf-8"))
        except Exception:
            return None

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_HEAD(self):
        self.do_GET(head_only=True)

    def do_GET(self, head_only=False):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # API Endpoints
        if path == "/api/stats":
            stats = db.get_stats()
            self.send_json(200, stats)
            return

        if path == "/api/ideas":
            category = query.get("category", [None])[0]
            stage = query.get("stage", [None])[0]
            search = query.get("search", [None])[0]
            sort_by = query.get("sort", ["votes"])[0]
            ideas = db.list_ideas(category=category, stage=stage, search=search, sort_by=sort_by)
            self.send_json(200, ideas)
            return

        # /api/ideas/<id>
        match = re.match(r"^/api/ideas/(\d+)$", path)
        if match:
            idea_id = int(match.group(1))
            idea = db.get_idea(idea_id)
            if idea:
                self.send_json(200, idea)
            else:
                self.send_error_json(404, "Idea not found")
            return

        # Static file serving
        self.serve_static(path, head_only=head_only)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.parse_body()
        if body is None:
            self.send_error_json(400, "Invalid JSON payload")
            return

        # POST /api/ideas
        if path == "/api/ideas":
            title = body.get("title", "").strip()
            description = body.get("description", "").strip()
            if not title:
                self.send_error_json(400, "Title is required")
                return
            if not description:
                self.send_error_json(400, "Description is required")
                return

            new_idea = db.create_idea(body)
            self.send_json(201, new_idea)
            return

        # POST /api/ideas/<id>/vote
        match_vote = re.match(r"^/api/ideas/(\d+)/vote$", path)
        if match_vote:
            idea_id = int(match_vote.group(1))
            idea = db.get_idea(idea_id)
            if not idea:
                self.send_error_json(404, "Idea not found")
                return
            delta = body.get("delta", 1)
            new_votes = db.vote_idea(idea_id, delta=delta)
            self.send_json(200, {"id": idea_id, "votes": new_votes})
            return

        # POST /api/ideas/<id>/comments
        match_comment = re.match(r"^/api/ideas/(\d+)/comments$", path)
        if match_comment:
            idea_id = int(match_comment.group(1))
            idea = db.get_idea(idea_id)
            if not idea:
                self.send_error_json(404, "Idea not found")
                return
            author = body.get("author_name", "Anonymous").strip() or "Anonymous"
            content = body.get("content", "").strip()
            if not content:
                self.send_error_json(400, "Comment content cannot be empty")
                return
            comment = db.add_comment(idea_id, author, content)
            self.send_json(201, comment)
            return

        # POST /api/ideas/<id>/collaborators
        match_collab = re.match(r"^/api/ideas/(\d+)/collaborators$", path)
        if match_collab:
            idea_id = int(match_collab.group(1))
            idea = db.get_idea(idea_id)
            if not idea:
                self.send_error_json(404, "Idea not found")
                return
            name = body.get("name", "").strip()
            role = body.get("role", "").strip()
            contact = body.get("contact_info", "").strip()
            if not name or not role:
                self.send_error_json(400, "Collaborator name and role are required")
                return
            collab = db.add_collaborator(idea_id, name, role, contact)
            self.send_json(201, collab)
            return

        self.send_error_json(404, "Endpoint not found")

    def do_PUT(self):
        self.handle_update()

    def do_PATCH(self):
        self.handle_update()

    def handle_update(self):
        parsed = urlparse(self.path)
        path = parsed.path
        match = re.match(r"^/api/ideas/(\d+)$", path)
        if not match:
            self.send_error_json(404, "Endpoint not found")
            return

        idea_id = int(match.group(1))
        idea = db.get_idea(idea_id)
        if not idea:
            self.send_error_json(404, "Idea not found")
            return

        body = self.parse_body()
        if body is None:
            self.send_error_json(400, "Invalid JSON payload")
            return

        updated_idea = db.update_idea(idea_id, body)
        self.send_json(200, updated_idea)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        match = re.match(r"^/api/ideas/(\d+)$", path)
        if not match:
            self.send_error_json(404, "Endpoint not found")
            return

        idea_id = int(match.group(1))
        deleted = db.delete_idea(idea_id)
        if deleted:
            self.send_json(200, {"success": True, "deleted_id": idea_id})
        else:
            self.send_error_json(404, "Idea not found")

    def serve_static(self, path, head_only=False):
        if path == "/" or path == "":
            path = "/index.html"

        # Sanitize path to prevent directory traversal
        clean_path = os.path.normpath(path.lstrip("/"))
        file_path = os.path.join(PUBLIC_DIR, clean_path)

        if not os.path.commonpath([PUBLIC_DIR, os.path.abspath(file_path)]) == PUBLIC_DIR:
            self.send_error_json(403, "Forbidden")
            return

        if not os.path.isfile(file_path):
            self.send_error_json(404, "File not found")
            return

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            if not head_only:
                self.wfile.write(content)
        except Exception as e:
            self.send_error_json(500, f"Internal server error: {str(e)}")

def run_server(port=PORT):
    db.init_db()
    server_address = ("", port)
    httpd = HTTPServer(server_address, IdeaBridgeHandler)
    print(f"Idea Bridge Server running on http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Server stopped.")

if __name__ == "__main__":
    run_server()
