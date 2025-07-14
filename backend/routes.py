from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask import current_app as app
from flask import send_file  # for serving static files if needed
from flask_cors import CORS
from mpesa import stk_push
from flask_session import Session
from models import db, User, Employer, Employee, Job, Match, Content, SiteSetting, Application, Rating
from datetime import datetime
import os
from werkzeug.security import generate_password_hash

routes_bp = Blueprint("routes", __name__)

from flask import session, redirect, url_for, render_template, request, flash

from functools import wraps
from flask import session, redirect, url_for, flash
from flask_jwt_extended import create_access_token, set_access_cookies, jwt_required, get_jwt_identity


def login_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if user is None or user.role not in roles:
                flash("You do not have permission to access this page.", "error")
                return redirect(url_for("routes.login"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# routes.py

from flask import jsonify

@routes_bp.route("/rate-employee/<int:application_id>", methods=["GET", "POST"])
@login_required
@role_required("employer")
def rate_employee(application_id):
    application = Application.query.get_or_404(application_id)
    employee = application.employee
    user = User.query.get(employee.id) if employee else None

    # Find existing rating (if any)
    rating = Rating.query.filter_by(
        rater_id=get_jwt_identity(),
        rated_id=user.id
    ).order_by(Rating.timestamp.desc()).first()

    if request.method == "POST":
        rating_value = int(request.form.get("rating"))
        comment = request.form.get("comment", "")
        # If already rated, update; else create new
        if rating:
            rating.rating = rating_value
            rating.comment = comment
            rating.timestamp = datetime.utcnow()
        else:
            rating = Rating(
                rater_id=get_jwt_identity(),
                rated_id=user.id,
                rating=rating_value,
                comment=comment,
                timestamp=datetime.utcnow()
            )
            db.session.add(rating)
        db.session.commit()
        flash("Employee rated successfully!", "success")
        return redirect(url_for("routes.view_applications", job_id=application.job_id))

    return render_template(
        "rate_employee.html",
        application=application,
        employee=employee,
        user=user,
        rating=rating
    )

@routes_bp.route("/apply-job/<int:job_id>", methods=["GET", "POST"])
@login_required
@role_required("worker")
def apply_job(job_id):
    user_id = get_jwt_identity()
    job = Job.query.get_or_404(job_id)
    employer = Employer.query.get(job.employer_id)
    success = None
    error = None

    if request.method == "POST":
        existing = Application.query.filter_by(job_id=job_id, employee_id=user_id).first()
        if existing:
            error = "You have already applied for this job."
        else:
            application = Application(job_id=job_id, employee_id=user_id, application_date=datetime.utcnow())
            db.session.add(application)
            db.session.commit()
            success = "Your application has been submitted successfully!"
    return render_template("apply_job.html", job=job, employer=employer, success=success, error=error)

@routes_bp.route("/matches")
@login_required
@role_required("employer")
def matches():
    # Example: adjust as needed for your models
    users = User.query.all()
    jobs = Job.query.all()
    employees = Employee.query.all()

    # Convert to dicts for JSON
    users_data = [
        {"id": u.id, "name": u.name}
        for u in users
    ]
    jobs_data = [
        {"id": j.id, "title": j.job_title, "description": j.job_description, "skills": (j.job_description or "").split(",")}
        for j in jobs
    ]
    employees_data = [
       {"id": e.id, "name": e.user.name if e.user else "", "skills": (e.skills or "").split(",")}
        for e in employees
    ]
    return render_template(
        "matches.html",
        users=users_data,
        jobs=jobs_data,
        employees=employees_data
    )

@routes_bp.route("/", methods=["GET"])
def home():
    return render_template("index.html")

from flask_jwt_extended import create_access_token, set_access_cookies

@routes_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]
        user = None
        db_error = False
        try:
            user = User.query.filter(
                (User.username == username) | (User.phone_no == username)
            ).first()
        except Exception as db_err:
            db_error = True

        if db_error:
            flash("Database connection error. Please try again later.", "error")
        elif not user:
            flash("No user found with that username or phone.", "error")
        elif user.role != role:
            flash("Role does not match for this user.", "error")
        elif not user.check_password(password):
            flash("Incorrect password.", "error")
        else:
            access_token = create_access_token(identity=str(user.id))
            if role == "admin":
                resp = redirect(url_for("routes.admin_dashboard"))
            elif role == "employer":
                resp = redirect(url_for("routes.employer_dashboard"))
            elif role == "worker":
                resp = redirect(url_for("routes.worker_dashboard"))
            else:
                flash("Unknown role.", "error")
                return render_template("login.html")
            set_access_cookies(resp, access_token)
            flash("Logged in successfully!", "success")
            return resp
    return render_template("login.html")



@routes_bp.route("/admin-dashboard")
@login_required
@role_required("admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")

@routes_bp.route("/employer/job/<int:job_id>")
@login_required
@role_required("employer")
def employer_view_job(job_id):
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    employer = Employer.query.get(user_id)
    if not employer:
        flash("Employer not found.", "error")
        return redirect(url_for("routes.home"))
    job = Job.query.filter_by(id=job_id, employer_id=employer.id).first()
    if not job:
        flash("Job not found or you do not have permission to view it.", "error")
        return redirect(url_for("routes.employer_dashboard"))
    return render_template("employer_job_detail.html", job=job, employer=employer)

@routes_bp.route("/employer-dashboard", methods=["GET"])
@login_required
@role_required("employer")
def employer_dashboard():
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    employer = Employer.query.get(user_id)
    if not employer:
        flash("Employer not found.", "error")
        return redirect(url_for("routes.home"))
    jobs = Job.query.filter_by(employer_id=employer.id).order_by(Job.post_date.desc()).all()
    return render_template("employers.html", employer=employer, jobs=jobs)



@routes_bp.route("/worker-dashboard")
@login_required
@role_required("worker")
def worker_dashboard():
    user_id = get_jwt_identity()
    worker = User.query.get(user_id)
    # Get jobs matching worker's profession, include employer info
    jobs = (
        db.session.query(Job, Employer)
        .join(Employer, Job.employer_id == Employer.id)
        .filter(
            Job.job_title.ilike(f"%{worker.profession}%"),
            Job.status == "listed"
        )
        .order_by(Job.post_date.desc())
        .all()
    )
    total_jobs = Job.query.count()
    return render_template("workers.html", worker=worker, jobs=jobs, total_jobs=total_jobs)


#user route
@routes_bp.route("/add-user", methods=["POST"])
@login_required
@role_required("admin")
def add_user():
    data = request.form if request.form else request.get_json()
    try:
        user = User(
            name=data.get("name"),
            age=data.get("age"),
            phone_no=data.get("phone_no"),
            gender=data.get("gender"),
            county=data.get("county"),
            town=data.get("town"),
            level_of_education=data.get("level_of_education"),
            profession=data.get("profession"),
            marital_status=data.get("marital_status"),
            religion=data.get("religion"),
            ethnicity=data.get("ethnicity"),
            description=data.get("description")
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({"status": "success", "user_id": user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

# 1. SEARCH WORKERS BASED ON FILTERS
@routes_bp.route("/search")
def search():
    category = request.args.get("category")
    location = request.args.get("location")

    query = Job.query.filter_by(status="listed")
    if category:
        query = query.filter_by(job_title=category)
    if location:
        query = query.filter_by(job_location=location)

    results = query.all()
    return render_template("results.html", jobs=results)


# 2. MATCH WORKER TO JOB (from results page)
@routes_bp.route("/match/<int:employee_id>", methods=["POST"])
def match_worker(employee_id):
    job_id = request.form.get("job_id")
    matched = Match(job_id=job_id, employee_id=employee_id, matched_at=datetime.utcnow())
    db.session.add(matched)
    db.session.commit()
    flash("Worker matched successfully!")
    return redirect(url_for("routes.search"))

# 3. ADD WORKER (GET & POST)
@routes_bp.route("/add-worker", methods=["POST"])
@login_required
@role_required("admin")
def add_worker():
    data = request.form
    try:
        # Create User
        user = User(
            username=data.get("username"),
            name=data.get("name"),
            age=data.get("age"),
            phone_no=data.get("phone_no"),
            gender=data.get("gender"),
            county=data.get("county"),
            town=data.get("town"),
            level_of_education=data.get("level_of_education"),
            profession=data.get("profession"),
            marital_status=data.get("marital_status"),
            religion=data.get("religion"),
            ethnicity=data.get("ethnicity"),
            description=data.get("description"),
            password_hash=generate_password_hash(data.get("password"))
        )
        db.session.add(user)
        db.session.flush()  # get user.id

        # Create Employee
        employee = Employee(
            id=user.id,
            role=data.get("role", "technician"),
            specialty=data.get("specialty"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            skills=data.get("skills"),
            years_of_experience=data.get("years_of_experience"),
            expected_rate=data.get("expected_rate"),
            rate_unit=data.get("rate_unit"),
            availability=data.get("availability"),
            preferred_job_types=data.get("preferred_job_types"),
            portfolio_url=data.get("portfolio_url")
        )
        db.session.add(employee)
        db.session.commit()
        flash("Worker added successfully!", "success")
        return redirect(url_for("routes.add_worker_page"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("routes.add_worker_page"))
    
@routes_bp.route("/site-settings", methods=["GET", "POST"])
@login_required
@role_required("admin")
def site_settings():
    settings = SiteSetting.query.first()
    if not settings:
        settings = SiteSetting(site_name="LinkHub")
        db.session.add(settings)
        db.session.commit()
    if request.method == "POST":
        settings.site_name = request.form.get("site_name")
        settings.contact_email = request.form.get("contact_email")
        settings.maintenance_mode = bool(request.form.get("maintenance_mode"))
        db.session.commit()
        flash("Settings updated successfully!", "success")
        return redirect(url_for("routes.site_settings"))
    return render_template("site_settings.html", settings=settings)

@routes_bp.route("/view-logs")
@login_required
@role_required("admin")
def view_logs():
    # logs = Log.query.order_by(Log.timestamp.desc()).all()  # Uncomment if you have a Log model
    return render_template("view_logs.html")  # Pass logs=logs if you have logs


@routes_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        if not new_password or new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("change_password.html")
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash("Password changed successfully!", "success")
        return redirect(url_for("routes.admin_dashboard"))
    return render_template("change_password.html")

from flask_jwt_extended import unset_jwt_cookies

@routes_bp.route("/logout")
def logout():
    resp = redirect(url_for("routes.login"))
    unset_jwt_cookies(resp)
    flash("You have been logged out.", "success")
    return resp

@routes_bp.route("/edit-job/<int:job_id>", methods=["GET", "POST"])
@login_required
@role_required("employer")
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == "POST":
        job.job_title = request.form["job_title"]
        job.job_description = request.form["job_description"]
        job.job_location = request.form["job_location"]
        job.salary_range = request.form.get("salary_range")
        job.employment_type = request.form.get("employment_type")
        db.session.commit()
        flash("Job updated successfully!", "success")
        return redirect(url_for("routes.employer_dashboard"))
    return render_template("edit_job.html", job=job)

@routes_bp.route("/edit-user/<int:user_id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        data = request.form
        user.username = data.get("username")
        user.name = data.get("name")
        user.phone_no = data.get("phone_no")
        user.role = data.get("role")
        user.county = data.get("county")
        user.town = data.get("town")
        if data.get("password"):
            user.password_hash = generate_password_hash(data.get("password"))
        db.session.commit()
        flash("User updated successfully!", "success")
        return redirect(url_for("routes.manage_users"))
    return render_template("edit_user.html", user=user)

@routes_bp.route("/delete-user/<int:user_id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", "success")
    return redirect(url_for("routes.manage_users"))

@routes_bp.route("/manage-content")
@login_required
@role_required("admin")
def manage_content():
    # Replace Content with your actual content model
    contents = Content.query.all()
    return render_template("manage_content.html", contents=contents)
    
@routes_bp.route("/manage-users")
@login_required
@role_required("admin")
def manage_users():
    users = User.query.all()
    return render_template("manage_users.html", users=users, active="users")

@routes_bp.route("/retrieve-workers")
@login_required
@role_required("admin")
def retrieve_workers():
    workers = Employee.query.all()
    return render_template("manage_users.html", workers=workers, active="workers")

@routes_bp.route("/retrieve-employers")
@login_required
@role_required("admin")
def retrieve_employers():
    employers = Employer.query.all()
    return render_template("manage_users.html", employers=employers, active="employers")

@routes_bp.route("/retrieve-jobs")
@login_required
@role_required("admin")
def retrieve_jobs():
    jobs = Job.query.all()
    return render_template("manage_users.html", jobs=jobs, active="jobs")

@routes_bp.route("/retrieve-matches")
@login_required
@role_required("admin")
def retrieve_matches():
    matches = Match.query.all()
    return render_template("manage_users.html", matches=matches, active="matches")

    # 4. ADD EMPLOYER
@routes_bp.route("/add-employer", methods=["POST"])
@login_required
@role_required("admin")
def add_employer():
    data = request.form
    try:
        # Create User
        user = User(
            username=data.get("username"),
            name=data.get("name"),
            phone_no=data.get("phone_no"),
            county=data.get("county"),
            town=data.get("town"),
            password_hash=generate_password_hash(data.get("password"))
        )
        db.session.add(user)
        db.session.flush()  # get user.id

        # Create Employer
        employer = Employer(
            id=user.id,
            company_name=data.get("company_name"),
            business_type_id=data.get("business_type_id"),
            registration_number=data.get("registration_number"),
            company_email=data.get("company_email"),
            company_phone=data.get("company_phone"),
            company_location=data.get("company_location"),
            logo_url=data.get("logo_url"),
            verified=data.get("verified", False)
        )
        db.session.add(employer)
        db.session.commit()
        return jsonify({"status": "success", "user_id": user.id, "employer_id": employer.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
# 5. ADD JOB LISTING
@routes_bp.route("/post-job", methods=["GET"])
@login_required
@role_required("employer")
def post_job():
    return render_template("post_job.html")
# routes.py

@routes_bp.route("/add-job", methods=["GET", "POST"])
@login_required
@role_required("employer")
def add_job():
    from flask_jwt_extended import get_jwt_identity
    if request.method == "POST":
        user_id = get_jwt_identity()
        employer = Employer.query.get(user_id)
        if not employer:
            flash("You must be registered as an employer to post jobs.", "error")
            return redirect(url_for("routes.index"))

        job = Job(
            job_title=request.form["job_title"],
            job_description=request.form["job_description"],
            job_location=request.form["job_location"],
            salary_range=request.form.get("salary_range"),
            employment_type=request.form.get("employment_type"),
            employer_id=employer.id
        )
        db.session.add(job)
        db.session.commit()
        flash("Job posted successfully!", "success")
        return redirect(url_for("routes.employer_dashboard"))
    return render_template("post_job.html")
# 6. VIEW JOBS
@routes_bp.route("/jobs")
@login_required
@role_required("employer")
def view_jobs():
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    employer = Employer.query.get(user_id)
    if not employer:
        flash("Employer not found.", "error")
        return redirect(url_for("routes.home"))
    jobs = Job.query.filter_by(employer_id=employer.id).order_by(Job.post_date.desc()).all()
    return render_template("jobs.html", jobs=jobs)

# 7. VIEW APPLICATIONS
@routes_bp.route("/applications/<int:job_id>")
@login_required
@role_required("employer")
def view_applications(job_id):
    job = Job.query.get_or_404(job_id)
    applications = Application.query.filter_by(job_id=job_id).all()
    # Get employee info for each application
    app_data = []
    for app in applications:
        employee = Employee.query.get(app.employee_id)
        user = User.query.get(employee.id) if employee else None
        rating = Rating.query.filter_by(employee_id=app.employee_id, job_id=job_id).first()
        app_data.append({
            "application": app,
            "employee": employee,
            "user": user
            "rating": rating
        })
    return render_template("applications.html", job=job, applications=app_data)

# 8. DASHBOARD
@routes_bp.route("/dashboard")
def dashboard():
    users = User.query.count()
    jobs = Job.query.count()
    matches = Match.query.count()
    return render_template("dashboard.html", user_count=users, job_count=jobs, match_count=matches)

# GET: Fetch all technicians with known coordinates
@routes_bp.route("/api/technicians", methods=["GET"])
def get_technicians():
    technicians = Employee.query.filter_by(role='technician').all()
    tech_list = [
        {
            "id": tech.id,
            "name": tech.full_name,
            "lat": tech.latitude,
            "lng": tech.longitude,
            "specialty": tech.specialty
        }
        for tech in technicians if tech.latitude and tech.longitude
    ]
    return jsonify(tech_list)

# POST: Update technician location by ID
@routes_bp.route("/api/technicians/location", methods=["POST"])
def update_technician_location():
    data = request.get_json()
    tech_id = data.get("id")
    lat = data.get("lat")
    lng = data.get("lng")

    technician = Employee.query.get(tech_id)
    if not technician or technician.role != 'technician':
        return jsonify({"error": "Technician not found"}), 404

    technician.latitude = lat
    technician.longitude = lng
    db.session.commit()

    return jsonify({"message": "Location updated"}), 200

# GET: Retrieve technician markers for map display
@routes_bp.route("/api/map/technicians", methods=["GET"])
def get_map_technicians():
    technicians = Employee.query.filter(Employee.latitude.isnot(None), Employee.longitude.isnot(None)).all()
    markers = [
        {
            "name": tech.full_name,
            "specialty": tech.specialty,
            "lat": tech.latitude,
            "lng": tech.longitude
        }
        for tech in technicians
    ]
    return jsonify(markers)

# POST: Submit current geolocation for technician (optional extension)
@routes_bp.route("/api/map/location", methods=["POST"])
def post_map_location():
    data = request.get_json()
    lat = data.get("lat")
    lng = data.get("lng")
    user = data.get("user")  # optional: associate location with a user

    if not lat or not lng:
        return jsonify({"error": "Missing coordinates"}), 400

    # You could store the location temporarily or update a user profile here
    return jsonify({"message": "Location received", "lat": lat, "lng": lng, "user": user}), 200


#MPESA DARAJA
@routes_bp.route("/mpesa/callback", methods=["POST"])
def mpesa_callback():
    data = request.get_json()
    # Process the callback data as needed
    # For example, save transaction details to the database
    print("MPESA Callback Data:", data)
    return jsonify({"status": "success"}), 200

@routes_bp.route("/subscribe", methods=["GET", "POST"])
def subscribe():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        plan = request.form["plan"]

        amount = 10 if plan == "basic" else 50

        try:
            if phone.startswith("07"):
                phone = "254" + phone[1:]
                print("About to call stk_push with:", phone, amount)
            response = stk_push(phone=phone, amount=amount)
            flash("STK push sent. Complete the payment on your phone.")
        except Exception as e:
            flash(f"Payment failed: {str(e)}")

        return redirect(url_for("routes.subscribe"))

    return render_template("subscription.html")

@routes_bp.route("/healthz")
def health_check():
    return "OK", 200


# ...existing code...

# Serve the add_worker.html page
@routes_bp.route("/add_worker", methods=["GET"])
def add_worker_page():
    return render_template("add_worker.html")

# Serve the results.html page
@routes_bp.route("/results", methods=["GET"])
def results_page():
    return render_template("results.html")

# Serve the hire_smarter.html page (if you want it via Flask, not static)
@routes_bp.route("/hire_smarter", methods=["GET"])
def hire_smarter_page():
    return render_template("hire_smarter.html")
