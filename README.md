🌱 MicroHabit AI

A Smart, Full-Stack Habit Tracking System with AI Coaching.

MicroHabit AI is a sophisticated productivity application built for the 2026 web ecosystem. It moves beyond simple checklists by incorporating real-time data visualization and personalized motivation powered by the Google Gemini 2.0/3.0 SDK.

User1 - kushal
password - 1234

User2 - shaswat
password -123

🚀 Features

1. AI-Powered Coaching

Integrated with the latest Gemini Flash models, the app analyzes your specific habits and provides contextual "Life Hacks" and encouragement. It doesn't just track data; it provides insight.

2. Dynamic Data Visualization

Progress Tracking: A real-time progress bar that changes color (Green to Blue) upon completion.

Celebration Logic: Integrated canvas-confetti triggers when a user hits 100% daily progress.

Horizontal History Chart: A 7-day retrospective view that uses localized date logic to ensure accuracy across timezones (specifically optimized for IST).

3. Robust Authentication & Security

Session Management: Uses Flask-Session with SameSite=Lax and HttpOnly cookies to maintain security without the complexity of manual JWT handling.

Relational Database: SQLite with SQLAlchemy ORM ensures data integrity across Users, Habits, and Completion Logs.

🛠️ Technical Stack

Layer

Technology

Frontend

React.js, CSS-in-JS (Standard Styles), Canvas-Confetti

Backend

Python Flask, Flask-CORS, Flask-SQLAlchemy

Database

SQLite (Relational)

AI Engine

Google Gen AI SDK (google-genai 2026)

Model

gemini-2.0-flash

📂 Project Structure

/assignment
├── app.py              # Flask API, DB Models, & Gemini Integration
├── habits.db           # SQLite Database (Auto-generated)
└── /frontend
    ├── /src
    │   ├── App.js      # Main UI Logic, History Component, & API Layer
    │   └── index.js    # React Entry Point
    └── package.json    # Frontend Dependencies


🧠 Key Technical Decisions & Walkthrough

A. Architecture: Decoupled REST API

The project uses a clean separation between the React frontend and Flask backend. This allows the backend to serve as a secure gateway for sensitive API keys (Gemini) while the frontend focuses on a high-performance, reactive user experience.

B. Data Modeling: The CompletionLog Pattern

To enable historical charts, we implemented a CompletionLog model.

Decision: Instead of a simple is_completed toggle, every checkmark creates a date-stamped entry in a separate logs table.

Reason: This allows for "Group By" SQL queries to generate 7-day trends without bloating the primary Habit table.

C. The "Timezone Trap" Resolution

One of the most critical technical fixes was shifting from UTC-based .toISOString() to Local Date Logic.

Decision: Manual date string construction: `${year}-${month}-${day}`.

Reason: This ensures users in India (IST) see their "28th Feb" progress exactly at 12:00 AM local time, preventing a 5.5-hour delay in data reflection.

D. AI Prompt Engineering

The AI Coach is not a static chatbot. It is fed a "State-Aware" prompt containing:

Current Habit Names.

Completion Status.

Time of Day context.
This results in highly personalized coaching that feels "alive" to the user.

⚠️ Risks & Mitigation

API Deprecation: Addressed Python 3.9 "End of Life" and google-generativeai deprecation by migrating to the google-genai 2026 library.

CORS Conflicts: Resolved through explicit credential support and origin white-listing for localhost:3000.

Scaling: SQLite is perfect for MVP; however, the architecture is "Postgres-Ready" should the user base grow.

⚙️ Setup & Installation

1. Backend (Flask)

uv pip install flask flask-sqlalchemy flask-cors google-genai
python app.py


2. Frontend (React)

cd frontend
npm install canvas-confetti
npm start


3. AI Configuration

Create a free API Key at Google AI Studio and add it to the client initialization in app.py.

🔮 Future Roadmap

Leaderboards: Compare habit streaks with other local users.

Mood Tracking: Let Gemini adjust its coaching tone based on user sentiment.

PWA Support: Convert the horizontal UI into a mobile-installable application.