"""
Smart Campus AI - Sample Data Seeder
Provides realistic, high-quality university data so the application is immediately ready for hackathon demonstration.
"""

from database import get_connection, execute_db, query_db
from datetime import datetime, timedelta
import json

def seed_sample_data():
    conn = get_connection()
    cur = conn.cursor()

    # Check if data already seeded
    cur.execute("SELECT COUNT(*) as count FROM users")
    if cur.fetchone()['count'] > 0:
        conn.close()
        return

    print("Seeding Smart Campus AI database with realistic collegiate data...")

    # 1. User Profile
    cur.execute("""
    INSERT INTO users (name, email, student_id, major, semester, gpa, attendance_pct, streak_days, daily_goal_hours)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Alex Morgan",
        "alex.morgan@campus.edu",
        "STU-2024-8891",
        "Computer Science & Engineering",
        "Semester 4 (Sophomore)",
        3.84,
        94.6,
        8,
        4.5
    ))

    # 2. Courses
    courses = [
        ("CS301", "Design & Analysis of Algorithms", "Prof. Robert Thorne", "Turing Hall 302", 4, "#6366f1"),
        ("CS304", "Database Management Systems", "Dr. Elena Rostova", "Ada Lovelace Lab 3", 4, "#06b6d4"),
        ("MATH210", "Discrete Mathematics & Logic", "Prof. Kevin Zhang", "Newton Block 104", 3, "#f59e0b"),
        ("AI102", "Artificial Intelligence & Heuristics", "Dr. Maya Patel", "Shannon AI Suite", 4, "#8b5cf6"),
        ("ENG205", "Technical Communication & Ethics", "Prof. Sarah Jenkins", "Humanities Complex 210", 2, "#10b981")
    ]
    cur.executemany("""
    INSERT INTO courses (code, name, instructor, room, credits, color)
    VALUES (?, ?, ?, ?, ?, ?)
    """, courses)

    # 3. Weekly Class Timetable
    # Generate for all weekdays
    classes = [
        # Monday
        ("CS301", "Monday", "09:00", "10:30", "Turing Hall 302", "Prof. Robert Thorne", "Dynamic Programming & Knapsack"),
        ("CS304", "Monday", "11:00", "12:30", "Ada Lovelace Lab 3", "Dr. Elena Rostova", "SQL Indexes & Query Plans"),
        ("MATH210", "Monday", "14:00", "15:30", "Newton Block 104", "Prof. Kevin Zhang", "Graph Theory & Trees"),
        # Tuesday
        ("AI102", "Tuesday", "10:00", "11:30", "Shannon AI Suite", "Dr. Maya Patel", "A* Search & Adversarial Minimax"),
        ("ENG205", "Tuesday", "13:00", "14:30", "Humanities Complex 210", "Prof. Sarah Jenkins", "Technical Whitepaper Drafting"),
        # Wednesday
        ("CS301", "Wednesday", "09:00", "10:30", "Turing Hall 302", "Prof. Robert Thorne", "Graph Algorithms: Dijkstra & Prim"),
        ("CS304", "Wednesday", "11:00", "13:00", "Ada Lovelace Lab 3", "Dr. Elena Rostova", "Database Normalization Lab (BCNF)"),
        ("MATH210", "Wednesday", "14:30", "16:00", "Newton Block 104", "Prof. Kevin Zhang", "Combinatorics & Recurrence Relations"),
        # Thursday
        ("AI102", "Thursday", "10:00", "12:00", "Shannon AI Suite", "Dr. Maya Patel", "Neural Network Backpropagation Lab"),
        ("ENG205", "Thursday", "14:00", "15:30", "Humanities Complex 210", "Prof. Sarah Jenkins", "Oral Presentation Workshop"),
        # Friday
        ("CS301", "Friday", "09:30", "11:00", "Turing Hall 302", "Prof. Robert Thorne", "NP-Completeness & Reductions"),
        ("CS304", "Friday", "11:30", "13:00", "Ada Lovelace Lab 3", "Dr. Elena Rostova", "Transaction ACID & Locking Protocols")
    ]
    cur.executemany("""
    INSERT INTO classes (course_code, day_of_week, start_time, end_time, room, professor, topic)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, classes)

    # 4. Tasks (Dynamic dates relative to now)
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    in_2_days = (now + timedelta(days=2)).strftime("%Y-%m-%d")
    in_4_days = (now + timedelta(days=4)).strftime("%Y-%m-%d")
    in_6_days = (now + timedelta(days=6)).strftime("%Y-%m-%d")

    tasks = [
        ("Complete Dijkstra's Algorithm implementation in Python", "Write unit tests for edge cases and analyze worst-case time complexity with adjacency list.", "CS301", f"{today_str}T23:59", "Urgent", "in_progress", 90),
        ("Design Schema for University Hospital Management System", "Draw 3NF ER diagram, write SQL DDL scripts, and define primary/foreign key constraints.", "CS304", f"{tomorrow_str}T18:00", "High", "pending", 120),
        ("Solve Discrete Math Problem Set 5 on Generating Functions", "Problems 4.1 to 4.15 from Chapter 4 of Kenneth Rosen textbook.", "MATH210", f"{in_2_days}T17:00", "Medium", "pending", 75),
        ("Implement Minimax with Alpha-Beta Pruning for Connect-4", "Build the heuristic evaluation function and submit code to GitHub Classroom.", "AI102", f"{in_4_days}T23:59", "High", "pending", 150),
        ("Prepare 5-Minute Pitch Presentation on AI in Education", "Create 6 slides covering problem, proposed architecture, and social impact.", "ENG205", f"{in_6_days}T12:00", "Low", "pending", 45),
        ("Review Lecture Slides on B-Trees & B+ Trees", "Annotate chapter slides and summarize differences in leaf node pointers.", "CS304", f"{today_str}T16:00", "Medium", "completed", 40),
        ("Submit Ethics Case Study on Autonomous Vehicles", "Analyze liability frameworks in self-driving car crashes.", "ENG205", f"{today_str}T10:00", "Low", "completed", 60)
    ]
    cur.executemany("""
    INSERT INTO tasks (title, description, course_code, due_date, priority, status, estimated_minutes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, tasks)

    # 5. Deadlines & Major Examinations
    deadlines = [
        ("CS301 Mid-Term Examination", "CS301", "Exam", f"{in_2_days}T09:00", 30, "Main Auditorium Hall A", "Comprehensive written examination covering asymptotic analysis, divide-and-conquer, dynamic programming, and greedy algorithms.", "upcoming"),
        ("Database Term Project Milestone 2: Query Optimization", "CS304", "Project", f"{in_4_days}T23:59", 20, "Canvas Portal Submission", "Submit execution plans for 10 complex queries, indexing strategy benchmarks, and explain EXPLAIN ANALYZE results.", "upcoming"),
        ("AI102 Adversarial Search Tournament", "AI102", "Assignment", f"{in_6_days}T17:00", 15, "AI Lab Server", "Automated bot tournament where our agent will compete against other class submissions in a 6x7 grid.", "upcoming"),
        ("Discrete Math Quiz 3", "MATH210", "Quiz", f"{(now + timedelta(days=8)).strftime('%Y-%m-%d')}T14:30", 10, "Newton Block 104", "Timed 30-minute closed book quiz on Pigeonhole Principle and Recurrence Relations.", "upcoming")
    ]
    cur.executemany("""
    INSERT INTO deadlines (title, course_code, type, deadline_date, weight_pct, location, description, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, deadlines)

    # 6. Campus Announcements
    announcements = [
        ("Mid-Term Examination Schedule & Hall Allotment Released", "Examination", "Office of the Dean (Academics)", f"{today_str}", 
         "The official Mid-Term schedule for all 2nd and 3rd year engineering students has been finalized. Hall tickets can be downloaded from the university student portal. Please review your designated seating halls at least 24 hours prior to exams.", 1, 1, 0),
        
        ("Annual National Hackathon 2026: Registrations Open ($10,000 Prize Pool)", "Events", "Student Council & Tech Club", f"{today_str}", 
         "Join 500+ student developers, designers, and innovators for a 36-hour weekend sprint. Tracks include AI & Healthcare, Smart Cities, and EdTech. Food, swags, and mentor office hours provided. Register by Friday!", 1, 0, 0),
        
        ("Library 24/7 Extended Study Hours for Midterms", "Academic", "University Central Library", f"{(now - timedelta(days=1)).strftime('%Y-%m-%d')}", 
         "The Central Library and Digital Resource Center will remain open 24/7 starting this Monday through exam week. Quiet reading rooms on floors 3 & 4 have high-speed charging stations and reservable group study pods.", 0, 0, 1),
        
        ("Temporary Relocation: Ada Lovelace Lab 3 Maintenance", "Timetable", "Department of Computer Science", f"{(now - timedelta(days=2)).strftime('%Y-%m-%d')}", 
         "Due to scheduled server hardware upgrades and optical fiber cabling, all Thursday lab sessions for CS304 will be conducted in Turing Hall Lab 1. Regular lab operations resume next week.", 0, 1, 1),
        
        ("Guest Lecture: Scalable Distributed Systems at Google", "Events", "ACM Student Chapter", f"{(now - timedelta(days=3)).strftime('%Y-%m-%d')}", 
         "Distinguished engineer Dr. Alicia Gomez will deliver an interactive talk on 'Building Multi-Region High-Availability Architectures' this Wednesday at 4:30 PM in the Science Auditorium.", 0, 0, 1)
    ]
    cur.executemany("""
    INSERT INTO announcements (title, category, author, date, content, is_pinned, is_urgent, is_read)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, announcements)

    # 7. Pre-populated Notes & Quizzes (Sample lecture note)
    sample_note_text = """
Graph Algorithms: Single-Source Shortest Paths (Dijkstra vs Bellman-Ford)

1. Dijkstra's Algorithm:
- Purpose: Finds shortest paths from a single source vertex to all other vertices in a weighted, directed or undirected graph with NON-NEGATIVE edge weights.
- Strategy: Greedy approach. Maintains a priority queue (min-heap) of tentative distances.
- Time Complexity: O((V + E) log V) using a binary heap, or O(E + V log V) using a Fibonacci heap.
- Limitation: Fails on graphs with negative edge weights or negative cycles because it assumes once a vertex is finalized, its shortest distance cannot be decreased further.

2. Bellman-Ford Algorithm:
- Purpose: Computes shortest paths from a single source vertex, and CAN handle negative edge weights.
- Detection: Detects negative weight cycles. If a cycle's total weight is negative, shortest paths are undefined (can loop indefinitely).
- Strategy: Dynamic Programming. Relaxes all |E| edges (|V| - 1) times.
- Time Complexity: O(V * E), which is slower than Dijkstra on sparse graphs.

3. Key Distinction:
- Dijkstra is faster (logarithmic heap ops) but requires non-negative weights.
- Bellman-Ford is slower but versatile and flags negative cycles.
"""
    key_takeaways = [
        "Dijkstra uses a Greedy strategy with Min-Heap for graphs with non-negative edge weights.",
        "Dijkstra's optimal time complexity is O((V + E) log V) with binary min-heap.",
        "Bellman-Ford uses Dynamic Programming and relaxes all |E| edges (|V| - 1) times.",
        "Bellman-Ford works with negative edge weights and detects negative weight cycles in O(V * E) time.",
        "If a graph has negative cycles reachable from the source, shortest paths are mathematically undefined."
    ]
    quiz_items = [
        {
            "id": 1,
            "question": "Why does Dijkstra's algorithm fail when applied to graphs with negative edge weights?",
            "options": [
                "It causes a stack overflow in recursion",
                "Once a node is marked visited/finalized, the greedy assumption assumes its distance cannot decrease",
                "It creates duplicate vertices in the adjacency list",
                "Priority queues cannot store negative integers"
            ],
            "correct": 1,
            "explanation": "Dijkstra relies on the greedy invariant that adding non-negative edges will never yield a shorter path to an already settled vertex. Negative edges violate this property."
        },
        {
            "id": 2,
            "question": "What is the time complexity of Bellman-Ford on a graph with V vertices and E edges?",
            "options": [
                "O(V log V)",
                "O((V + E) log V)",
                "O(V * E)",
                "O(V^3)"
            ],
            "correct": 2,
            "explanation": "Bellman-Ford performs (|V| - 1) passes, relaxing all |E| edges in each pass, yielding O(V * E) overall time complexity."
        },
        {
            "id": 3,
            "question": "Which data structure yields O((V + E) log V) running time for Dijkstra's algorithm?",
            "options": [
                "Unsorted Array",
                "Binary Min-Heap (Priority Queue)",
                "FIFO Queue (Breadth First Search)",
                "Hash Map without ordering"
            ],
            "correct": 1,
            "explanation": "Using an adjacency list representation with a binary min-heap allows extract-min in O(log V) and edge relaxations in O(log V), totaling O((V + E) log V)."
        },
        {
            "id": 4,
            "question": "How does the Bellman-Ford algorithm detect a negative weight cycle?",
            "options": [
                "If any distance becomes exactly zero",
                "If after (V - 1) iterations, an additional pass still manages to relax any edge",
                "If all edge weights sum to a negative number",
                "If the graph contains back edges in DFS"
            ],
            "correct": 1,
            "explanation": "In a graph with no negative cycles, the shortest path has at most (V - 1) edges. If an edge can still be relaxed on the V-th iteration, a negative cycle must exist."
        },
        {
            "id": 5,
            "question": "For a dense graph where E is proportional to V^2, which Dijkstra implementation performs best?",
            "options": [
                "Dijkstra with simple array: O(V^2)",
                "Dijkstra with binary heap: O(V^2 log V)",
                "Bellman-Ford: O(V^3)",
                "Depth-First Search: O(V + E)"
            ],
            "correct": 0,
            "explanation": "For dense graphs (E ≈ V^2), a simple linear array lookup for extract-min achieves O(V^2), outperforming a binary heap's O(V^2 log V)."
        }
    ]

    cur.execute("""
    INSERT INTO notes (title, course_code, original_text, summary, key_takeaways_json, quiz_json)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "CS301: Graph Shortest Paths - Dijkstra & Bellman-Ford",
        "CS301",
        sample_note_text,
        "A rigorous comparative breakdown of Single-Source Shortest Path algorithms. Covers Dijkstra's greedy min-heap approach (O((V+E)logV)) for non-negative weights versus Bellman-Ford's dynamic programming edge relaxation (O(V*E)) capable of negative weight cycle detection.",
        json.dumps(key_takeaways),
        json.dumps(quiz_items)
    ))

    # 8. Past 7 Days Study Logs (for interactive analytics charts)
    study_logs = [
        ((now - timedelta(days=6)).strftime("%Y-%m-%d"), "CS301", 120, "Pomodoro", "Dynamic programming memoization tables"),
        ((now - timedelta(days=5)).strftime("%Y-%m-%d"), "CS304", 150, "Deep Work", "Query execution plans and BCNF normalization"),
        ((now - timedelta(days=4)).strftime("%Y-%m-%d"), "MATH210", 90, "Pomodoro", "Generating functions and discrete probability"),
        ((now - timedelta(days=3)).strftime("%Y-%m-%d"), "AI102", 180, "Deep Work", "Alpha-Beta pruning and minimax game trees"),
        ((now - timedelta(days=2)).strftime("%Y-%m-%d"), "CS301", 135, "Pomodoro", "Dijkstra algorithm and proof of correctness"),
        ((now - timedelta(days=1)).strftime("%Y-%m-%d"), "CS304", 110, "Pomodoro", "Relational algebra and SQL group-by optimizations"),
        (today_str, "CS301", 95, "Pomodoro", "Graph implementations and priority queue benchmarks")
    ]
    cur.executemany("""
    INSERT INTO study_logs (date, subject, minutes_studied, technique, notes)
    VALUES (?, ?, ?, ?, ?)
    """, study_logs)

    # 9. Active Study Plan
    active_plan = {
        "title": "Midterm Sprint & Assignment Completion Schedule",
        "target_date": in_2_days,
        "available_hours": 4.5,
        "technique": "Pomodoro (50 min study / 10 min break)",
        "sessions": [
            {
                "time": "09:00 - 10:00",
                "subject": "CS301 Algorithms",
                "topic": "Graph Algorithms & Dijkstra Implementation",
                "task": "Complete unit test suite and time complexity writeup",
                "priority": "Urgent",
                "status": "completed"
            },
            {
                "time": "10:15 - 11:30",
                "subject": "CS304 Databases",
                "topic": "Hospital ER Diagram & Normalization to 3NF",
                "task": "Draft ER relational schema and SQL DDL tables",
                "priority": "High",
                "status": "pending"
            },
            {
                "time": "14:00 - 15:15",
                "subject": "MATH210 Discrete Math",
                "topic": "Problem Set 5: Generating Functions & Graphs",
                "task": "Solve exercises 4.5 through 4.10",
                "priority": "Medium",
                "status": "pending"
            },
            {
                "time": "16:00 - 17:00",
                "subject": "AI102 Artificial Intelligence",
                "topic": "Connect-4 Game Heuristic Function",
                "task": "Code board evaluation state score weights",
                "priority": "High",
                "status": "pending"
            },
            {
                "time": "20:00 - 20:45",
                "subject": "Exam Review",
                "topic": "CS301 Flashcards & Concept Recall",
                "task": "Review 20 flashcards on NP-Completeness and Master Theorem",
                "priority": "Medium",
                "status": "pending"
            }
        ]
    }
    cur.execute("""
    INSERT INTO study_plans (title, subjects_json, available_hours, technique, plan_json, is_active)
    VALUES (?, ?, ?, ?, ?, 1)
    """, (
        active_plan["title"],
        json.dumps(["CS301", "CS304", "MATH210", "AI102"]),
        4.5,
        "Pomodoro (50/10)",
        json.dumps(active_plan)
    ))

    # 10. Initial Chatbot Welcome & Context Messages
    initial_chat = [
        ("assistant", "Hello Alex! 👋 I am your Smart Campus AI Assistant. I can help you with your class timetable, approaching assignment deadlines, personalized study schedules, lecture note summarization, and campus regulations. What would you like to tackle today?", "general", None),
        ("user", "What are my most urgent tasks for today?", "general", None),
        ("assistant", "You have 1 urgent task due tonight: **Complete Dijkstra's Algorithm implementation in Python (CS301)** at 23:59. Additionally, your **CS304 Hospital Management Schema** is due tomorrow at 18:00. I recommend dedicating a 90-minute Pomodoro block to Dijkstra's testing this morning!", "task", None)
    ]
    cur.executemany("""
    INSERT INTO chat_messages (role, message, context_type, source_doc)
    VALUES (?, ?, ?, ?)
    """, initial_chat)

    # 11. Initial Settings
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('theme', 'dark')")
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('ai_engine', 'smart_local')")
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('gemini_model', 'gemini-1.5-flash')")

    conn.commit()
    conn.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    from database import init_db
    init_db()
    seed_sample_data()
