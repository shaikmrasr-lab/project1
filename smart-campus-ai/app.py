"""
Smart Campus AI - Backend Server & REST API Router
Self-contained Python HTTP Server using standard library.
Handles REST endpoints, JSON serialization, SQLite persistence, and static asset serving.
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import mimetypes
import traceback
from datetime import datetime, timedelta

from database import init_db, query_db, execute_db, get_setting, set_setting
from sample_data import seed_sample_data
from ai_engine import (
    answer_chat_query, 
    summarize_notes_ai, 
    generate_study_plan_ai, 
    calculate_academic_urgency_copilot,
    get_active_gemini_key
)

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

class SmartCampusHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Override for clean logging
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]} - {args[1]}")

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"error": message, "status": status}, status=status)

    def read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode('utf-8')
        try:
            return json.loads(raw)
        except Exception:
            return {}

    # -----------------------------------------------------------------
    # GET REQUEST DISPATCHER
    # -----------------------------------------------------------------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        # 1. API Endpoints
        if path.startswith("/api/"):
            return self.handle_api_get(path, query_params)

        # 2. Static File Serving
        self.serve_static(path)

    def handle_api_get(self, path, params):
        try:
            # Dashboard Overview
            if path == "/api/dashboard":
                user = query_db("SELECT * FROM users LIMIT 1", one=True)
                today_day = datetime.now().strftime("%A")
                today_classes = query_db("SELECT * FROM classes WHERE day_of_week = ? ORDER BY start_time", (today_day,))
                urgent_deadlines = query_db("SELECT * FROM deadlines WHERE status = 'upcoming' ORDER BY deadline_date ASC LIMIT 4")
                pending_tasks = query_db("SELECT * FROM tasks WHERE status != 'completed' ORDER BY due_date ASC LIMIT 4")
                notices = query_db("SELECT * FROM announcements ORDER BY is_pinned DESC, id DESC LIMIT 3")
                copilot = calculate_academic_urgency_copilot()

                # Calculate quick stats
                total_tasks = query_db("SELECT COUNT(*) as count FROM tasks", one=True)['count']
                completed_tasks = query_db("SELECT COUNT(*) as count FROM tasks WHERE status = 'completed'", one=True)['count']
                
                # Active API status
                has_key = bool(get_active_gemini_key())

                return self.send_json({
                    "user": user,
                    "today_day": today_day,
                    "today_classes": today_classes,
                    "urgent_deadlines": urgent_deadlines,
                    "pending_tasks": pending_tasks,
                    "notices": notices,
                    "stats": {
                        "total_tasks": total_tasks,
                        "completed_tasks": completed_tasks,
                        "completion_rate": round((completed_tasks / total_tasks * 100) if total_tasks else 0, 1),
                        "gpa": user['gpa'] if user else 3.82,
                        "attendance": user['attendance_pct'] if user else 94.2,
                        "streak_days": user['streak_days'] if user else 7,
                        "ai_engine_active": "Gemini Flash (API Key Set)" if has_key else "Smart Local AI (Zero Quota Mode)"
                    },
                    "copilot": copilot
                })

            # Classes / Timetable
            elif path == "/api/timetable":
                day = params.get("day", [None])[0]
                if day:
                    classes = query_db("SELECT * FROM classes WHERE day_of_week = ? ORDER BY start_time", (day,))
                else:
                    classes = query_db("SELECT * FROM classes ORDER BY CASE day_of_week "
                                       "WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 "
                                       "WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 ELSE 6 END, start_time")
                courses = query_db("SELECT * FROM courses")
                return self.send_json({"classes": classes, "courses": courses})

            # Tasks
            elif path == "/api/tasks":
                status = params.get("status", [None])[0]
                priority = params.get("priority", [None])[0]
                sql = "SELECT * FROM tasks WHERE 1=1"
                args = []
                if status == "pending":
                    sql += " AND status != 'completed'"
                elif status == "completed":
                    sql += " AND status = 'completed'"
                if priority:
                    sql += " AND priority = ?"
                    args.append(priority)
                sql += " ORDER BY CASE status WHEN 'in_progress' THEN 1 WHEN 'pending' THEN 2 ELSE 3 END, due_date ASC"
                tasks = query_db(sql, args)
                return self.send_json({"tasks": tasks})

            # Deadlines & Exams
            elif path == "/api/deadlines":
                deadlines = query_db("SELECT * FROM deadlines ORDER BY deadline_date ASC")
                now = datetime.now()
                # Compute human friendly countdown
                enriched = []
                for d in deadlines:
                    d_dict = dict(d)
                    try:
                        due_dt = datetime.fromisoformat(d['deadline_date'].replace('Z', ''))
                        diff = due_dt - now
                        if diff.total_seconds() < 0:
                            d_dict['time_left'] = "Overdue"
                            d_dict['urgency_level'] = "critical"
                        else:
                            hours = int(diff.total_seconds() // 3600)
                            days = hours // 24
                            rem_hours = hours % 24
                            if days > 0:
                                d_dict['time_left'] = f"{days}d {rem_hours}h left"
                            else:
                                d_dict['time_left'] = f"{rem_hours}h left"
                            
                            if hours <= 24:
                                d_dict['urgency_level'] = "critical"
                            elif hours <= 72:
                                d_dict['urgency_level'] = "high"
                            elif days <= 7:
                                d_dict['urgency_level'] = "medium"
                            else:
                                d_dict['urgency_level'] = "normal"
                    except Exception:
                        d_dict['time_left'] = "Upcoming"
                        d_dict['urgency_level'] = "normal"
                    enriched.append(d_dict)
                return self.send_json({"deadlines": enriched})

            # Announcements
            elif path == "/api/announcements":
                cat = params.get("category", [None])[0]
                if cat and cat != "All":
                    notices = query_db("SELECT * FROM announcements WHERE category = ? ORDER BY is_pinned DESC, id DESC", (cat,))
                else:
                    notices = query_db("SELECT * FROM announcements ORDER BY is_pinned DESC, id DESC")
                return self.send_json({"announcements": notices})

            # Chat History
            elif path == "/api/chat":
                messages = query_db("SELECT * FROM chat_messages ORDER BY id ASC LIMIT 50")
                return self.send_json({"messages": messages})

            # Notes
            elif path == "/api/notes":
                notes = query_db("SELECT id, title, course_code, summary, created_at FROM notes ORDER BY id DESC")
                return self.send_json({"notes": notes})

            elif path.startswith("/api/notes/"):
                note_id = path.split("/")[-1]
                note = query_db("SELECT * FROM notes WHERE id = ?", (note_id,), one=True)
                if not note:
                    return self.send_error_json("Note not found", 404)
                note_dict = dict(note)
                try:
                    note_dict['key_takeaways'] = json.loads(note_dict['key_takeaways_json'])
                except Exception:
                    note_dict['key_takeaways'] = []
                try:
                    note_dict['quiz'] = json.loads(note_dict['quiz_json'])
                except Exception:
                    note_dict['quiz'] = []
                return self.send_json({"note": note_dict})

            # Study Planner Active
            elif path == "/api/study-planner/active":
                plan = query_db("SELECT * FROM study_plans WHERE is_active = 1 ORDER BY id DESC LIMIT 1", one=True)
                if plan:
                    plan_dict = dict(plan)
                    try:
                        plan_dict['details'] = json.loads(plan_dict['plan_json'])
                    except Exception:
                        plan_dict['details'] = {}
                    return self.send_json({"active_plan": plan_dict})
                return self.send_json({"active_plan": None})

            # Analytics & Progress Tracker
            elif path == "/api/analytics":
                study_logs = query_db("SELECT date, SUM(minutes_studied) as total_minutes FROM study_logs GROUP BY date ORDER BY date ASC")
                subject_dist = query_db("SELECT subject, SUM(minutes_studied) as total_minutes FROM study_logs GROUP BY subject ORDER BY total_minutes DESC")
                tasks_status = query_db("SELECT status, COUNT(*) as count FROM tasks GROUP BY status")
                user = query_db("SELECT * FROM users LIMIT 1", one=True)

                total_mins = sum(s['total_minutes'] for s in study_logs) if study_logs else 0
                total_hours = round(total_mins / 60.0, 1)

                return self.send_json({
                    "study_trend": study_logs,
                    "subject_distribution": subject_dist,
                    "tasks_status": tasks_status,
                    "total_study_hours": total_hours,
                    "streak_days": user['streak_days'] if user else 7,
                    "attendance": user['attendance_pct'] if user else 94.2,
                    "gpa": user['gpa'] if user else 3.82
                })

            # Co-pilot Urgency Matrix
            elif path == "/api/copilot":
                copilot = calculate_academic_urgency_copilot()
                return self.send_json(copilot)

            # Settings
            elif path == "/api/settings":
                api_key = get_active_gemini_key()
                theme = get_setting("theme", "dark")
                model = get_setting("gemini_model", "gemini-1.5-flash")
                # Mask API key for UI security
                masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else ("Configured" if api_key else "")
                return self.send_json({
                    "has_gemini_key": bool(api_key),
                    "masked_key": masked_key,
                    "theme": theme,
                    "gemini_model": model,
                    "engine_label": "Gemini 1.5 Flash (Online)" if api_key else "Smart Local AI Engine (Zero Quota Mode)"
                })

            else:
                self.send_error_json("API Route Not Found", 404)

        except Exception as e:
            traceback.print_exc()
            self.send_error_json(f"Internal Server Error: {str(e)}", 500)

    # -----------------------------------------------------------------
    # POST REQUEST DISPATCHER
    # -----------------------------------------------------------------
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        try:
            # 1. Chat Message
            if path == "/api/chat":
                msg = body.get("message", "").strip()
                if not msg:
                    return self.send_error_json("Message cannot be empty")
                
                context_type = body.get("context_type", "general")
                source_doc = body.get("source_doc", None)

                # Save user message
                execute_db("INSERT INTO chat_messages (role, message, context_type, source_doc) VALUES (?, ?, ?, ?)",
                           ("user", msg, context_type, source_doc))

                # Answer with AI
                ai_result = answer_chat_query(msg, context_type=context_type, source_doc=source_doc)
                reply = ai_result["reply"]
                engine = ai_result["engine"]

                # Save assistant reply
                msg_id = execute_db("INSERT INTO chat_messages (role, message, context_type, source_doc) VALUES (?, ?, ?, ?)",
                                   ("assistant", reply, context_type, source_doc))

                return self.send_json({
                    "id": msg_id,
                    "role": "assistant",
                    "message": reply,
                    "engine": engine,
                    "created_at": datetime.now().isoformat()
                })

            # 2. Add Task
            elif path == "/api/tasks":
                title = body.get("title", "").strip()
                if not title:
                    return self.send_error_json("Task title is required")
                course_code = body.get("course_code", "GEN101").strip()
                due_date = body.get("due_date", datetime.now().strftime("%Y-%m-%dT23:59"))
                priority = body.get("priority", "Medium")
                description = body.get("description", "").strip()
                est_mins = int(body.get("estimated_minutes", 60))

                task_id = execute_db("""
                INSERT INTO tasks (title, description, course_code, due_date, priority, estimated_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (title, description, course_code, due_date, priority, est_mins))

                return self.send_json({"success": True, "task_id": task_id, "message": "Task created successfully"})

            # 3. Add Deadline
            elif path == "/api/deadlines":
                title = body.get("title", "").strip()
                if not title:
                    return self.send_error_json("Deadline title is required")
                course_code = body.get("course_code", "GEN101").strip()
                dtype = body.get("type", "Assignment")
                deadline_date = body.get("deadline_date", datetime.now().strftime("%Y-%m-%dT23:59"))
                weight = int(body.get("weight_pct", 10))
                location = body.get("location", "")
                description = body.get("description", "")

                did = execute_db("""
                INSERT INTO deadlines (title, course_code, type, deadline_date, weight_pct, location, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (title, course_code, dtype, deadline_date, weight, location, description))

                return self.send_json({"success": True, "deadline_id": did, "message": "Deadline added successfully"})

            # 4. Add Announcement
            elif path == "/api/announcements":
                title = body.get("title", "").strip()
                content = body.get("content", "").strip()
                if not title or not content:
                    return self.send_error_json("Title and content are required")
                category = body.get("category", "General")
                author = body.get("author", "Student Council")
                is_urgent = 1 if body.get("is_urgent") else 0

                aid = execute_db("""
                INSERT INTO announcements (title, category, author, date, content, is_pinned, is_urgent)
                VALUES (?, ?, ?, ?, ?, 0, ?)
                """, (title, category, author, datetime.now().strftime("%Y-%m-%d"), content, is_urgent))

                return self.send_json({"success": True, "announcement_id": aid, "message": "Announcement published"})

            # 5. Mark Announcement Read
            elif path.startswith("/api/announcements/") and path.endswith("/read"):
                aid = path.split("/")[3]
                execute_db("UPDATE announcements SET is_read = 1 WHERE id = ?", (aid,))
                return self.send_json({"success": True})

            # 6. Notes Summarizer & Quiz Generation
            elif path == "/api/notes/summarize":
                note_title = body.get("title", "Lecture Notes").strip()
                note_content = body.get("content", "").strip()
                course_code = body.get("course_code", "CS301").strip()

                if not note_content or len(note_content) < 30:
                    return self.send_error_json("Please provide at least 30 characters of note text to summarize.")

                result = summarize_notes_ai(note_title, note_content, course_code=course_code)

                # Save note to library
                note_id = execute_db("""
                INSERT INTO notes (title, course_code, original_text, summary, key_takeaways_json, quiz_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    note_title,
                    course_code,
                    note_content,
                    result.get("summary", ""),
                    json.dumps(result.get("key_takeaways", [])),
                    json.dumps(result.get("quiz", []))
                ))

                result["id"] = note_id
                return self.send_json(result)

            # 7. Generate Study Plan
            elif path == "/api/study-planner/generate":
                subjects = body.get("subjects", ["CS301", "CS304", "MATH210"])
                available_hours = body.get("available_hours", 4.0)
                target_date = body.get("target_date", datetime.now().strftime("%Y-%m-%d"))
                technique = body.get("technique", "Pomodoro (25/5)")

                plan = generate_study_plan_ai(subjects, available_hours, target_date, technique)

                # Deactivate older plans
                execute_db("UPDATE study_plans SET is_active = 0")
                # Save as active plan
                plan_id = execute_db("""
                INSERT INTO study_plans (title, subjects_json, available_hours, technique, plan_json, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
                """, (
                    plan.get("title", "Study Plan"),
                    json.dumps(subjects if isinstance(subjects, list) else [subjects]),
                    available_hours,
                    technique,
                    json.dumps(plan)
                ))

                plan["id"] = plan_id
                return self.send_json(plan)

            # 8. Log Study Session (for Progress Analytics)
            elif path == "/api/study-logs":
                subject = body.get("subject", "CS301")
                minutes = int(body.get("minutes", 30))
                technique = body.get("technique", "Pomodoro")
                notes = body.get("notes", "")

                lid = execute_db("""
                INSERT INTO study_logs (date, subject, minutes_studied, technique, notes)
                VALUES (?, ?, ?, ?, ?)
                """, (datetime.now().strftime("%Y-%m-%d"), subject, minutes, technique, notes))

                return self.send_json({"success": True, "log_id": lid})

            # 9. Update Settings
            elif path == "/api/settings":
                if "gemini_api_key" in body:
                    set_setting("gemini_api_key", body["gemini_api_key"].strip())
                if "theme" in body:
                    set_setting("theme", body["theme"].strip())
                if "gemini_model" in body:
                    set_setting("gemini_model", body["gemini_model"].strip())
                return self.send_json({"success": True, "message": "Settings updated successfully"})

            else:
                self.send_error_json("POST Route Not Found", 404)

        except Exception as e:
            traceback.print_exc()
            self.send_error_json(f"Error handling POST: {str(e)}", 500)

    # -----------------------------------------------------------------
    # PUT REQUEST DISPATCHER
    # -----------------------------------------------------------------
    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        try:
            # Update Task
            if path.startswith("/api/tasks/"):
                task_id = path.split("/")[-1]
                fields = []
                args = []
                for field in ["title", "description", "course_code", "due_date", "priority", "status", "estimated_minutes"]:
                    if field in body:
                        fields.append(f"{field} = ?")
                        args.append(body[field])

                if "status" in body and body["status"] == "completed":
                    fields.append("completed_at = ?")
                    args.append(datetime.now().isoformat())

                if not fields:
                    return self.send_error_json("No fields to update")

                args.append(task_id)
                execute_db(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", args)
                return self.send_json({"success": True, "message": "Task updated"})

            # Toggle Study Plan Session Status
            elif path.startswith("/api/study-planner/session/"):
                slot = int(path.split("/")[-1])
                plan = query_db("SELECT * FROM study_plans WHERE is_active = 1 ORDER BY id DESC LIMIT 1", one=True)
                if plan:
                    plan_data = json.loads(plan['plan_json'])
                    for s in plan_data.get('sessions', []):
                        if s.get('slot') == slot:
                            s['status'] = "completed" if s.get('status') != "completed" else "pending"
                    execute_db("UPDATE study_plans SET plan_json = ? WHERE id = ?", (json.dumps(plan_data), plan['id']))
                    return self.send_json({"success": True, "sessions": plan_data.get('sessions', [])})
                return self.send_error_json("No active plan found", 404)

            else:
                self.send_error_json("PUT Route Not Found", 404)

        except Exception as e:
            traceback.print_exc()
            self.send_error_json(f"Error handling PUT: {str(e)}", 500)

    # -----------------------------------------------------------------
    # DELETE REQUEST DISPATCHER
    # -----------------------------------------------------------------
    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            if path.startswith("/api/tasks/"):
                task_id = path.split("/")[-1]
                execute_db("DELETE FROM tasks WHERE id = ?", (task_id,))
                return self.send_json({"success": True, "message": "Task deleted"})

            elif path.startswith("/api/deadlines/"):
                did = path.split("/")[-1]
                execute_db("DELETE FROM deadlines WHERE id = ?", (did,))
                return self.send_json({"success": True, "message": "Deadline deleted"})

            elif path.startswith("/api/notes/"):
                nid = path.split("/")[-1]
                execute_db("DELETE FROM notes WHERE id = ?", (nid,))
                return self.send_json({"success": True, "message": "Note deleted"})

            elif path == "/api/chat":
                execute_db("DELETE FROM chat_messages")
                return self.send_json({"success": True, "message": "Chat history cleared"})

            else:
                self.send_error_json("DELETE Route Not Found", 404)

        except Exception as e:
            traceback.print_exc()
            self.send_error_json(f"Error handling DELETE: {str(e)}", 500)

    # -----------------------------------------------------------------
    # STATIC FILE SERVING
    # -----------------------------------------------------------------
    def serve_static(self, path):
        if path == "/" or path == "":
            path = "/index.html"

        # Sanitize path
        clean_path = os.path.normpath(path.lstrip("/"))
        file_path = os.path.join(STATIC_DIR, clean_path)

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            file_path = os.path.join(STATIC_DIR, "index.html")

        if not os.path.exists(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            if file_path.endswith(".js"):
                mime_type = "application/javascript"
            elif file_path.endswith(".css"):
                mime_type = "text/css"
            else:
                mime_type = "application/octet-stream"

        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))


def run_server(port=PORT):
    init_db()
    seed_sample_data()

    handler = SmartCampusHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"============================================================")
        print(f"🎓 Smart Campus AI Server running at http://localhost:{port}")
        print(f"   Zero-dependency Python server with SQLite & Dual AI Engine")
        print(f"============================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down Smart Campus AI server...")
            httpd.server_close()

if __name__ == "__main__":
    run_server()
