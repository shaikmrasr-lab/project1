"""
Smart Campus AI - Internal Component & Request Handler Test Suite
Tests routing, database queries, and AI methods directly using in-memory streams.
Runs seamlessly inside standard sandbox without requiring external sockets.
"""

import io
import json
from app import SmartCampusHandler, init_db, seed_sample_data
from ai_engine import (
    answer_chat_query, 
    local_campus_qa, 
    local_document_qa,
    generate_notes_summary_local,
    generate_study_plan_local,
    calculate_academic_urgency_copilot
)
from database import query_db, execute_db

class MockSocket:
    def __init__(self, data=b""):
        self.rfile = io.BytesIO(data)
        self.output = io.BytesIO()

    def makefile(self, mode, *args, **kwargs):
        if 'r' in mode:
            return self.rfile
        return self.output

    def sendall(self, b):
        self.output.write(b)

class DummyServer:
    pass

def simulate_request(method, path, body=None):
    raw_body = json.dumps(body).encode('utf-8') if body else b""
    header_lines = [
        f"{method} {path} HTTP/1.1",
        "Host: localhost",
        f"Content-Length: {len(raw_body)}",
        "Content-Type: application/json",
        "",
        ""
    ]
    raw_req = "\r\n".join(header_lines).encode('utf-8') + raw_body
    
    mock_sock = MockSocket(raw_req)
    
    # Instantiate handler
    handler = SmartCampusHandler(mock_sock, ("127.0.0.1", 8000), DummyServer)
    
    # Read response
    mock_sock.output.seek(0)
    response_data = mock_sock.output.read().decode('utf-8')
    
    # Parse headers and body
    parts = response_data.split("\r\n\r\n", 1)
    status_line = parts[0].split("\r\n")[0]
    status_code = int(status_line.split()[1])
    body_text = parts[1] if len(parts) > 1 else ""
    
    return status_code, body_text

def run_tests():
    print("==================================================")
    print("Testing Smart Campus AI - Backend & Engine")
    print("==================================================")

    init_db()
    seed_sample_data()

    # 1. Database tests
    user = query_db("SELECT * FROM users LIMIT 1", one=True)
    assert user is not None
    print(f"✓ User profile found: {user['name']} ({user['major']})")

    classes = query_db("SELECT COUNT(*) as c FROM classes", one=True)
    assert classes['c'] > 0
    print(f"✓ Scheduled classes loaded: {classes['c']} class slots")

    deadlines = query_db("SELECT COUNT(*) as c FROM deadlines", one=True)
    assert deadlines['c'] > 0
    print(f"✓ Exam deadlines loaded: {deadlines['c']} deadlines")

    # 2. AI Engine Local Tests
    chat_resp = local_campus_qa("What are the library hours and study rooms?")
    assert "library" in chat_resp.lower()
    print("✓ Local Campus Knowledge Base Q&A verified")

    doc_sample = "Project milestone 2 requires submitting execution plans and indexing strategies for 10 queries."
    doc_resp = local_document_qa("What are the submission requirements?", doc_sample)
    assert "execution plans" in doc_resp.lower()
    print("✓ Local Document-Grounded Q&A (RAG) verified")

    summary = generate_notes_summary_local("Graph Shortest Paths", "Dijkstra algorithm uses a priority queue with O((V+E) log V) time complexity. Bellman-Ford supports negative weights.")
    assert len(summary['key_takeaways']) > 0
    assert len(summary['quiz']) == 5
    print(f"✓ Local Note Summarizer & Quiz Generator verified (5 quiz questions generated)")

    plan = generate_study_plan_local(["CS301", "CS304"], 4.0, "2026-10-15")
    assert len(plan['sessions']) > 0
    print(f"✓ Local Study Planner generated {len(plan['sessions'])} sessions")

    copilot = calculate_academic_urgency_copilot()
    assert "risk_index" in copilot
    assert "recommended_action" in copilot
    print(f"✓ Academic Urgency Co-pilot Risk: {copilot['risk_index']}%, Action: {copilot['recommended_action']['title']}")

    # 3. Request Handler Simulated Endpoints
    status, body = simulate_request("GET", "/api/dashboard")
    assert status == 200
    dash_json = json.loads(body)
    assert dash_json["user"]["name"] == "Alex Morgan"
    print("✓ GET /api/dashboard returned 200 OK with full student state")

    status, body = simulate_request("GET", "/api/timetable")
    assert status == 200
    print("✓ GET /api/timetable returned 200 OK")

    status, body = simulate_request("GET", "/api/tasks")
    assert status == 200
    print("✓ GET /api/tasks returned 200 OK")

    status, body = simulate_request("POST", "/api/tasks", {
        "title": "Build Final AI Presentation Slides",
        "course_code": "CS301",
        "priority": "High",
        "estimated_minutes": 60
    })
    assert status == 200
    print("✓ POST /api/tasks created new task successfully")

    status, body = simulate_request("POST", "/api/chat", {
        "message": "When can I use the Ada Lovelace computer lab?"
    })
    assert status == 200
    chat_out = json.loads(body)
    assert len(chat_out["message"]) > 0
    print(f"✓ POST /api/chat replied: '{chat_out['message'][:50]}...'")

    status, body = simulate_request("GET", "/api/analytics")
    assert status == 200
    analytics_out = json.loads(body)
    assert len(analytics_out["study_trend"]) > 0
    print("✓ GET /api/analytics returned trend logs")

    status, body = simulate_request("GET", "/")
    assert status == 200
    assert "Smart Campus" in body
    print("✓ GET / (Static Index) returned 200 OK")

    status, body = simulate_request("GET", "/css/styles.css")
    assert status == 200
    assert "--primary" in body
    print("✓ GET /css/styles.css returned 200 OK")

    status, body = simulate_request("GET", "/js/app.js")
    assert status == 200
    assert "app.init" in body
    print("✓ GET /js/app.js returned 200 OK")

    print("\n==================================================")
    print("🎯 ALL 14 INTERNAL TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
