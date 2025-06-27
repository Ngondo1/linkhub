from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask import current_app as app
from flask import send_file  # for serving static files if needed
from flask_cors import CORS
from mpesa import stk_push
from flask_session import Session
from models import db, User, Employer, Employee, Job, Match
from datetime import datetime
import os

routes_bp = Blueprint("routes", __name__)
#user route
@routes_bp.route("/add-user", methods=["POST"])
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
@routes_bp.route("/match/<int:worker_id>", methods=["POST"])
def match_worker(worker_id):
    job_id = request.form.get("job_id")
    matched = Match(job_id=job_id, employee_id=worker_id, matched_at=datetime.utcnow())
    db.session.add(matched)
    db.session.commit()
    flash("Worker matched successfully!")
    return redirect(url_for("routes.search"))

# 3. ADD WORKER (GET & POST)
@routes_bp.route("/add-worker", methods=["POST"])
def add_worker():
    data = request.form if request.form else request.get_json()
    try:
        # Create User
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
            rate_unit=data.get("rate_unit", "per job"),
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
    # 4. ADD EMPLOYER
@routes_bp.route("/add-employer", methods=["POST"])
def add_employer():
    data = request.form if request.form else request.get_json()
    try:
        # Create User
        user = User(
            name=data.get("name"),
            phone_no=data.get("phone_no"),
            county=data.get("county"),
            town=data.get("town")
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
@routes_bp.route("/add-job", methods=["GET", "POST"])
def add_job():
    if request.method == "POST":
        job = Job(
            employer_id=request.form["employer_id"],
            job_title=request.form["title"],
            job_description=request.form["description"],
            job_location=request.form["location"],
            salary_range=request.form["salary"],
            employment_type=request.form["type"],
            status="listed"
        )
        db.session.add(job)
        db.session.commit()
        flash("Job posted successfully!")
        return redirect(url_for("routes.add_job"))

    return render_template("add_job.html")

# 6. VIEW JOBS
@routes_bp.route("/jobs")
def view_jobs():
    jobs = Job.query.order_by(Job.post_date.desc()).all()
    return render_template("jobs.html", jobs=jobs)

# 7. VIEW APPLICATIONS
@routes_bp.route("/applications")
def view_applications():
    # Assuming a simple model for now
    return render_template("applications.html")

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
