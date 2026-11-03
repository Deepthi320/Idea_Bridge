"""
Idea Bridge - Unit & Integration Test Suite
Tests SQLite database methods and HTTP REST API handlers.
"""

import unittest
import os
import json
import tempfile
import urllib.request
import urllib.parse
from http.server import HTTPServer
from socketserver import ThreadingMixIn
import threading
import time

import db
from server import IdeaBridgeHandler

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class TestDatabaseLayer(unittest.TestCase):
    def setUp(self):
        self.tmp_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.tmp_fd)
        db.init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_seed_ideas_exist(self):
        ideas = db.list_ideas(db_path=self.db_path)
        self.assertGreaterEqual(len(ideas), 5)
        stats = db.get_stats(db_path=self.db_path)
        self.assertGreaterEqual(stats["total_ideas"], 5)
        self.assertGreaterEqual(stats["total_votes"], 10)

    def test_create_and_get_idea(self):
        new_data = {
            "title": "Quantum Mesh Sensor Network",
            "description": "Distributed environmental sensors measuring urban heat islands.",
            "category": "Technology",
            "stage": "Discovery",
            "tags": "iot,quantum,urban",
            "author_name": "Dr. Alice",
            "author_email": "alice@test.org"
        }
        created = db.create_idea(new_data, db_path=self.db_path)
        self.assertIsNotNone(created)
        self.assertEqual(created["title"], "Quantum Mesh Sensor Network")
        self.assertEqual(created["votes"], 0)

        fetched = db.get_idea(created["id"], db_path=self.db_path)
        self.assertEqual(fetched["id"], created["id"])
        self.assertEqual(fetched["author_name"], "Dr. Alice")

    def test_update_idea(self):
        ideas = db.list_ideas(db_path=self.db_path)
        target = ideas[0]
        updated = db.update_idea(target["id"], {"stage": "Completed", "title": "Updated Title"}, db_path=self.db_path)
        self.assertEqual(updated["stage"], "Completed")
        self.assertEqual(updated["title"], "Updated Title")

    def test_delete_idea(self):
        new_data = {
            "title": "Temporary Idea",
            "description": "To be removed",
            "category": "Other",
            "author_name": "Test User"
        }
        created = db.create_idea(new_data, db_path=self.db_path)
        self.assertTrue(db.delete_idea(created["id"], db_path=self.db_path))
        self.assertIsNone(db.get_idea(created["id"], db_path=self.db_path))

    def test_vote_idea(self):
        ideas = db.list_ideas(db_path=self.db_path)
        target = ideas[0]
        initial_votes = target["votes"]
        new_votes = db.vote_idea(target["id"], delta=1, db_path=self.db_path)
        self.assertEqual(new_votes, initial_votes + 1)

    def test_comments_and_collaborators(self):
        ideas = db.list_ideas(db_path=self.db_path)
        target_id = ideas[0]["id"]

        comment = db.add_comment(target_id, "Tester", "Excited about this!", db_path=self.db_path)
        self.assertEqual(comment["author_name"], "Tester")
        self.assertEqual(comment["content"], "Excited about this!")

        collab = db.add_collaborator(target_id, "Dev Dave", "Lead Architect", "dave@example.com", db_path=self.db_path)
        self.assertEqual(collab["name"], "Dev Dave")
        self.assertEqual(collab["role"], "Lead Architect")

        fetched = db.get_idea(target_id, db_path=self.db_path)
        comment_contents = [c["content"] for c in fetched["comments"]]
        self.assertIn("Excited about this!", comment_contents)
        collab_names = [c["name"] for c in fetched["collaborators"]]
        self.assertIn("Dev Dave", collab_names)

    def test_filtering_and_search(self):
        results = db.list_ideas(category="Sustainability", db_path=self.db_path)
        for r in results:
            self.assertEqual(r["category"].lower(), "sustainability")

        search_results = db.list_ideas(search="waste", db_path=self.db_path)
        self.assertGreaterEqual(len(search_results), 1)

class TestServerAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_fd, cls.test_db = tempfile.mkstemp(suffix=".db")
        os.close(cls.tmp_fd)
        os.environ["IDEA_BRIDGE_DB"] = cls.test_db
        db.init_db(cls.test_db)

        cls.port = 8999
        cls.server = ThreadedHTTPServer(("127.0.0.1", cls.port), IdeaBridgeHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)

    def url(self, endpoint):
        return f"http://127.0.0.1:{self.port}{endpoint}"

    def request_json(self, endpoint, method="GET", payload=None):
        req = urllib.request.Request(self.url(endpoint), method=method)
        if payload is not None:
            req.add_header("Content-Type", "application/json")
            data = json.dumps(payload).encode("utf-8")
        else:
            data = None

        with urllib.request.urlopen(req, data=data) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
            return status, json.loads(body) if body else None

    def test_get_stats(self):
        status, data = self.request_json("/api/stats")
        self.assertEqual(status, 200)
        self.assertIn("total_ideas", data)
        self.assertIn("active_projects", data)

    def test_list_ideas(self):
        status, data = self.request_json("/api/ideas")
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_create_idea_validation(self):
        # Missing title
        try:
            self.request_json("/api/ideas", method="POST", payload={"description": "No title"})
            self.fail("Should have failed with HTTP 400")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)

        # Successful creation
        status, created = self.request_json("/api/ideas", method="POST", payload={
            "title": "GreenRoof Solar Integration",
            "description": "Combining rooftop gardens with bifacial solar panels.",
            "category": "Sustainability",
            "author_name": "SolarTeam"
        })
        self.assertEqual(status, 201)
        self.assertEqual(created["title"], "GreenRoof Solar Integration")

        # Get idea by id
        status, fetched = self.request_json(f"/api/ideas/{created['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(fetched["title"], "GreenRoof Solar Integration")

    def test_voting_endpoint(self):
        status, ideas = self.request_json("/api/ideas")
        target_id = ideas[0]["id"]
        status, res = self.request_json(f"/api/ideas/{target_id}/vote", method="POST", payload={"delta": 1})
        self.assertEqual(status, 200)
        self.assertEqual(res["id"], target_id)

    def test_comments_and_collaborators_api(self):
        status, ideas = self.request_json("/api/ideas")
        target_id = ideas[0]["id"]

        status, comment = self.request_json(f"/api/ideas/{target_id}/comments", method="POST", payload={
            "author_name": "API Reviewer",
            "content": "API is fast and clean."
        })
        self.assertEqual(status, 201)
        self.assertEqual(comment["author_name"], "API Reviewer")

        status, collab = self.request_json(f"/api/ideas/{target_id}/collaborators", method="POST", payload={
            "name": "Jane Tester",
            "role": "QA Specialist",
            "contact_info": "jane@qa.org"
        })
        self.assertEqual(status, 201)
        self.assertEqual(collab["name"], "Jane Tester")

    def test_patch_stage(self):
        status, ideas = self.request_json("/api/ideas")
        target_id = ideas[0]["id"]

        status, updated = self.request_json(f"/api/ideas/{target_id}", method="PATCH", payload={
            "stage": "Completed"
        })
        self.assertEqual(status, 200)
        self.assertEqual(updated["stage"], "Completed")

    def test_delete_endpoint(self):
        status, created = self.request_json("/api/ideas", method="POST", payload={
            "title": "Ephemeral Concept",
            "description": "Will be deleted immediately.",
            "author_name": "Tester"
        })
        target_id = created["id"]

        status, del_res = self.request_json(f"/api/ideas/{target_id}", method="DELETE")
        self.assertEqual(status, 200)
        self.assertTrue(del_res["success"])

        # Subsequent GET should return 404
        try:
            self.request_json(f"/api/ideas/{target_id}")
            self.fail("Expected 404")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)

if __name__ == "__main__":
    unittest.main()
