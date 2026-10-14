# 🎓 Smart Campus AI — AI-Powered Academic Life Assistant

[![Built for Hackathons](https://img.shields.io/badge/Hackathon-Ready-indigo.svg)](README.md)
[![Zero Dependency](https://img.shields.io/badge/Dependencies-Zero%20pip%20packages-emerald.svg)](README.md)
[![Dual AI Engine](https://img.shields.io/badge/AI%20Engine-Gemini%20Flash%20%2B%20Local%20NLP-purple.svg)](README.md)
[![Persistent SQLite](https://img.shields.io/badge/Database-SQLite%20ACID-blue.svg)](README.md)

**Smart Campus AI** is an all-in-one, intelligent academic command center built for college students. It centralizes scattered university announcements, class schedules, exam deadlines, and study materials into a unified platform powered by a dual-engine AI assistant.

---

## 🚀 Live Demo & Quick Start (Under 10 Seconds)

### Prerequisites
- Python 3.8+ (Already installed on macOS, Linux, and Windows)
- **Zero external packages required!** (No `pip install`, no `npm install`, zero setup friction)

### Launch the Application
1. Open your terminal and navigate to the project directory:
   ```bash
   cd "/Users/mac/Downloads copy/smart-campus-ai"
   ```
2. Start the application server:
   ```bash
   python3 app.py
   ```
3. Open your web browser and visit:
   ```
   http://localhost:8000
   ```
   *The database automatically initializes and pre-seeds realistic sophomore collegiate demo data (timetables, tasks, exam countdowns, study logs, lecture notes, and quizzes) so you can begin demonstrating immediately!*

---

## 🎯 The Real-World Problem It Solves

College students juggle multiple disconnected portals:
- Timetable changes announced via scattered emails or notice boards
- Assignment deadlines buried in learning management portals (Canvas / Moodle / Blackboard)
- Examination date sheets released in PDFs
- Fragmented lecture slides without concise summaries or practice questions
- Cognitive overload leading to missed deadlines, poor attendance, and academic anxiety

**Smart Campus AI eliminates this friction** by acting as a proactive personal academic co-pilot.

---

## 🌟 Key Features

| Feature | Description |
| :--- | :--- |
| **📊 Student Dashboard** | Real-time overview of today's classes with room numbers and professors, upcoming deadlines, attendance percentage, GPA tracker, and campus news ticker. |
| **🤖 CampusBot AI Chatbot** | Conversational academic assistant trained on university regulations, hostel policies, library hours, and exam rules. Features a **Document Q&A mode** for querying uploaded notes and syllabi. |
| **📝 Smart Task Manager** | Full CRUD task manager with priority filters (`Urgent`, `High`, `Medium`, `Low`), estimated completion times, and a 1-click "Convert to Study Session" action. |
| **⏳ Deadline & Exam Hub** | Real-time countdown clocks (days, hours, minutes, seconds) with visual urgency color-coding and syllabus weightage percentages. |
| **📅 AI Study Planner** | Constraint-satisfaction schedule builder. Students configure available daily hours (1-8 hrs), subjects, and study styles (Pomodoro 25/5 or Deep Work 50/10) to generate day-by-day time-blocked agendas. |
| **📖 Notes Summarizer & Quiz** | Paste lecture text or upload notes to generate an Executive Summary, 5 Core Takeaways, and an **Interactive 5-Question Multiple-Choice Quiz** with instant score tracking and answer explanations. |
| **📢 Campus Notice Board** | Categorized college notices (`Academic`, `Examinations`, `Events`, `Timetable`) with search filtering, urgency tags, pinned announcements, and a submission modal. |
| **📈 Progress & Analytics** | Interactive SVG visualizations: Weekly Study Hours bar chart, Subject Distribution donut chart, and Academic Consistency Index score (0-100). |
| **🌓 Modern Responsive UI/UX** | Cyber-slate dark theme and crisp light theme toggle, glassmorphism cards, mobile navigation drawer, and instant keyboard shortcuts. |

---

## 🏆 Hackathon-Level Innovation: Academic Urgency Co-pilot

Instead of functioning as a passive to-do list, **Smart Campus AI** features a dynamic **Academic Urgency & Risk Engine**:
1. **Urgency Formula:** Continuously evaluates pending tasks and upcoming exams by calculating:
   $$\text{Urgency Score} = \frac{\text{Priority Weight} \times 50}{\sqrt{\text{Hours Remaining}}} + \left(\frac{\text{Est. Effort}}{\text{Hours Remaining}} \times 40\right)$$
2. **"What Should I Do Right Now?" Widget:** Identifies the #1 highest-impact academic task for the current hour, explains *why* it matters, and gives a clear 30-minute first step to conquer procrastination.
3. **Academic Risk Meter (0-100%):** Visual warning indicator alerting students before academic workload spirals out of control.

---

## 💡 Dual-Engine AI Architecture (Free-Tier & Offline Proof)

The app is designed to **never fail during a live presentation**:

1. **Free-Tier Google Gemini Flash API:**
   - Supports `gemini-1.5-flash` or `gemini-2.5-flash` with strict token caps to remain within free quotas.
   - Configurable via the UI Settings modal or `GEMINI_API_KEY` environment variable.
2. **Built-in Smart Local AI Engine:**
   - Operates **100% offline with zero quota consumption**.
   - Uses TF-IDF keyword extraction, regex semantic chunking, and heuristic constraint scheduling.
   - If the Gemini API key is missing or encounters HTTP 429 (quota exceeded), the system seamlessly and automatically falls back to the Local AI Engine without displaying errors.

---

## 📁 Project Architecture

```
smart-campus-ai/
├── app.py                     # HTTP server & REST API router (Standard library)
├── database.py                # SQLite schema, migrations, and CRUD helpers
├── ai_engine.py               # Dual-Engine: Free Gemini Flash + Intelligent Local Fallback
├── sample_data.py             # Realistic university demo data seeder
├── test_suite_internal.py     # Automated 14-point test suite
├── test_app.py                # Network-level integration test suite
├── README.md                  # Complete documentation and setup guide
├── presentation.md            # Hackathon pitch deck and demonstration script
└── static/
    ├── index.html             # Semantic Single-Page Application interface
    ├── css/
    │   ├── styles.css         # Design system, CSS variables, dark/light themes
    │   └── components.css     # Widgets, chat, quiz, and charts styling
    └── js/
        ├── api.js             # Async REST API client
        ├── store.js           # Reactive store, toasts, modals, markdown renderer
        ├── app.js             # Router, theme toggle, search, and settings
        ├── dashboard.js       # Dashboard view and timetable controller
        ├── chat.js            # CampusBot AI conversation & document Q&A
        ├── tasks.js           # Task manager with filters and status toggles
        ├── deadlines.js       # Live countdown timers and exam cards
        ├── planner.js         # AI Study schedule generator & session toggles
        ├── notes.js           # Notes summarizer & interactive 5-question quiz
        ├── announcements.js   # Campus notices feed and submission form
        └── tracker.js         # Progress charts (pure responsive SVG)
```

---

## 🧪 Running Automated Tests

Run the comprehensive test suite directly from your terminal:
```bash
python3 test_suite_internal.py
```
*Outputs verification across all 14 database models, AI summarizers, study planners, and REST endpoints.*

---

## 🔮 Future Scope
- **LMS Bi-directional Sync:** Canvas, Moodle, and Google Classroom webhooks.
- **Push & WhatsApp Notifications:** Telegram / WhatsApp reminders for morning classes.
- **Peer Study Pods:** Collaborative Pomodoro rooms with shared study goals.
- **Audio Note Transcription:** Whisper API integration for live classroom lecture transcription.
