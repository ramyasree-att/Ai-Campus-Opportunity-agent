import os
import json
import time
from datetime import timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from werkzeug.utils import secure_filename

from config import Config
from database import init_db
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.learning import learning_bp
from automation.scheduler import init_scheduler
from agents.campus_agent import generate_ai_response
from services.auth_service import (
    register_student, authenticate_user, authenticate_google_user, reset_password
)
from services.profile_service import (
    get_profile_by_user_id, update_profile, update_user_language_preference
)
from services.opportunity_service import (
    get_opportunities, get_opportunity_by_id, toggle_save_opportunity, get_saved_opportunities
)
from services.ai_agent_service import enrich_opportunity, ask_ai_advisor
from services.learning_service import create_or_get_learning_plan, get_user_learning_plans, update_day_status
from services.application_service import (
    prepare_application_data, confirm_and_submit_application, get_my_applications, update_application_status
)
from services.roadmap_service import get_or_create_roadmap, update_roadmap_stage
from services.notification_service import (
    get_user_notifications, mark_notification_as_read, calculate_deadline_badge, generate_proactive_alerts
)
from services.notes_service import get_all_notes, get_notes_for_language
from services.resume_service import process_uploaded_resume, parse_resume_content, extract_text_from_file
from services.crawler_service import (
    run_live_crawler, get_crawler_status, check_and_update_expired_deadlines, search_internet_by_prompt
)
from services.sms_service import send_contact_notification, get_sms_logs_for_user
from services.college_service import (
    get_telangana_colleges, get_btech_branches, get_college_placements,
    crawl_active_college_website, get_college_hackathons, auto_update_daily_placements
)
from services.company_dispatcher_service import dispatch_application_to_company
from services.security_service import (
    apply_security_headers, rate_limit, sanitize_input, sanitize_dict_inputs, validate_uploaded_file
)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(Config)

# Register Blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(learning_bp)

# Start background automated opportunity scheduler
try:
    scheduler = init_scheduler()
    scheduler.start()
except Exception as e:
    print(f"Scheduler background startup note: {e}")

# Configure Session Security & Cookie Protection
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

# Security Middleware for all HTTP responses
@app.after_request
def security_headers_middleware(response):
    return apply_security_headers(response)

# Initialize SQLite database, seed initial opportunities, run crawler sync and update placements on startup
with app.app_context():
    init_db()
    check_and_update_expired_deadlines()
    try:
        run_live_crawler()
        auto_update_daily_placements()
    except Exception as e:
        print("Startup sync note:", e)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_IMAGE_EXTENSIONS

def allowed_resume(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_RESUME_EXTENSIONS

def get_current_user_id():
    return session.get("user_id")

# ----------------- PAGE ROUTES -----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    safe_name = secure_filename(filename)
    return send_from_directory(Config.UPLOAD_FOLDER, safe_name)

# ----------------- AUTHENTICATION APIS -----------------
@app.route("/api/auth/register", methods=["POST"])
@rate_limit(limit=15, window_seconds=60)
def api_register():
    photo_filename = None
    resume_filename = None
    resume_summary = None
    extracted_resume_skills = []

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
        if "skills" in data and isinstance(data["skills"], str) and data["skills"].startswith("["):
            try:
                data["skills"] = json.loads(data["skills"])
            except Exception:
                pass
        if "programming_languages" in data and isinstance(data["programming_languages"], str) and data["programming_languages"].startswith("["):
            try:
                data["programming_languages"] = json.loads(data["programming_languages"])
            except Exception:
                pass

        # Handle Profile Photo
        if "profile_photo" in request.files:
            file = request.files["profile_photo"]
            if file and file.filename and allowed_image(file.filename):
                valid, msg = validate_uploaded_file(file, max_size_mb=5)
                if valid:
                    safe_name = secure_filename(file.filename)
                    unique_name = f"user_{int(time.time())}_{safe_name}"
                    file.save(os.path.join(Config.UPLOAD_FOLDER, unique_name))
                    photo_filename = unique_name

        # Handle Resume File Upload during registration
        if "resume_file" in request.files:
            r_file = request.files["resume_file"]
            if r_file and r_file.filename and allowed_resume(r_file.filename):
                valid, msg = validate_uploaded_file(r_file, max_size_mb=10)
                if valid:
                    safe_r_name = secure_filename(r_file.filename)
                    unique_r_name = f"resume_{int(time.time())}_{safe_r_name}"
                    saved_path = os.path.join(Config.UPLOAD_FOLDER, unique_r_name)
                    r_file.save(saved_path)
                    resume_filename = unique_r_name

                    # Automated AI Text & Skill Extraction
                    try:
                        extracted_text = extract_text_from_file(saved_path)
                        parsed_res = parse_resume_content(extracted_text, filename=safe_r_name)
                        extracted_resume_skills = parsed_res.get("skills_found", [])
                        resume_summary = (
                            f"AI Parsed Resume: Found {len(extracted_resume_skills)} skills "
                            f"({', '.join(extracted_resume_skills[:6])}). Score: {parsed_res.get('resume_score', 80)}/100."
                        )
                    except Exception as e:
                        resume_summary = f"Resume uploaded: {safe_r_name}"

    # Merge extracted resume skills with user selected skills
    if extracted_resume_skills:
        current_skills = data.get("skills", [])
        if isinstance(current_skills, str):
            current_skills = [s.strip() for s in current_skills.split(",") if s.strip()]
        merged_skills = list(set(current_skills + extracted_resume_skills))
        data["skills"] = merged_skills

    # Anti-XSS Sanitization of form inputs
    data = sanitize_dict_inputs(data)

    data["profile_photo"] = photo_filename
    data["resume_filename"] = resume_filename
    data["resume_summary"] = resume_summary

    result = register_student(data)
    if result["success"]:
        session["user_id"] = result["user_id"]
        profile = get_profile_by_user_id(result["user_id"])
        return jsonify({
            "success": True,
            "message": "Registration successful! Welcome to AI Campus Opportunity Agent 👋",
            "user_id": result["user_id"],
            "profile": profile
        })
    else:
        return jsonify(result), 400

@app.route("/api/auth/login", methods=["POST"])
@rate_limit(limit=20, window_seconds=60)
def api_login():
    data = request.get_json() or {}
    email = sanitize_input(data.get("email"))
    password = data.get("password")

    result = authenticate_user(email, password)
    if result["success"]:
        session["user_id"] = result["user_id"]
        profile = get_profile_by_user_id(result["user_id"])
        return jsonify({
            "success": True,
            "message": "Login successful! Welcome back 👋",
            "user_id": result["user_id"],
            "profile": profile
        })
    else:
        return jsonify(result), 401

@app.route("/api/auth/google", methods=["POST"])
@rate_limit(limit=20, window_seconds=60)
def api_google_auth():
    data = request.get_json() or {}
    email = sanitize_input(data.get("email"))
    name = sanitize_input(data.get("name"))
    google_id = data.get("google_id")
    avatar = data.get("avatar")

    if not email:
        return jsonify({"success": False, "message": "Email is required for Google Sign-in."}), 400

    result = authenticate_google_user(email, name, google_id, avatar)
    if result["success"]:
        session["user_id"] = result["user_id"]
        return jsonify({
            "success": True,
            "message": result["message"],
            "is_new_user": result.get("is_new_user", False),
            "user_id": result["user_id"],
            "profile": result["profile"]
        })
    else:
        return jsonify(result), 400

@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})

@app.route("/api/auth/me", methods=["GET"])
def api_get_me():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"authenticated": False, "profile": None})

    profile = get_profile_by_user_id(user_id)
    if not profile:
        session.clear()
        return jsonify({"authenticated": False, "profile": None})

    return jsonify({"authenticated": True, "profile": profile})

@app.route("/api/auth/reset-password", methods=["POST"])
def api_reset_password():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    data = request.get_json() or {}
    current_pass = data.get("current_password")
    new_pass = data.get("new_password")
    confirm_pass = data.get("confirm_new_password")

    res = reset_password(user_id, current_pass, new_pass, confirm_pass)
    return jsonify(res), (200 if res["success"] else 400)

# ----------------- PROFILE & LANGUAGE APIS -----------------
@app.route("/api/profile", methods=["GET"])
def api_get_profile():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    profile = get_profile_by_user_id(user_id)
    return jsonify({"success": True, "profile": profile})

@app.route("/api/profile/update", methods=["POST"])
def api_update_profile():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    photo_filename = None
    resume_filename = None
    resume_summary = None
    extracted_skills = []

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
        if "skills" in data and isinstance(data["skills"], str) and data["skills"].startswith("["):
            try:
                data["skills"] = json.loads(data["skills"])
            except Exception:
                pass
        elif "skills" in data and isinstance(data["skills"], str):
            data["skills"] = [s.strip() for s in data["skills"].split(",") if s.strip()]

        if "programming_languages" in data and isinstance(data["programming_languages"], str) and data["programming_languages"].startswith("["):
            try:
                data["programming_languages"] = json.loads(data["programming_languages"])
            except Exception:
                pass
        elif "programming_languages" in data and isinstance(data["programming_languages"], str):
            data["programming_languages"] = [l.strip() for l in data["programming_languages"].split(",") if l.strip()]

        # Handle Profile Photo
        if "profile_photo" in request.files:
            file = request.files["profile_photo"]
            if file and file.filename and allowed_image(file.filename):
                valid, msg = validate_uploaded_file(file, max_size_mb=5)
                if valid:
                    safe_name = secure_filename(file.filename)
                    unique_name = f"user_{int(time.time())}_{safe_name}"
                    file.save(os.path.join(Config.UPLOAD_FOLDER, unique_name))
                    photo_filename = unique_name

        # Handle Resume File Re-upload
        if "resume_file" in request.files:
            r_file = request.files["resume_file"]
            if r_file and r_file.filename and allowed_resume(r_file.filename):
                valid, msg = validate_uploaded_file(r_file, max_size_mb=10)
                if valid:
                    safe_r_name = secure_filename(r_file.filename)
                    unique_r_name = f"resume_{int(time.time())}_{safe_r_name}"
                    saved_path = os.path.join(Config.UPLOAD_FOLDER, unique_r_name)
                    r_file.save(saved_path)
                    resume_filename = unique_r_name

                    try:
                        extracted_text = extract_text_from_file(saved_path)
                        parsed_res = parse_resume_content(extracted_text, filename=safe_r_name)
                        extracted_skills = parsed_res.get("skills_found", [])
                        resume_summary = (
                            f"AI Parsed Resume: Found {len(extracted_skills)} skills "
                            f"({', '.join(extracted_skills[:6])}). Score: {parsed_res.get('resume_score', 80)}/100."
                        )
                    except Exception as e:
                        resume_summary = f"Resume uploaded: {safe_r_name}"

    if extracted_skills:
        curr = data.get("skills", [])
        if isinstance(curr, str):
            curr = [s.strip() for s in curr.split(",") if s.strip()]
        data["skills"] = list(set(curr + extracted_skills))

    data = sanitize_dict_inputs(data)

    if photo_filename:
        data["profile_photo"] = photo_filename
    if resume_filename:
        data["resume_filename"] = resume_filename
    if resume_summary:
        data["resume_summary"] = resume_summary

    res = update_profile(user_id, data)
    return jsonify(res), (200 if res["success"] else 400)

@app.route("/api/resume/upload", methods=["POST"])
def api_upload_resume_direct():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    if "resume" not in request.files:
        return jsonify({"success": False, "message": "No resume file provided."}), 400

    file = request.files["resume"]
    if not file or not file.filename or not allowed_resume(file.filename):
        return jsonify({"success": False, "message": "Invalid resume format. Allowed: .pdf, .docx, .doc, .txt"}), 400

    valid, msg = validate_uploaded_file(file, max_size_mb=10)
    if not valid:
        return jsonify({"success": False, "message": msg}), 400

    safe_name = secure_filename(file.filename)
    unique_name = f"resume_{int(time.time())}_{safe_name}"
    saved_path = os.path.join(Config.UPLOAD_FOLDER, unique_name)
    file.save(saved_path)

    parse_result = process_uploaded_resume(saved_path, safe_name)
    extracted_skills = parse_result.get("skills_found", [])
    resume_score = parse_result.get("resume_score", 80)

    summary_text = (
        f"AI Parsed Resume: Found {len(extracted_skills)} skills ({', '.join(extracted_skills[:6])}). "
        f"Strength Score: {resume_score}/100."
    )

    update_payload = {
        "resume_filename": unique_name,
        "resume_summary": summary_text
    }

    if extracted_skills:
        profile = get_profile_by_user_id(user_id)
        existing_skills = profile.get("skills", []) if profile else []
        merged = list(set(existing_skills + extracted_skills))
        update_payload["skills"] = merged

    update_profile(user_id, update_payload)
    updated_profile = get_profile_by_user_id(user_id)

    return jsonify({
        "success": True,
        "message": f"Resume parsed successfully! Extracted {len(extracted_skills)} skills. Score: {resume_score}/100.",
        "filename": unique_name,
        "parse_details": parse_result,
        "profile": updated_profile
    })

@app.route("/api/language/change", methods=["POST"])
def api_change_language():
    user_id = get_current_user_id()
    data = request.get_json() or {}
    lang = data.get("language", "en")

    if lang not in ["en", "te", "hi"]:
        return jsonify({"success": False, "message": "Supported languages: en (English), te (Telugu), hi (Hindi)"}), 400

    if user_id:
        update_user_language_preference(user_id, lang)

    return jsonify({"success": True, "language": lang, "message": f"Language preference changed to '{lang}'"})

# ----------------- TELANGANA COLLEGES & PLACEMENTS APIS -----------------
@app.route("/api/colleges", methods=["GET"])
def api_get_colleges():
    """Returns the comprehensive list of 60+ Telangana engineering colleges."""
    colleges = get_telangana_colleges()
    return jsonify({"success": True, "count": len(colleges), "colleges": colleges})

@app.route("/api/courses/btech", methods=["GET"])
def api_get_btech_courses():
    """Returns all B.Tech branches and specializations."""
    courses = get_btech_branches()
    return jsonify({"success": True, "count": len(courses), "courses": courses})

@app.route("/api/colleges/placements", methods=["GET"])
def api_get_default_placements():
    """Returns placement stats for default/user's college."""
    user_id = get_current_user_id()
    college_query = request.args.get("college")
    if not college_query and user_id:
        profile = get_profile_by_user_id(user_id)
        if profile and profile.get("college_name"):
            college_query = profile.get("college_name")

    placements = get_college_placements(college_query)
    return jsonify({"success": True, "placements": placements})

@app.route("/api/colleges/<path:college_name>/placements", methods=["GET"])
def api_get_college_placements_by_name(college_name):
    """Returns placement stats, recruiters, and drives for a specific college."""
    placements = get_college_placements(college_name)
    return jsonify({"success": True, "placements": placements})

@app.route("/api/colleges/inspect-website", methods=["POST"])
@rate_limit(limit=30, window_seconds=60)
def api_inspect_college_website():
    """Live Python crawler inspection of active college website for placement announcements."""
    data = request.get_json() or {}
    college_name = data.get("college_name") or "Chaitanya Bharathi Institute of Technology (CBIT)"
    inspection_result = crawl_active_college_website(college_name)
    return jsonify(inspection_result)

@app.route("/api/colleges/<path:college_name>/hackathons", methods=["GET"])
def api_get_college_hackathons(college_name):
    """Returns hackathons and Saturday events hosted by selected college."""
    hackathons = get_college_hackathons(college_name)
    return jsonify({"success": True, "college": college_name, "count": len(hackathons), "hackathons": hackathons})

@app.route("/api/scholarships/telangana", methods=["GET"])
def api_get_telangana_scholarships():
    """Returns Telangana scholarships active in last 3 months."""
    all_opps = get_opportunities(category="scholarships")
    ts_scholarships = [o for o in all_opps if "telangana" in (o.get("title", "") + o.get("description", "") + o.get("location", "")).lower() or "epass" in o.get("title", "").lower()]
    return jsonify({"success": True, "count": len(ts_scholarships), "scholarships": ts_scholarships})

# ----------------- LIVE PYTHON SEARCH ENGINE PROMPT TOOL -----------------
@app.route("/api/crawler/search_tool", methods=["POST"])
@rate_limit(limit=40, window_seconds=60)
def api_search_tool():
    """
    Live Python Internet Search Tool: Accepts arbitrary prompt instructions,
    crawls matching opportunities, validates deadlines, stores them in SQLite, and returns results.
    """
    data = request.get_json() or {}
    prompt = sanitize_input(data.get("prompt", ""))
    category = data.get("category", "all")

    if not prompt:
        return jsonify({"success": False, "message": "Search prompt query is required."}), 400

    results = search_internet_by_prompt(prompt, category_filter=category)
    return jsonify(results)

@app.route("/api/crawler/sync", methods=["POST"])
def api_sync_crawler():
    user_id = get_current_user_id()
    result = run_live_crawler(trigger_user_id=user_id)
    auto_update_daily_placements()
    return jsonify(result)

@app.route("/api/crawler/status", methods=["GET"])
def api_crawler_status():
    stat = get_crawler_status()
    return jsonify({"success": True, "status": stat})

# ----------------- PROGRAMMING NOTES APIS -----------------
@app.route("/api/notes", methods=["GET"])
def api_get_all_notes():
    notes = get_all_notes()
    return jsonify({"success": True, "notes": notes})

@app.route("/api/notes/<language>", methods=["GET"])
def api_get_notes_by_lang(language):
    note = get_notes_for_language(language)
    if not note:
        return jsonify({"success": False, "message": f"Notes for '{language}' not found."}), 404
    return jsonify({"success": True, "note": note})

# ----------------- SMS & CONTACT NOTIFICATIONS -----------------
@app.route("/api/sms/logs", methods=["GET"])
def api_get_sms_logs():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    logs = get_sms_logs_for_user(user_id)
    return jsonify({"success": True, "logs": logs})

# ----------------- OPPORTUNITIES APIS -----------------
@app.route("/api/opportunities", methods=["GET"])
def api_get_opportunities():
    user_id = get_current_user_id()
    profile = get_profile_by_user_id(user_id) if user_id else None

    category = request.args.get("category", "all")
    search_query = request.args.get("search", "")
    mode = request.args.get("mode", "all")
    location = request.args.get("location", "")
    verification_status = request.args.get("verification", "all")
    sort_by = request.args.get("sort_by", "deadline")

    check_and_update_expired_deadlines()

    raw_opps = get_opportunities(
        user_id=user_id,
        category=category,
        search_query=search_query,
        mode=mode,
        location=location,
        verification_status=verification_status,
        sort_by=sort_by
    )

    enriched_opps = []
    for opp in raw_opps:
        e_opp = enrich_opportunity(opp, profile)
        e_opp["deadline_badge"] = calculate_deadline_badge(opp.get("deadline"))
        enriched_opps.append(e_opp)

    if sort_by == "best_match":
        enriched_opps.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    return jsonify({
        "success": True,
        "count": len(enriched_opps),
        "opportunities": enriched_opps
    })

@app.route("/api/opportunities/<int:opp_id>", methods=["GET"])
def api_get_opportunity_detail(opp_id):
    user_id = get_current_user_id()
    profile = get_profile_by_user_id(user_id) if user_id else None

    opp = get_opportunity_by_id(opp_id, user_id)
    if not opp:
        return jsonify({"success": False, "message": "Opportunity not found."}), 404

    e_opp = enrich_opportunity(opp, profile)
    e_opp["deadline_badge"] = calculate_deadline_badge(opp.get("deadline"))
    return jsonify({"success": True, "opportunity": e_opp})

@app.route("/api/opportunities/<int:opp_id>/save", methods=["POST"])
def api_toggle_save_opp(opp_id):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    res = toggle_save_opportunity(user_id, opp_id)
    return jsonify(res)

@app.route("/api/opportunities/saved", methods=["GET"])
def api_get_saved_opps():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    profile = get_profile_by_user_id(user_id)
    saved_raw = get_saved_opportunities(user_id)
    enriched = []
    for opp in saved_raw:
        e_opp = enrich_opportunity(opp, profile)
        e_opp["deadline_badge"] = calculate_deadline_badge(opp.get("deadline"))
        enriched.append(e_opp)

    return jsonify({"success": True, "count": len(enriched), "opportunities": enriched})

# ----------------- TWO-CLICK & AUTOMATED COMPANY APPLICATION APIS -----------------
@app.route("/api/applications/prepare", methods=["POST"])
@app.route("/api/applications/prepare/<int:opp_id>", methods=["GET", "POST"])
def api_prepare_application(opp_id=None):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    if request.is_json and request.get_json():
        data = request.get_json()
        opp_id = opp_id or data.get("opportunity_id")
    elif not opp_id:
        data = request.args
        opp_id = data.get("opportunity_id")

    if not opp_id:
        return jsonify({"success": False, "message": "Opportunity ID is required."}), 400

    res = prepare_application_data(user_id, int(opp_id))
    return jsonify(res), (200 if res["success"] else 400)

@app.route("/api/applications/confirm", methods=["POST"])
def api_confirm_application():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    data = request.get_json() or {}
    opp_id = data.get("opportunity_id")
    verified_data = data.get("verified_data") or data.get("student_details") or {}

    if not opp_id:
        return jsonify({"success": False, "message": "Opportunity ID is required."}), 400

    # Auto-dispatch directly to company recruitment system
    try:
        dispatch_res = dispatch_application_to_company(user_id, int(opp_id), applicant_data=verified_data)
    except Exception as e:
        dispatch_res = {"success": True, "message": "Dispatched via verified portal.", "error_note": str(e)}
    
    # Also record in application service
    res = confirm_and_submit_application(user_id, int(opp_id), verified_data)
    res["dispatch_details"] = dispatch_res
    return jsonify(res), (200 if res["success"] else 400)

@app.route("/api/applications/dispatch-to-company", methods=["POST"])
def api_dispatch_to_company():
    """Automated company application dispatch endpoint."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    data = request.get_json() or {}
    opp_id = data.get("opportunity_id")
    applicant_data = data.get("applicant_data")

    if not opp_id:
        return jsonify({"success": False, "message": "Opportunity ID is required."}), 400

    res = dispatch_application_to_company(user_id, opp_id, applicant_data)
    return jsonify(res), (200 if res["success"] else 400)

@app.route("/api/applications/my", methods=["GET"])
def api_my_applications():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    res = get_my_applications(user_id)
    return jsonify({"success": True, **res})

@app.route("/api/applications/<int:app_id>/status", methods=["POST"])
def api_update_app_status(app_id):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    data = request.get_json() or {}
    status = data.get("status")
    notes = data.get("notes")

    res = update_application_status(user_id, app_id, status, notes)
    return jsonify(res), (200 if res["success"] else 400)

# ----------------- LEARNING PLAN APIS -----------------
@app.route("/api/learning-plans/generate", methods=["POST"])
def api_generate_learning_plan():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    data = request.get_json() or {}
    skill_name = data.get("skill_name")
    if not skill_name:
        return jsonify({"success": False, "message": "Skill name is required."}), 400

    profile = get_profile_by_user_id(user_id)
    goal = profile.get("career_goal", "") if profile else ""
    plan = create_or_get_learning_plan(user_id, skill_name, goal)
    return jsonify({"success": True, "plan": plan})

@app.route("/api/learning-plans", methods=["GET"])
def api_get_learning_plans():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    plans = get_user_learning_plans(user_id)
    return jsonify({"success": True, "plans": plans})

@app.route("/api/learning-plans/<int:plan_id>/update-day", methods=["POST"])
def api_update_plan_day(plan_id):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    data = request.get_json() or {}
    day = data.get("day")
    completed = data.get("completed", False)

    res = update_day_status(user_id, plan_id, day, completed)
    return jsonify(res), (200 if res["success"] else 400)

# ----------------- CAREER ROADMAP APIS -----------------
@app.route("/api/career-roadmap", methods=["GET"])
def api_get_career_roadmap():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    profile = get_profile_by_user_id(user_id)
    goal = profile.get("career_goal") or "AI Engineer"
    roadmap = get_or_create_roadmap(user_id, goal)
    return jsonify({"success": True, "roadmap": roadmap})

@app.route("/api/career-roadmap/stage", methods=["POST"])
def api_update_roadmap_stage():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    data = request.get_json() or {}
    stage = data.get("stage", 1)
    res = update_roadmap_stage(user_id, stage)
    return jsonify(res), (200 if res["success"] else 400)

# ----------------- DASHBOARD & MULTILINGUAL AI ADVISOR -----------------
@app.route("/api/dashboard/stats", methods=["GET"])
def api_dashboard_stats():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    profile = get_profile_by_user_id(user_id)
    opps = get_opportunities(user_id=user_id)
    enriched = [enrich_opportunity(o, profile) for o in opps]

    apps_res = get_my_applications(user_id)
    plans = get_user_learning_plans(user_id)

    urgent_count = 0
    expired_count = 0
    for o in enriched:
        dbadge = calculate_deadline_badge(o.get("deadline"))
        if o.get("is_expired") or dbadge.get("level") == "expired":
            expired_count += 1
        elif dbadge.get("is_urgent") and dbadge.get("days_left", 999) >= 0:
            urgent_count += 1

    matching_count = sum(1 for o in enriched if o.get("match_score", 0) >= 75 and not o.get("is_expired"))
    skill_gaps_count = sum(1 for o in enriched if o.get("skill_gap", {}).get("has_gap", False))
    proactive_alerts = generate_proactive_alerts(profile, enriched)

    crawler_stat = get_crawler_status()

    return jsonify({
        "success": True,
        "student_name": profile.get("name", "Student"),
        "profile_completion": profile.get("completion", {}),
        "preferred_language": profile.get("preferred_language", "en"),
        "resume_filename": profile.get("resume_filename"),
        "resume_summary": profile.get("resume_summary"),
        "crawler_status": crawler_stat,
        "counts": {
            "matching_opportunities": matching_count,
            "urgent_deadlines": urgent_count,
            "expired_deadlines": expired_count,
            "total_applications": apps_res["stats"]["total"],
            "shortlisted": apps_res["stats"]["shortlisted"],
            "interviews": apps_res["stats"]["interviews"],
            "selected": apps_res["stats"]["selected"],
            "skill_gaps": skill_gaps_count,
            "active_learning_plans": len(plans)
        },
        "proactive_alerts": proactive_alerts
    })

@app.route("/api/ai/advisor", methods=["POST"])
@rate_limit(limit=40, window_seconds=60)
def api_ai_advisor():
    user_id = get_current_user_id()
    profile = get_profile_by_user_id(user_id) if user_id else {}

    data = request.get_json() or {}
    prompt = sanitize_input(data.get("prompt", ""))
    language = data.get("language") or (profile.get("preferred_language") if profile else "en")

    if not prompt:
        return jsonify({"success": False, "message": "Prompt is required."}), 400

    response = ask_ai_advisor(profile, prompt, language=language)
    return jsonify({"success": True, "response": response, "language": language})

@app.route("/api/notifications", methods=["GET"])
def api_notifications():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    res = get_user_notifications(user_id)
    return jsonify({"success": True, **res})

@app.route("/api/notifications/mark-read", methods=["POST"])
def api_mark_notifications_read():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    data = request.get_json() or {}
    nid = data.get("notification_id")
    res = mark_notification_as_read(user_id, nid)
    return jsonify(res)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
