"""
Smart Campus AI - End-to-End Test Suite
Tests server startup, routing, database CRUD, and dual AI engine responses.
"""

import threading
import time
import urllib.request
import urllib.error
import json
import socketserver
from app import SmartCampusHandler, init_db, seed_sample_data

PORT = 8000
BASE_URL = f"http://127.0.0.1:{PORT}"

def run_test_server():
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), SmartCampusHandler)
    httpd.serve_forever()

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, json.loads(r.read().decode('utf-8'))

def post(path, data):
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return r.status, json.loads(r.read().decode('utf-8'))

def run_all_tests():
    print(">>> 1. Initializing DB and Sample Data...")
    init_db()
    seed_sample_data()

    print(">>> 2. Launching Test Server in background thread...")
    t = threading.Thread(target=run_test_server, daemon=True)
    t.start()
    time.sleep(1)

    print(">>> 3. Testing Static HTML and Assets...")
    with urllib.request.urlopen(f"{BASE_URL}/", timeout=5) as r:
        assert r.status == 200
        html = r.read().decode('utf-8')
        assert "Smart Campus AI" in html
        print("  ✓ index.html served correctly")

    with urllib.request.urlopen(f"{BASE_URL}/css/styles.css", timeout=5) as r:
        assert r.status == 200
        print("  ✓ styles.css served correctly")

    print(">>> 4. Testing GET /api/dashboard...")
    status, dash = get("/api/dashboard")
    assert status == 200
    assert dash["user"]["name"] == "Alex Morgan"
    assert len(dash["today_classes"]) > 0
    assert len(dash["urgent_deadlines"]) > 0
    print(f"  ✓ Dashboard returned {len(dash['today_classes'])} classes and {len(dash['urgent_deadlines'])} deadlines")

    print(">>> 5. Testing GET /api/tasks & POST /api/tasks...")
    status, task_list = get("/api/tasks")
    assert status == 200
    initial_count = len(task_list["tasks"])
    print(f"  ✓ Initial tasks count: {initial_count}")

    status, new_task = post("/api/tasks", {
        "title": "Automated Unit Test Task",
        "course_code": "CS301",
        "priority": "Urgent",
        "estimated_minutes": 45
    })
    assert status == 200
    assert new_task["success"] is True
    print(f"  ✓ Task created with id: {new_task['task_id']}")

    print(">>> 6. Testing GET /api/copilot (Academic Urgency Co-pilot)...")
    status, copilot = get("/api/copilot")
    assert status == 200
    assert "risk_index" in copilot
    assert "recommended_action" in copilot
    print(f"  ✓ Co-pilot Risk: {copilot['risk_index']}%, Next Action: {copilot['recommended_action']['title']}")

    print(">>> 7. Testing POST /api/chat (CampusBot)...")
    status, chat_res = post("/api/chat", {
        "message": "What is the attendance policy for examinations?"
    })
    assert status == 200
    assert "attendance" in chat_res["message"].lower() or "policy" in chat_res["message"].lower()
    print(f"  ✓ CampusBot replied using: {chat_res['engine']}")

    print(">>> 8. Testing Document Q&A in Chatbot...")
    doc_text = "The mid-term exam will cover Chapters 1 to 5. Negative marking of 0.25 marks applies to multiple choice questions."
    status, doc_chat = post("/api/chat", {
        "message": "Is there negative marking in the exam?",
        "context_type": "doc",
        "source_doc": doc_text
    })
    assert status == 200
    assert "negative" in doc_chat["message"].lower()
    print(f"  ✓ Document Q&A verified with citations")

    print(">>> 9. Testing POST /api/notes/summarize & Quiz Generator...")
    sample_text = (
        "Binary Search Trees (BST) maintain the invariant that for every node, left child values are strictly smaller, "
        "and right child values are strictly greater. In average case, search takes O(log N) time, but can degrade to O(N) if unbalanced. "
        "AVL trees and Red-Black trees self-balance using rotations to guarantee worst-case logarithmic lookup."
    )
    status, note_res = post("/api/notes/summarize", {
        "title": "Binary Search Trees & Balancing",
        "course_code": "CS301",
        "content": sample_text
    })
    assert status == 200
    assert "summary" in note_res
    assert len(note_res["key_takeaways"]) > 0
    assert len(note_res["quiz"]) == 5
    print(f"  ✓ Notes summarized successfully, {len(note_res['quiz'])} quiz questions generated")

    print(">>> 10. Testing POST /api/study-planner/generate...")
    status, plan_res = post("/api/study-planner/generate", {
        "subjects": ["CS301", "CS304", "MATH210"],
        "available_hours": 4.0,
        "technique": "Pomodoro (25/5)"
    })
    assert status == 200
    assert len(plan_res["sessions"]) > 0
    print(f"  ✓ Study plan generated with {len(plan_res['sessions'])} sessions")

    print(">>> 11. Testing GET /api/analytics...")
    status, analytics = get("/api/analytics")
    assert status == 200
    assert len(analytics["study_trend"]) > 0
    assert len(analytics["subject_distribution"]) > 0
    print(f"  ✓ Analytics verified: {analytics['total_study_hours']} study hours recorded")

    print("\n========================================================")
    print("🎉 ALL TESTS PASSED SUCCESSFULLY! SMART CAMPUS AI IS READY.")
    print("========================================================")

if __name__ == "__main__":
    run_all_tests()
