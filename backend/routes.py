from flask import Blueprint, request, render_template, redirect, url_for, flash
from models import db, User, Employer, Employee, Job, Match
from datetime import datetime

routes_bp = Blueprint("routes", __name__)

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
@routes_bp.route("/add-worker", methods=["GET", "POST"])
def add_worker():
    if request.method == "POST":
        user = User(
            name=request.form["name"],
            phone_no=request.form["phone_no"],
            gender=request.form["gender"],
            county=request.form["county"],
            town=request.form["town"],
            level_of_education=request.form["education"],
            profession=request.form["profession"],
            marital_status=request.form["marital_status"],
            description=request.form["description"]
        )
        db.session.add(user)
        db.session.flush()  # get user.id before commit

        employee = Employee(
            id=user.id,
            skills=request.form["skills"],
            years_of_experience=request.form["experience"],
            expected_salary=request.form["salary"],
            availability=request.form["availability"]
        )
        db.session.add(employee)
        db.session.commit()
        flash("Worker added successfully!")
        return redirect(url_for("routes.add_worker"))

    return render_template("add_worker.html")

# 4. ADD EMPLOYER
@routes_bp.route("/add-employer", methods=["GET", "POST"])
def add_employer():
    if request.method == "POST":
        user = User(
            name=request.form["name"],
            phone_no=request.form["phone_no"],
            county=request.form["county"],
            town=request.form["town"]
        )
        db.session.add(user)
        db.session.flush()

        employer = Employer(
            id=user.id,
            company_name=request.form["company_name"],
            company_email=request.form["email"],
            company_phone=request.form["phone"],
            company_location=request.form["location"]
        )
        db.session.add(employer)
        db.session.commit()
        flash("Employer added successfully!")
        return redirect(url_for("routes.add_employer"))

    return render_template("add_employer.html")

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
