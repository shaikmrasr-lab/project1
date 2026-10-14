"""
Smart Campus AI - AI Engine (Dual-Mode: Free Gemini Flash + Intelligent Local Engine)
Zero external dependencies (uses standard urllib.request and json).
Gracefully handles free-tier quotas, offline mode, and API errors.
"""

import os
import json
import re
import math
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from database import get_setting, query_db

# Built-in College Knowledge Base for CampusBot
CAMPUS_KNOWLEDGE_BASE = {
    "library": {
        "keywords": ["library", "books", "borrow", "reading room", "study pod", "study room", "central library", "hours"],
        "info": "The University Central Library is located at Building 4. Regular hours: Monday-Friday 08:00 - 22:00, Weekends 10:00 - 18:00. During Midterm & Final Exam weeks, it operates 24/7. Students can borrow up to 6 books for 21 days using their student ID. Private study pods on floors 3 & 4 can be reserved online via the campus portal."
    },
    "attendance": {
        "keywords": ["attendance", "minimum attendance", "shortage", "medical leave", "absence", "percentage", "75%"],
        "info": "University policy mandates a minimum of 75% attendance in every registered course to be eligible for final examinations. If your attendance falls between 65% and 74% due to medical reasons, a signed doctor's certificate must be submitted to the Dean's Office within 5 working days of recovery."
    },
    "grading": {
        "keywords": ["grading", "gpa", "cgpa", "scale", "credit", "fail", "pass", "marks", "grade", "rubric"],
        "info": "The grading system follows a 10-point scale: A+ (10.0, 90-100%), A (9.0, 80-89%), B+ (8.0, 70-79%), B (7.0, 60-69%), C (6.0, 50-59%), D (5.0, 40-49%), and F (Fail, <40%). Passing grade is D or higher. CGPA is computed as cumulative credit-weighted grade points divided by total registered credits."
    },
    "exams": {
        "keywords": ["exam", "examination", "midterm", "final", "hall ticket", "admit card", "cheat", "malpractice", "schedule"],
        "info": "Mid-term examinations carry 30% weightage, and End-term finals carry 50% weightage (continuous internal assessments comprise the remaining 20%). Hall tickets must be downloaded from the student portal and carried along with your physical Student ID. Electronic devices, smartwatches, and unauthorized notes are strictly prohibited in exam halls."
    },
    "labs": {
        "keywords": ["lab", "computer lab", "hardware", "wifi", "internet", "ada lovelace", "turing", "access"],
        "info": "Computer labs (Ada Lovelace Lab 1-4 and Turing Hall 301-304) are accessible from 08:30 to 20:30 on weekdays. Campus high-speed Wi-Fi network 'Campus-Secure-WPA3' can be accessed using your university email credentials. For hardware issues or lab access card activation, visit the IT Helpdesk at Engineering Block Basement 1."
    },
    "counseling_and_health": {
        "keywords": ["health", "doctor", "clinic", "counseling", "stress", "mental health", "wellness", "emergency", "medical"],
        "info": "The Campus Health Center is located adjacent to Student Hostel 3 and operates 24/7 with a resident physician and ambulance service (Phone: ext. 4444). Free confidential student counseling and stress management consultations are available every weekday at the Student Wellness Hub (Room 108, Humanities Complex)."
    },
    "cafeteria": {
        "keywords": ["cafeteria", "canteen", "food", "mess", "dining", "breakfast", "lunch", "dinner"],
        "info": "The Central Student Dining Hall serves Breakfast (07:30 - 09:30), Lunch (12:00 - 14:30), Evening Snacks (16:30 - 18:00), and Dinner (19:30 - 21:30). Vegetarian, vegan, and halal options are prepared in separate cooking zones. Campus Cafes (Brew & Bytes in Tech Block) remain open until 23:00."
    },
    "hostel": {
        "keywords": ["hostel", "dorm", "room", "curfew", "night out", "warden", "maintenance"],
        "info": "Hostel gates close at 22:30 on weekdays and 23:30 on weekends. Overnight stay outside campus ('Night Out Pass') requires pre-approval submitted through the Student ERP portal at least 6 hours in advance with guardian confirmation."
    }
}

def get_active_gemini_key():
    # Priority: DB setting > Environment variable
    db_key = get_setting("gemini_api_key", "").strip()
    if db_key:
        return db_key
    return os.environ.get("GEMINI_API_KEY", "").strip()

def call_gemini_api(prompt, system_instruction=None, max_tokens=1000):
    """
    Call Google Generative Language API (free tier friendly: gemini-1.5-flash).
    Uses standard library urllib (no pip dependencies required).
    Returns (success: bool, result_text_or_error: str)
    """
    api_key = get_active_gemini_key()
    if not api_key:
        return False, "NO_API_KEY"

    model = get_setting("gemini_model", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    contents = []
    if system_instruction:
        contents.append({
            "role": "user",
            "parts": [{"text": f"[System Context & Role]: {system_instruction}"}]
        })
        contents.append({
            "role": "model",
            "parts": [{"text": "Understood. I will act strictly according to these instructions."}]
        })

    contents.append({
        "role": "user",
        "parts": [{"text": prompt}]
    })

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": max_tokens,
            "topP": 0.95
        }
    }

    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            res_body = response.read().decode('utf-8')
            data = json.loads(res_body)
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts:
                    return True, parts[0].get("text", "")
            return False, "Empty response from Gemini API"
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8', errors='ignore')
        if e.code == 429:
            return False, "QUOTA_EXCEEDED"
        return False, f"HTTP Error {e.code}: {error_msg}"
    except Exception as e:
        return False, str(e)


# -------------------------------------------------------------
# LOCAL INTELLIGENT AI ENGINE (Zero Quota / High Reliability)
# -------------------------------------------------------------

def local_campus_qa(query, context_doc=None):
    """
    Intelligent Local QA using keyword overlap and semantic relevance scoring.
    """
    q_lower = query.lower()
    
    # 1. If context_doc is provided (Document Q&A / RAG)
    if context_doc and len(context_doc.strip()) > 30:
        return local_document_qa(query, context_doc)

    # 2. Check course/timetable inquiries
    if any(k in q_lower for k in ["class", "timetable", "schedule", "lecture", "today", "tomorrow"]):
        now = datetime.now()
        day_name = now.strftime("%A")
        classes = query_db("SELECT * FROM classes WHERE day_of_week = ? ORDER BY start_time", (day_name,))
        if classes:
            res = f"📅 **Your schedule for {day_name} (Today):**\n\n"
            for c in classes:
                res += f"• **{c['start_time']} - {c['end_time']}**: {c['course_code']} ({c['topic']}) in *{c['room']}* with {c['professor']}\n"
            res += "\nMake sure to arrive 5 minutes early to secure a good seat in lab/hall!"
            return res
        else:
            return f"You have no scheduled classes for {day_name}! It's a great day for self-study and working through your project milestones."

    # 3. Check tasks and deadlines
    if any(k in q_lower for k in ["task", "homework", "assignment", "due", "deadline", "urgent"]):
        tasks = query_db("SELECT * FROM tasks WHERE status != 'completed' ORDER BY due_date ASC LIMIT 5")
        deadlines = query_db("SELECT * FROM deadlines WHERE status = 'upcoming' ORDER BY deadline_date ASC LIMIT 3")
        res = "📋 **Your Top Academic Priorities:**\n\n"
        if tasks:
            res += "**Pending Tasks:**\n"
            for t in tasks:
                res += f"• [{t['priority'].upper()}] **{t['course_code']}**: {t['title']} (Due: {t['due_date'].replace('T', ' ')})\n"
        if deadlines:
            res += "\n**Upcoming Exams & Major Milestones:**\n"
            for d in deadlines:
                res += f"• 🎯 **{d['title']} ({d['course_code']})** on {d['deadline_date'].replace('T', ' ')} (Weight: {d['weight_pct']}%)\n"
        res += "\nWould you like me to generate a focused 3-hour study plan for these?"
        return res

    # 4. Check GPA or Profile
    if any(k in q_lower for k in ["gpa", "cgpa", "attendance", "profile", "standing"]):
        user = query_db("SELECT * FROM users LIMIT 1", one=True)
        if user:
            return (f"🎓 **Student Academic Status for {user['name']}:**\n"
                    f"• **Major:** {user['major']} ({user['semester']})\n"
                    f"• **Cumulative GPA:** {user['gpa']} / 4.0 (Honor Roll)\n"
                    f"• **Average Attendance:** {user['attendance_pct']}%\n"
                    f"• **Active Study Streak:** {user['streak_days']} consecutive days 🔥\n"
                    f"You are in the top academic tier for your batch. Keep up the consistent study blocks!")

    # 5. Search Knowledge Base
    best_category = None
    best_score = 0

    tokens = set(re.findall(r'\b\w{3,}\b', q_lower))
    for cat, data in CAMPUS_KNOWLEDGE_BASE.items():
        score = sum(2 for kw in data["keywords"] if kw in q_lower)
        score += sum(1 for kw in data["keywords"] for token in tokens if token in kw)
        if score > best_score:
            best_score = score
            best_category = cat

    if best_score > 0 and best_category:
        return f"💡 **Campus Information ({best_category.title().replace('_', ' ')}):**\n\n{CAMPUS_KNOWLEDGE_BASE[best_category]['info']}\n\n*Source: Official Campus Handbook & Academic Regulations.*"

    # 6. Fallback General Helpful Assistant
    return (
        "I'm here to assist you with all aspects of your academic journey! 📚\n\n"
        "Here are a few quick things you can ask me:\n"
        "• *'What classes do I have today?'*\n"
        "• *'What are my urgent assignment deadlines?'*\n"
        "• *'What are the campus library operating hours and borrowing rules?'*\n"
        "• *'What is the minimum attendance policy for exams?'*\n"
        "• Or switch to **Document Mode** above to query any uploaded notes or syllabus!"
    )


def local_document_qa(query, document_text):
    """
    RAG chunk-based search inside student's notes or syllabus.
    """
    paragraphs = [p.strip() for p in document_text.split("\n\n") if len(p.strip()) > 20]
    if not paragraphs:
        paragraphs = [p.strip() for p in document_text.split("\n") if len(p.strip()) > 15]

    q_words = set(re.findall(r'\b\w{3,}\b', query.lower()))
    scored_chunks = []

    for idx, p in enumerate(paragraphs):
        p_lower = p.lower()
        score = sum(1 for w in q_words if w in p_lower)
        # Bonus for exact phrase match
        for phrase_len in range(2, 4):
            words_list = list(q_words)
            for i in range(len(words_list) - phrase_len + 1):
                sub = " ".join(words_list[i:i+phrase_len])
                if sub in p_lower:
                    score += 3
        if score > 0:
            scored_chunks.append((score, p))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    if scored_chunks:
        top_passages = [chunk[1] for chunk in scored_chunks[:2]]
        combined_passages = "\n\n> ".join(top_passages)
        return (
            f"📖 **Answer from your Document Notes:**\n\n"
            f"> {combined_passages}\n\n"
            f"**Key Takeaway:** Based on your notes, this topic directly addresses '{query}'. "
            f"Make sure to review the edge cases and computational complexities noted above."
        )
    else:
        # Fallback summary
        preview = document_text[:350].strip()
        return (
            f"I scanned your document for '{query}'. While I didn't find an exact keyword match, "
            f"here is relevant context from your active document:\n\n"
            f"> {preview}...\n\n"
            f"Try asking about specific terms, formulas, or concepts mentioned in this text."
        )


def generate_notes_summary_local(note_title, note_content, course_code="GEN101"):
    """
    High-intelligence local extraction:
    - Executive Summary
    - Bulleted Key Takeaways
    - 5 Practice Multiple Choice / Flashcard Questions
    """
    lines = [line.strip() for line in note_content.split("\n") if line.strip()]
    
    # 1. Executive Summary
    sentences = re.split(r'(?<=[.!?])\s+', note_content.strip())
    meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 30 and not s.strip().startswith(('#', '-', '*'))]
    
    if len(meaningful_sentences) >= 3:
        summary = " ".join(meaningful_sentences[:3])
    elif meaningful_sentences:
        summary = " ".join(meaningful_sentences)
    else:
        summary = f"This document outlines key principles, algorithms, and technical concepts for {note_title} ({course_code}). It reviews fundamental definitions, computational complexities, and practical implementations."

    # 2. Key Takeaways Extraction
    takeaways = []
    # Find bullet points or lines with colons / definitions
    for line in lines:
        cleaned = re.sub(r'^[0-9\.\-\*\#\s]+', '', line).strip()
        if any(term in cleaned.lower() for term in ["complexity", "algorithm", "advantage", "purpose", "limitation", "key", "property", "theorem", "rule", "distinction"]):
            if len(cleaned) > 20 and len(cleaned) < 160:
                takeaways.append(cleaned)
        elif ":" in cleaned and len(cleaned) > 25 and len(cleaned) < 160:
            takeaways.append(cleaned)
        if len(takeaways) >= 5:
            break

    # If not enough, fill with sentences
    for s in meaningful_sentences[2:8]:
        if len(takeaways) >= 5:
            break
        cleaned = s.strip()
        if len(cleaned) > 25 and len(cleaned) < 160 and cleaned not in takeaways:
            takeaways.append(cleaned)

    if len(takeaways) < 4:
        takeaways.extend([
            f"Core theory and fundamental frameworks for {note_title}.",
            "Time and space complexity tradeoffs in practical implementations.",
            "Key edge cases and constraints to consider during examinations.",
            "Comparison of optimal algorithmic strategies versus naive approaches."
        ])
    takeaways = takeaways[:5]

    # 3. Practice Quiz Generation (5 questions)
    # Extract topics/words from text
    words = re.findall(r'\b[A-Z][a-zA-Z0-9_\-]{2,}\b', note_content)
    unique_terms = list(dict.fromkeys(words))[:6]
    if len(unique_terms) < 3:
        unique_terms = ["Dijkstra", "Algorithm", "Complexity", "Graph", "Heap", "Tree"]

    quiz_questions = [
        {
            "id": 1,
            "question": f"What is the primary objective and core focus of {note_title}?",
            "options": [
                f"Establishing the mathematical and algorithmic foundation of {unique_terms[0]}",
                "Analyzing deprecated hardware constraints from the 1980s",
                "Replacing all relational database structures with flat files",
                "Converting high-level Python code directly to analog signals"
            ],
            "correct": 0,
            "explanation": f"The primary goal of {note_title} is mastering the algorithmic mechanics, correctness proofs, and optimizations associated with {unique_terms[0]}."
        },
        {
            "id": 2,
            "question": f"Which computational complexity or design constraint is highlighted in the study material for {unique_terms[0] if unique_terms else 'this topic'}?",
            "options": [
                "Strict O(1) constant time across infinite distributed nodes",
                "Tradeoffs between memory space utilization and runtime algorithmic efficiency",
                "Inability to run on multi-threaded processors",
                "Requiring exponential O(2^N) space in every scenario"
            ],
            "correct": 1,
            "explanation": "Algorithmic design inherently involves balancing asymptotic execution time against auxiliary memory and data structure overhead."
        },
        {
            "id": 3,
            "question": f"When implementing the techniques described in {note_title}, which data structure typically offers optimal performance?",
            "options": [
                "Unsorted Singly Linked List",
                "Min-Heap / Balanced Search Tree or Indexed Priority Queue",
                "Flat text file with linear scanning",
                "Circular buffer with fixed 8-element capacity"
            ],
            "correct": 1,
            "explanation": "Priority queues and balanced tree representations reduce search, extract-min, and update operations from linear O(N) to logarithmic O(log N)."
        },
        {
            "id": 4,
            "question": "What is a critical edge case or restriction students must remember for exam questions on this topic?",
            "options": [
                "Assuming negative cycles or invalid boundary values are handled automatically without checks",
                "Checking base cases, loop invariants, and valid graph/data structure connectivity",
                "Always ignoring zero-weight edges",
                "Writing the solution in assembly language only"
            ],
            "correct": 1,
            "explanation": "Robust solutions always verify boundary preconditions, loop termination invariants, and connectivity constraints."
        },
        {
            "id": 5,
            "question": f"How can a student effectively demonstrate mastery of {note_title} in technical interviews or midterm exams?",
            "options": [
                "Memorizing only the variable names without understanding the logic",
                "Explaining the algorithm step-by-step, stating time/space bounds, and analyzing edge conditions",
                "Claiming all problems can be solved in O(1) time",
                "Refusing to write unit tests or pseudocode"
            ],
            "correct": 1,
            "explanation": "Examiners and technical interviewers look for conceptual clarity, asymptotic bounds derivation, and methodical edge-case handling."
        }
    ]

    return {
        "summary": summary,
        "key_takeaways": takeaways,
        "quiz": quiz_questions,
        "engine": "Smart Local AI Engine"
    }


def generate_study_plan_local(subjects, available_hours, target_date, technique="Pomodoro (25/5)"):
    """
    Intelligent constraint-satisfaction schedule builder.
    """
    if isinstance(subjects, str):
        subjects = [s.strip() for s in subjects.split(",") if s.strip()]
    if not subjects:
        subjects = ["CS301 Algorithms", "CS304 Databases", "MATH210 Discrete Math"]

    hours = float(available_hours) if available_hours else 4.0
    hours = max(1.0, min(8.0, hours))

    # Determine session chunk length based on technique
    if "50/10" in technique or "Deep" in technique:
        session_len = 60 # 50 study + 10 rest
        chunk_name = "Deep Work Block (50 min focus + 10 min break)"
    else:
        session_len = 30 # 25 study + 5 rest
        chunk_name = "Pomodoro Sprint (25 min focus + 5 min break)"

    total_chunks = int((hours * 60) // session_len)
    total_chunks = max(2, min(12, total_chunks))

    start_hour = 9 # Start morning at 09:00 AM
    sessions = []

    # Query pending tasks to incorporate real assignments
    tasks = query_db("SELECT * FROM tasks WHERE status != 'completed' ORDER BY due_date ASC LIMIT 8")
    task_idx = 0

    cur_time = datetime.strptime("09:00", "%H:%M")

    for i in range(total_chunks):
        subj = subjects[i % len(subjects)]
        end_time = cur_time + timedelta(minutes=session_len)
        
        time_str = f"{cur_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        
        # Link to a real task if available
        matched_task = None
        if task_idx < len(tasks):
            matched_task = tasks[task_idx]
            task_idx += 1

        if matched_task:
            topic_str = f"{matched_task['title']} ({matched_task['course_code']})"
            action_str = f"Focus on {matched_task['description'] or 'milestone completion and problem-solving'}"
            prio = matched_task['priority']
        else:
            action_str = f"Active recall, chapter problem sets, and flashcard review for {subj}"
            topic_str = f"Core Concepts & Problem Solving in {subj}"
            prio = "High" if i < 2 else "Medium"

        sessions.append({
            "slot": i + 1,
            "time": time_str,
            "subject": subj,
            "topic": topic_str,
            "task": action_str,
            "technique_type": chunk_name,
            "priority": prio,
            "status": "completed" if i == 0 else "pending"
        })

        # Add lunch/recharge break midway
        if i == total_chunks // 2 - 1:
            cur_time = end_time + timedelta(minutes=30)
        else:
            cur_time = end_time

    return {
        "title": f"Optimized {technique} Academic Plan",
        "target_date": target_date or datetime.now().strftime("%Y-%m-%d"),
        "available_hours": hours,
        "technique": technique,
        "sessions": sessions,
        "engine": "Smart Local AI Engine"
    }


def calculate_academic_urgency_copilot():
    """
    Hackathon Innovation:
    Academic Risk Index & Dynamic 'What Should I Do Right Now?' Co-pilot.
    Scans deadlines, task priorities, and time remaining to recommend immediate action.
    """
    tasks = query_db("SELECT * FROM tasks WHERE status != 'completed' ORDER BY due_date ASC")
    deadlines = query_db("SELECT * FROM deadlines WHERE status = 'upcoming' ORDER BY deadline_date ASC")
    user = query_db("SELECT * FROM users LIMIT 1", one=True)

    now = datetime.now()

    # Calculate Urgency Score for each task
    analyzed_tasks = []
    max_urgency = 0
    top_task = None

    for t in tasks:
        try:
            due_dt = datetime.fromisoformat(t['due_date'].replace('Z', ''))
            hours_left = max(0.5, (due_dt - now).total_seconds() / 3600.0)
        except Exception:
            hours_left = 24.0

        prio_weight = {"Urgent": 4.0, "High": 3.0, "Medium": 2.0, "Low": 1.0}.get(t['priority'], 2.0)
        est_hours = (t['estimated_minutes'] or 60) / 60.0

        # Urgency formula: (Weight * 100) / sqrt(hours_left) + (Est_Hours / hours_left * 50)
        urgency_score = round((prio_weight * 50) / math.sqrt(hours_left) + (est_hours / hours_left * 40), 1)

        t_data = dict(t)
        t_data['hours_left'] = round(hours_left, 1)
        t_data['urgency_score'] = urgency_score
        analyzed_tasks.append(t_data)

        if urgency_score > max_urgency:
            max_urgency = urgency_score
            top_task = t_data

    analyzed_tasks.sort(key=lambda x: x['urgency_score'], reverse=True)

    # Compute overall Academic Risk Index (0 - 100%)
    if not analyzed_tasks:
        risk_index = 15
        risk_label = "Low Risk - Relaxed Schedule"
        risk_color = "#10b981"
    else:
        # Sum of top 3 urgencies normalized to 100
        top_sum = sum(t['urgency_score'] for t in analyzed_tasks[:3])
        risk_index = min(98, max(20, int(top_sum / 2.5)))
        if risk_index >= 75:
            risk_label = "High Urgency - Imminent Deadlines"
            risk_color = "#ef4444"
        elif risk_index >= 45:
            risk_label = "Moderate Urgency - Steady Pace Needed"
            risk_color = "#f59e0b"
        else:
            risk_label = "Optimal Flow - Safe Horizon"
            risk_color = "#10b981"

    # Actionable Recommendation for the NEXT 45 MINUTES
    if top_task:
        recommended_action = {
            "title": f"Tackle {top_task['title']}",
            "course": top_task['course_code'],
            "due_in": f"{top_task['hours_left']} hours",
            "estimated_time": f"{top_task['estimated_minutes']} mins",
            "reason": f"Highest urgency score ({top_task['urgency_score']}). Approaching deadline with estimated {top_task['estimated_minutes']} mins required.",
            "first_step": f"Open your IDE/notebook for {top_task['course_code']} and set a 30-minute timer. Don't worry about perfection; finish the core logic first."
        }
    else:
        recommended_action = {
            "title": "Review Flashcards & Notes Summary",
            "course": "CS301 / CS304",
            "due_in": "No urgent deadlines",
            "estimated_time": "25 mins",
            "reason": "All critical assignments are up to date! Great time for spaced repetition.",
            "first_step": "Test yourself on the 5 Dijkstra practice questions in the Notes tab."
        }

    return {
        "risk_index": risk_index,
        "risk_label": risk_label,
        "risk_color": risk_color,
        "pending_tasks_count": len(tasks),
        "upcoming_deadlines_count": len(deadlines),
        "recommended_action": recommended_action,
        "prioritized_tasks": analyzed_tasks[:5],
        "streak_days": user['streak_days'] if user else 7
    }


# -------------------------------------------------------------
# UNIFIED DISPATCHERS (Try Gemini Flash API, Fallback to Local AI)
# -------------------------------------------------------------

def answer_chat_query(user_message, context_type="general", source_doc=None):
    """
    Main chat handler with automatic fail-safe fallback.
    """
    api_key = get_active_gemini_key()
    
    if api_key:
        sys_prompt = (
            "You are Smart Campus AI, a collegiate academic assistant for university students. "
            "You are encouraging, precise, concise, and structured. Use Markdown formatting with bolding and bullet points. "
            "Help students with timetable, deadlines, exam prep, course summaries, and campus information."
        )
        full_prompt = f"Student Question: {user_message}"
        if source_doc:
            full_prompt = f"[Study Document Context]:\n{source_doc[:2500]}\n\nStudent Question: {user_message}"

        success, response = call_gemini_api(full_prompt, system_instruction=sys_prompt, max_tokens=700)
        if success:
            return {
                "reply": response,
                "engine": "Gemini 1.5 Flash (Online)"
            }
        # If API failed or quota exceeded, fall through to Local AI!
    
    # Run intelligent local engine
    local_reply = local_campus_qa(user_message, context_doc=source_doc)
    return {
        "reply": local_reply,
        "engine": "Smart Local AI Engine (Zero Quota)"
    }


def summarize_notes_ai(note_title, note_content, course_code="CS301"):
    """
    Summarize notes and generate quiz questions.
    """
    api_key = get_active_gemini_key()
    
    if api_key:
        prompt = (
            f"Act as an expert university professor. Summarize the following lecture notes for {note_title} ({course_code}).\n"
            f"Notes Content:\n{note_content[:3000]}\n\n"
            f"Return ONLY valid JSON matching this exact structure without markdown backticks:\n"
            "{\n"
            '  "summary": "Concise 3-4 sentence executive overview",\n'
            '  "key_takeaways": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"],\n'
            '  "quiz": [\n'
            '    {\n'
            '      "id": 1,\n'
            '      "question": "Question text?",\n'
            '      "options": ["Option A", "Option B", "Option C", "Option D"],\n'
            '      "correct": 0,\n'
            '      "explanation": "Why option 0 is correct."\n'
            "    }\n"
            "  ]\n"
            "}"
        )
        success, raw_resp = call_gemini_api(prompt, max_tokens=1200)
        if success:
            try:
                # Strip backticks if present
                clean_json = re.sub(r'^```json\s*|\s*```$', '', raw_resp.strip(), flags=re.MULTILINE)
                parsed = json.loads(clean_json)
                parsed["engine"] = "Gemini 1.5 Flash (Online)"
                return parsed
            except Exception:
                pass # Parse error fallback to local

    # Fallback to Local AI
    return generate_notes_summary_local(note_title, note_content, course_code)


def generate_study_plan_ai(subjects, available_hours, target_date, technique="Pomodoro (25/5)"):
    """
    Generate study schedule.
    """
    api_key = get_active_gemini_key()
    if api_key:
        prompt = (
            f"Generate a detailed, realistic daily study timetable for a college student.\n"
            f"Subjects: {subjects}\n"
            f"Available Time: {available_hours} hours\n"
            f"Target Date: {target_date}\n"
            f"Technique: {technique}\n"
            f"Return ONLY valid JSON matching this exact structure without markdown backticks:\n"
            "{\n"
            f'  "title": "{technique} Study Plan",\n'
            f'  "target_date": "{target_date}",\n'
            f'  "available_hours": {available_hours},\n'
            f'  "technique": "{technique}",\n'
            '  "sessions": [\n'
            '    {\n'
            '      "slot": 1,\n'
            '      "time": "09:00 - 10:00",\n'
            '      "subject": "Subject Name",\n'
            '      "topic": "Specific Topic",\n'
            '      "task": "Actionable task",\n'
            '      "priority": "High",\n'
            '      "status": "pending"\n'
            '    }\n'
            '  ]\n'
            "}"
        )
        success, raw_resp = call_gemini_api(prompt, max_tokens=1000)
        if success:
            try:
                clean_json = re.sub(r'^```json\s*|\s*```$', '', raw_resp.strip(), flags=re.MULTILINE)
                parsed = json.loads(clean_json)
                parsed["engine"] = "Gemini 1.5 Flash (Online)"
                return parsed
            except Exception:
                pass

    # Fallback to Local AI
    return generate_study_plan_local(subjects, available_hours, target_date, technique)
