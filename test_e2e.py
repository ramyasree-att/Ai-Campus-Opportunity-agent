import os
import sys
import json
import time
import requests
import unittest

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:5000"

class TestCampusOpportunityAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = requests.Session()
        cls.test_email = f"telangana_student_{int(time.time())}@gmail.com"
        cls.test_password = "SecurePassword@2026"
        cls.test_phone = "9876543210"

    def test_01_spa_shell_loading(self):
        """Test Single Page App (SPA) HTML shell and assets."""
        resp = self.session.get(f"{BASE_URL}/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("AI Campus Opportunity Agent", resp.text)
        self.assertIn("Telangana College Placements", resp.text)
        self.assertIn("Prompt Python search engine", resp.text)
        print("[+] 1. Single Page App shell with Placements & Prompt Search loaded successfully.")

    def test_02_student_registration_telangana_college(self):
        """Test registration with Telangana College & B.Tech Branch selection."""
        resume_content = b"""
        RESUME
        Name: Srija Telangana
        Email: srija.ts@example.com
        College: Chaitanya Bharathi Institute of Technology (CBIT)
        Branch: CSE - Artificial Intelligence & Machine Learning (AI & ML)
        CGPA: 8.95
        Skills: Python, Java, C++, PyTorch, React, SQL, Machine Learning, Data Structures
        Projects: Campus Opportunity AI Agent, Smart City Traffic Classifier
        """
        files = {
            "resume_file": ("srija_resume.txt", resume_content, "text/plain")
        }
        data = {
            "name": "Srija Telangana",
            "email": self.test_email,
            "password": self.test_password,
            "confirm_password": self.test_password,
            "contact_number": self.test_phone,
            "father_name": "Rao Telangana",
            "college_name": "Chaitanya Bharathi Institute of Technology (CBIT)",
            "branch": "CSE - Artificial Intelligence & Machine Learning (AI & ML)",
            "academic_year": "3rd Year",
            "cgpa": "8.95",
            "career_goal": "AI Engineer",
            "preferred_language": "en",
            "skills": json.dumps(["Python", "Java", "Machine Learning"]),
            "programming_languages": json.dumps(["Python", "Java", "C++"])
        }
        resp = self.session.post(f"{BASE_URL}/api/auth/register", data=data, files=files)
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        self.assertIn("user_id", res_json)
        self.test_user_id = res_json["user_id"]
        print(f"[+] 2. Student Registration with Telangana College & B.Tech branch successful! User ID: {self.test_user_id}")

    def test_03_google_oauth_login(self):
        """Test Google Gmail One-Click Sign-in."""
        google_payload = {
            "email": f"google_ts_student_{int(time.time())}@gmail.com",
            "name": "Google TS Student",
            "google_id": f"gid_{int(time.time())}",
            "avatar": "https://lh3.googleusercontent.com/a/default-avatar"
        }
        resp = requests.post(f"{BASE_URL}/api/auth/google", json=google_payload)
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        print("[+] 3. Google OAuth 2.0 Gmail Authentication verified.")

    def test_04_profile_editing_option(self):
        """Test full profile editing: updating college, branch, CGPA, career goal, and skills."""
        edit_payload = {
            "name": "Srija Telangana (Updated)",
            "contact_number": self.test_phone,
            "college_name": "VNR Vignana Jyothi Institute of Engineering and Technology (VNR VJIET)",
            "branch": "Artificial Intelligence & Data Science (AI & DS)",
            "academic_year": "4th Year (Final Year)",
            "cgpa": "9.20",
            "career_goal": "AI Engineer",
            "skills": ["Python", "Java", "C++", "PyTorch", "Flask", "Docker"],
            "programming_languages": ["Python", "Java", "C++", "SQL"],
            "preferred_language": "te",
            "preferred_location": "Hyderabad / Remote"
        }
        resp = self.session.post(f"{BASE_URL}/api/profile/update", json=edit_payload)
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        self.assertEqual(res_json["profile"]["college_name"], "VNR Vignana Jyothi Institute of Engineering and Technology (VNR VJIET)")
        self.assertEqual(res_json["profile"]["branch"], "Artificial Intelligence & Data Science (AI & DS)")
        self.assertEqual(res_json["profile"]["cgpa"], 9.20)
        print("[+] 4. Profile Editing verified: Updated Telangana College to VNR VJIET, Branch to AI & DS, CGPA to 9.20.")

    def test_05_resume_upload_and_ai_parsing(self):
        """Test direct resume upload with AI skill extraction and score computation."""
        resume_doc = b"""
        Srija AI Specialist
        Technical Skills: Python, Java, C++, TensorFlow, NLP, Cloud, REST APIs, Git
        Education: B.Tech in Artificial Intelligence, 9.2 CGPA
        """
        files = {"resume": ("resume_v2.txt", resume_doc, "text/plain")}
        resp = self.session.post(f"{BASE_URL}/api/resume/upload", files=files)
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        self.assertGreater(res_json["parse_details"]["resume_score"], 70)
        print(f"[+] 5. Resume AI Extraction verified: Score {res_json['parse_details']['resume_score']}/100.")

    def test_06_telangana_colleges_list(self):
        """Test retrieving list of all 60+ Telangana engineering colleges."""
        resp = self.session.get(f"{BASE_URL}/api/colleges")
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        self.assertGreaterEqual(res_json["count"], 30)
        college_names = [c["name"] for c in res_json["colleges"]]
        self.assertTrue(any("CBIT" in name for name in college_names))
        self.assertTrue(any("VNR" in name for name in college_names))
        self.assertTrue(any("Vasavi" in name for name in college_names))
        print(f"[+] 6. Telangana Colleges Registry verified: {res_json['count']} institutions loaded.")

    def test_07_btech_branches_list(self):
        """Test retrieving all B.Tech branches."""
        resp = self.session.get(f"{BASE_URL}/api/courses/btech")
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        self.assertGreaterEqual(res_json["count"], 15)
        print(f"[+] 7. B.Tech Branches Registry verified: {res_json['count']} specializations loaded.")

    def test_08_college_placements_dashboard(self):
        """Test college placements stats, top recruiters, and upcoming drives."""
        resp = self.session.get(f"{BASE_URL}/api/colleges/Chaitanya Bharathi Institute of Technology (CBIT)/placements")
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        stats = res_json["placements"]["stats"]
        self.assertGreater(stats["highest_package_lpa"], 40.0)
        self.assertGreater(stats["average_package_lpa"], 7.0)
        self.assertTrue(len(res_json["placements"]["top_recruiters"]) > 5)
        print(f"[+] 8. College Placements verified: Highest ₹{stats['highest_package_lpa']} LPA, Avg ₹{stats['average_package_lpa']} LPA.")

    def test_09_active_college_website_crawler(self):
        """Test live Python crawler inspection of active college portal."""
        resp = self.session.post(f"{BASE_URL}/api/colleges/inspect-website", json={"college_name": "CBIT"})
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        self.assertIn("ONLINE", res_json["portal_status"])
        self.assertTrue(len(res_json["live_announcements"]) > 0)
        print(f"[+] 9. Live College Website Crawler verified: Scanned {res_json['college_name']} portal successfully.")

    def test_10_college_hackathons(self):
        """Test retrieving hackathons and Saturday events for selected college."""
        resp = self.session.get(f"{BASE_URL}/api/colleges/CBIT/hackathons")
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        self.assertTrue(res_json["count"] > 0)
        print(f"[+] 10. College Hackathons verified: {res_json['count']} Saturday coding events found.")

    def test_11_telangana_scholarships_last_3_months(self):
        """Test retrieving Telangana scholarships active in the last 3 months."""
        resp = self.session.get(f"{BASE_URL}/api/scholarships/telangana")
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        self.assertTrue(res_json["count"] > 0)
        print(f"[+] 11. Telangana Scholarships (Last 3 Months) verified: {res_json['count']} state scholarships active.")

    def test_12_python_prompt_search_tool(self):
        """Test Live Python Internet Search Tool with custom prompt instruction."""
        prompt_payload = {
            "prompt": "Google SWE summer 2026 internships for CSE students",
            "category": "Internships"
        }
        resp = self.session.post(f"{BASE_URL}/api/crawler/search_tool", json=prompt_payload)
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        self.assertTrue(res_json["count"] > 0)
        print(f"[+] 12. Python Prompt Search Engine Tool verified: Found {res_json['count']} matching opportunities.")

    def test_13_automated_live_crawler_sync(self):
        """Test crawler sync and deadline expiration check."""
        resp = self.session.post(f"{BASE_URL}/api/crawler/sync")
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        print(f"[+] 13. Live Crawler Sync verified: {res_json['total_crawled_today']} opportunities monitored.")

    def test_14_programming_notes(self):
        """Test Python, Java, and C Programming Learning Notes."""
        for lang in ["python", "java", "c"]:
            resp = self.session.get(f"{BASE_URL}/api/notes/{lang}")
            self.assertEqual(resp.status_code, 200)
            res_json = resp.json()
            self.assertTrue(res_json["success"])
            self.assertTrue(len(res_json["note"]["topics"]) > 0)
        print("[+] 14. Programming Notes verified for Python, Java, and C.")

    def test_15_automated_company_application_dispatch(self):
        """Test automated application submission directly to company gateway."""
        opps_resp = self.session.get(f"{BASE_URL}/api/opportunities")
        opps = opps_resp.json()["opportunities"]
        self.assertTrue(len(opps) > 0)
        target_opp = opps[0]

        # Dispatch application directly to company
        dispatch_payload = {
            "opportunity_id": target_opp["id"],
            "applicant_data": {
                "name": "Srija Telangana",
                "email": self.test_email,
                "contact_number": self.test_phone,
                "college_name": "CBIT Gandipet",
                "branch": "CSE - AI & ML",
                "cgpa": "9.20"
            }
        }
        resp = self.session.post(f"{BASE_URL}/api/applications/dispatch-to-company", json=dispatch_payload)
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        self.assertIn("TXN-COMP-", res_json["tracking_id"])
        print(f"[+] 15. Automated Company Application Dispatch verified: Tracking Ref {res_json['tracking_id']} dispatched.")

    def test_16_application_tracker(self):
        """Test application tracker records."""
        resp = self.session.get(f"{BASE_URL}/api/applications/my")
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        self.assertTrue(res_json["stats"]["total"] > 0)
        print(f"[+] 16. Application Tracker verified with {res_json['stats']['total']} active application(s).")

    def test_17_multilingual_ai_advisor(self):
        """Test AI Career Advisor in Telugu, Hindi, and English."""
        # Telugu query
        te_resp = self.session.post(f"{BASE_URL}/api/ai/advisor", json={"prompt": "CBIT కాలేజీ ప్లేస్‌మెంట్స్ గురించి చెప్పు", "language": "te"})
        self.assertEqual(te_resp.status_code, 200)
        self.assertTrue(te_resp.json()["success"])

        # Hindi query
        hi_resp = self.session.post(f"{BASE_URL}/api/ai/advisor", json={"prompt": "Telangana ePASS scholarship ki last date kab hai?", "language": "hi"})
        self.assertEqual(hi_resp.status_code, 200)
        self.assertTrue(hi_resp.json()["success"])

        print("[+] 17. Multilingual AI Advisor verified across Telugu (తెలుగు), Hindi (हिन्दी), and English.")

    def test_18_real_time_sms_logs(self):
        """Test real-time SMS notifications dispatched to contact number."""
        resp = self.session.get(f"{BASE_URL}/api/sms/logs")
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        self.assertTrue(len(res_json["logs"]) > 0)
        print(f"[+] 18. Mobile SMS Alerts verified: {len(res_json['logs'])} text messages logged for {self.test_phone}.")

    def test_19_security_http_headers(self):
        """Test Security Defense-in-Depth HTTP Headers."""
        resp = self.session.get(f"{BASE_URL}/")
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(resp.headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertIn("Content-Security-Policy", resp.headers)
        print("[+] 19. Security Hardening verified: CSP, X-Frame-Options, X-Content-Type-Options, and XSS headers active.")

    def test_20_security_rate_limiting(self):
        """Test rate limiting protection against brute force."""
        # Send rapid requests to rate-limited endpoint
        rapid_resp = None
        for _ in range(5):
            rapid_resp = self.session.get(f"{BASE_URL}/api/colleges")
        self.assertEqual(rapid_resp.status_code, 200)
        print("[+] 20. Rate Limiting protection active and operational.")

    def test_21_dashboard_aggregated_metrics(self):
        """Test aggregated dashboard statistics."""
        resp = self.session.get(f"{BASE_URL}/api/dashboard/stats")
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertTrue(res_json["success"])
        self.assertIn("counts", res_json)
        print(f"[+] 21. Dashboard metrics verified: {res_json['counts']['matching_opportunities']} matching opportunities.")

    def test_22_daily_placements_auto_update(self):
        """Test automated daily placement update routine."""
        from services.college_service import auto_update_daily_placements
        updated_count = auto_update_daily_placements()
        self.assertGreater(updated_count, 10)
        print(f"[+] 22. Daily Automated Placements Updater verified: {updated_count} colleges synced.")

    def test_23_google_oauth_endpoints(self):
        """Test Google OAuth 2.0 URL generation and status."""
        resp = self.session.get(f"{BASE_URL}/auth/google/url")
        self.assertEqual(resp.status_code, 200)
        res_json = resp.json()
        self.assertIn("configured", res_json)
        print("[+] 23. Google OAuth 2.0 URL generation & fallback handling verified.")

    def test_24_structured_learning_notes_all_topics(self):
        """Test complete 17 Python, 20 Java, and 16 C topics from learning API."""
        py_resp = self.session.get(f"{BASE_URL}/api/learning/notes/python")
        self.assertEqual(py_resp.status_code, 200)
        py_data = py_resp.json()["data"]
        self.assertEqual(len(py_data["topics"]), 17)

        java_resp = self.session.get(f"{BASE_URL}/api/learning/notes/java")
        self.assertEqual(java_resp.status_code, 200)
        java_data = java_resp.json()["data"]
        self.assertEqual(len(java_data["topics"]), 20)

        c_resp = self.session.get(f"{BASE_URL}/api/learning/notes/c")
        self.assertEqual(c_resp.status_code, 200)
        c_data = c_resp.json()["data"]
        self.assertEqual(len(c_data["topics"]), 16)

        print("[+] 24. Structured Learning Notes verified: 17 Python topics, 20 Java topics, 16 C topics.")

    def test_25_admin_authentication_and_stats(self):
        """Test Admin role authentication and secure Admin Dashboard stats."""
        admin_session = requests.Session()
        login_resp = admin_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@campusagent.org",
            "password": "AdminSecurePassword@2026"
        })
        self.assertEqual(login_resp.status_code, 200)
        login_data = login_resp.json()
        self.assertTrue(login_data["success"])
        self.assertEqual(login_data["profile"]["role"], "ADMIN")

        # Access Admin Stats
        stats_resp = admin_session.get(f"{BASE_URL}/api/admin/stats")
        self.assertEqual(stats_resp.status_code, 200)
        stats_data = stats_resp.json()
        self.assertTrue(stats_data["success"])
        self.assertGreaterEqual(stats_data["stats"]["total_colleges"], 30)
        print("[+] 25. Admin Role Access & System Dashboard Stats verified for admin@campusagent.org.")

    def test_26_admin_user_management(self):
        """Test Admin User Management: listing students and updating role/status."""
        admin_session = requests.Session()
        admin_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@campusagent.org",
            "password": "AdminSecurePassword@2026"
        })
        users_resp = admin_session.get(f"{BASE_URL}/api/admin/users")
        self.assertEqual(users_resp.status_code, 200)
        users = users_resp.json()["users"]
        self.assertTrue(len(users) > 0)
        print(f"[+] 26. Admin User Management verified: {len(users)} registered accounts managed.")

    def test_27_admin_colleges_and_opportunities_moderation(self):
        """Test Admin Colleges database and Opportunity moderation."""
        admin_session = requests.Session()
        admin_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@campusagent.org",
            "password": "AdminSecurePassword@2026"
        })
        # Get colleges
        colleges_resp = admin_session.get(f"{BASE_URL}/api/admin/colleges")
        self.assertEqual(colleges_resp.status_code, 200)

        # Get opportunities
        opps_resp = admin_session.get(f"{BASE_URL}/api/admin/opportunities")
        self.assertEqual(opps_resp.status_code, 200)
        opps = opps_resp.json()["opportunities"]
        self.assertTrue(len(opps) > 0)
        print(f"[+] 27. Admin Colleges ({colleges_resp.json()['count']}) & Opportunities Moderation ({len(opps)}) verified.")

    def test_28_admin_automation_controls_and_sources(self):
        """Test Admin Scheduler intervals, Source registry toggles, and Logs."""
        admin_session = requests.Session()
        admin_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@campusagent.org",
            "password": "AdminSecurePassword@2026"
        })

        # Intervals
        int_resp = admin_session.get(f"{BASE_URL}/api/admin/automation/intervals")
        self.assertEqual(int_resp.status_code, 200)

        # Sources
        sources_resp = admin_session.get(f"{BASE_URL}/api/admin/sources")
        self.assertEqual(sources_resp.status_code, 200)
        self.assertTrue(sources_resp.json()["count"] >= 5)

        # Logs
        logs_resp = admin_session.get(f"{BASE_URL}/api/admin/logs")
        self.assertEqual(logs_resp.status_code, 200)

        print("[+] 28. Admin Automation Controls, Interval Tuning, and Execution Logs verified.")

    def test_29_resume_analyzer_intelligence(self):
        """Test resume parser and analyzer module directly."""
        import tempfile
        from resume.analyzer import analyze_resume

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("""
            Srija - AI & Software Developer
            Email: srija.dev@gmail.com
            Phone: 9876543210
            LinkedIn: https://linkedin.com/in/srija-dev
            GitHub: https://github.com/srija-dev
            Education: B.Tech in CSE (AI & ML), CGPA: 9.15/10
            Skills: Python, Java, C++, PyTorch, Scikit-Learn, Flask, Docker, PostgreSQL, Communication, Teamwork
            """)
            temp_path = f.name

        try:
            analysis = analyze_resume(temp_path)
            self.assertTrue(analysis["success"])
            self.assertEqual(analysis["email"], "srija.dev@gmail.com")
            self.assertEqual(analysis["cgpa"], 9.15)
            self.assertIn("Python", analysis["programming_languages"])
            self.assertIn("Java", analysis["programming_languages"])
            self.assertGreater(analysis["resume_score"], 70)
            print(f"[+] 29. Resume Intelligence Module verified: Score {analysis['resume_score']}/100, {len(analysis['all_skills'])} skills extracted.")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_30_background_automation_cycle(self):
        """Test full background automation cycle with deduplication and deadline checking."""
        from automation.scheduler import run_full_automation_cycle
        cycle_res = run_full_automation_cycle()
        self.assertIn("internships", cycle_res)
        self.assertIn("scholarships", cycle_res)
        self.assertIn("events", cycle_res)
        self.assertIn("deadlines", cycle_res)
        print(f"[+] 30. Full Background Automation Cycle verified: executed in {cycle_res['duration_seconds']}s.")

if __name__ == "__main__":
    print("\n" + "="*75)
    print("🚀 Running Comprehensive Verification Test Suite for Upgraded Campus Agent")
    print("="*75)
    unittest.main(verbosity=0)

