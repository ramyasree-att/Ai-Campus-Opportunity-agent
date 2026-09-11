# AI Campus Opportunity Agent 🚀

An AI-powered personal career and opportunity discovery assistant built for college students. The system automates the discovery of live internet internships, hackathons, scholarships, and Saturday college events, integrates Google OAuth login, interactive Python/Java/C learning notes, resume parsing, multilingual support (Telugu, Hindi, English), and real-time contact number SMS alerts.

---

## 🌟 What's New & Upgraded

### 1. Automated Python Search Engine & Live Internet Crawler
- **Live Internet Opportunity Sync**: Automatically crawls and searches the web for tech internships, undergraduate scholarships, and Saturday inter-collegiate symposiums/hackathons.
- **Automatic Deadline Guardian**: Automatically checks and declares expired opportunities as `DEADLINE EXPIRED ❌` to prevent students from applying to closed positions.
- **On-Demand Live Sync**: Click **[🔄 Live Internet Sync]** in the header at any time to run the crawler and refresh opportunities.

### 2. Google Gmail OAuth 2.0 Integration
- **One-Click Google Sign-In**: Quick sign-in and registration using Google Gmail credentials on both Login and Registration screens.
- Seamless account and student profile generation.

### 3. Comprehensive Python, Java, and C Programming Learning Notes
- **Interactive Notes Studio**: Access structured learning notes and cheatsheets anytime from the sidebar (**📖 Programming Notes**).
- **Python**: Variables, Collections, OOP, File I/O, Web Scraping & Top 15 Placement Questions with code.
- **Java**: JVM/JDK Architecture, OOP (Inheritance, Polymorphism, Interfaces), Collections Framework, Streams API & Top 15 Placement Questions with code.
- **C Programming**: Pointers & Dynamic Memory (`malloc`/`free`), Structures, Unions, Pointer Arithmetic & Top 15 Placement Questions with code.
- **1-Click Copy Snippets & "Ask AI Advisor"**: Copy code directly to clipboard or ask the AI Advisor for instant explanations.

### 4. Resume Upload & AI Resume Parser
- **Resume Dropzone**: Upload resumes in PDF, DOCX, or TXT during registration or on the Profile page.
- **Skill & Education Extraction**: Automatically extracts candidate skills, programming languages, education, and calculates a **Resume Strength Score** (0–100%).
- Automatically feeds extracted competencies into the AI Opportunity Match Scorer and Eligibility Agent.

### 5. Multilingual Agent Intelligence (English, Telugu, Hindi)
- **Language Switcher**: Switch effortlessly between **English 🇬🇧**, **తెలుగు (Telugu) 🇮🇳**, and **हिन्दी (Hindi) 🇮🇳**.
- **Multilingual AI Career Advisor**: Generates natural, context-aware responses and guidance in the student's chosen language.
- **Multilingual Voice Assistant**: Speech-to-Text and Text-to-Speech tailored for `en-US`, `te-IN`, and `hi-IN`.

### 6. Automated Mobile Contact Number Notifications
- **Real-Time Contact Alerts**: Whenever new matching opportunities/events are crawled from the internet or deadlines approach, SMS notifications are dispatched to the student's registered contact number.
- **Mobile SMS Dispatch Log**: Inspect the log of dispatched SMS alerts anytime via **📱 SMS & Mobile Alerts** in the navigation bar.

---

## Technology Stack

- **Backend**: Python 3.10+, Flask, REST APIs, Werkzeug Security, Python-dotenv, Requests, BeautifulSoup4, PyPDF
- **Database**: SQLite with relational schema (`users`, `profiles`, `skills`, `programming_languages`, `opportunities`, `saved_opportunities`, `applications`, `learning_plans`, `career_roadmaps`, `notifications`, `sms_logs`)
- **Frontend**: HTML5, Vanilla CSS3 (Custom Glassmorphic Tokens, Responsive Grid, JetBrains Mono Code Styling), JavaScript ES6+ (SPA Architecture)
- **AI Integration**: OpenRouter API (with intelligent context-aware heuristic fallback in English, Telugu, and Hindi)
- **Voice Engine**: Web Speech API (Multilingual STT & TTS)

---

## Installation & Running Locally

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment** (optional for OpenRouter / Twilio / Google keys):
   ```bash
   cp .env.example .env
   ```

3. **Run the Flask application**:
   ```bash
   python app.py
   ```

4. **Run End-to-End Test Suite**:
   ```bash
   python test_e2e.py
   ```

5. **Access the application**:
   Open [http://localhost:5000](http://localhost:5000) in your web browser.
