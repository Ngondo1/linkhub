from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

# ----------------------------------------------------------------------------
# SQLAlchemy instance (initialized in app.py)
# ----------------------------------------------------------------------------

db = SQLAlchemy()

# ----------------------------------------------------------------------------
# Enumerations (keep business vocab centralised)
# ----------------------------------------------------------------------------

class MessageType(enum.Enum):
    user = "user"
    system = "system"

class Availability(enum.Enum):
    immediate = "immediate"
    week = "1_week"
    month = "1_month"

class EmploymentType(enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    casual = "casual"

class ApplicationStatus(enum.Enum):
    pending = "pending"
    shortlisted = "shortlisted"
    rejected = "rejected"
    hired = "hired"

class JobStatus(enum.Enum):
    draft = "draft"
    listed = "listed"
    filled = "filled"
    closed = "closed"

class MatchStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    declined = "declined"

# ----------------------------------------------------------------------------
# Core domain models mapped from your ER diagram & functional requirements
# ----------------------------------------------------------------------------

class User(db.Model):
    """Base profile for every account (Employer or Employee)."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    registration_time = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    phone_no = db.Column(db.String(30), unique=True)
    gender = db.Column(db.String(20))
    county = db.Column(db.String(100))
    town = db.Column(db.String(100))
    level_of_education = db.Column(db.String(100))
    profession = db.Column(db.String(100))
    marital_status = db.Column(db.String(50))
    religion = db.Column(db.String(100))
    ethnicity = db.Column(db.String(100))
    description = db.Column(db.Text)

    employer = db.relationship("Employer", back_populates="user", uselist=False)
    employee = db.relationship("Employee", back_populates="user", uselist=False)

    sent_ratings = db.relationship("Rating", foreign_keys="Rating.rater_id", back_populates="rater")
    received_ratings = db.relationship("Rating", foreign_keys="Rating.rated_id", back_populates="rated")

    def __repr__(self):
        return f"<User {self.id} – {self.name}>"


class Employer(db.Model):
    __tablename__ = "employers"

    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    company_name = db.Column(db.String(150))
    business_type_id = db.Column(db.Integer)
    registration_number = db.Column(db.String(50))
    company_email = db.Column(db.String(120))
    company_phone = db.Column(db.String(30))
    company_location = db.Column(db.String(150))
    logo_url = db.Column(db.String(255))
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="employer")
    jobs = db.relationship("Job", back_populates="employer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Employer {self.company_name}>"


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)

    # Technician-specific fields
    role = db.Column(db.String(50), default="technician")
    specialty = db.Column(db.String(120))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    skills = db.Column(db.Text)
    years_of_experience = db.Column(db.Integer)
    expected_rate = db.Column(db.Integer)  # Amount per job
    rate_unit = db.Column(db.String(50), default="per job")  # e.g., "per job", "per hour"
    availability = db.Column(db.Enum(Availability))
    preferred_job_types = db.Column(db.String(150))
    portfolio_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="employee")
    applications = db.relationship("Application", back_populates="employee", cascade="all, delete-orphan")
    matches = db.relationship("Match", back_populates="employee", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Employee {self.id} – {self.user.name if self.user else ''}>"

class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employer_id = db.Column(db.Integer, db.ForeignKey("employers.id"))
    job_title = db.Column(db.String(150))
    job_description = db.Column(db.Text)
    job_location = db.Column(db.String(150))
    salary_range = db.Column(db.String(100))
    employment_type = db.Column(db.Enum(EmploymentType))
    post_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum(JobStatus), default=JobStatus.listed)

    employer = db.relationship("Employer", back_populates="jobs")
    applications = db.relationship("Application", back_populates="job", cascade="all, delete-orphan")
    matches = db.relationship("Match", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job {self.job_title} (ID {self.id})>"


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"))
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"))
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum(ApplicationStatus), default=ApplicationStatus.pending)

    job = db.relationship("Job", back_populates="applications")
    employee = db.relationship("Employee", back_populates="applications")

    def __repr__(self):
        return f"<Application {self.id} – Job {self.job_id} / Emp {self.employee_id}>"


class Rating(db.Model):
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    rater_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    rated_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    rater = db.relationship("User", foreign_keys=[rater_id], back_populates="sent_ratings")
    rated = db.relationship("User", foreign_keys=[rated_id], back_populates="received_ratings")

    def __repr__(self):
        return f"<Rating {self.id} – {self.rating}/5>"


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    short_code = db.Column(db.Integer)
    send_time = db.Column(db.DateTime, default=datetime.utcnow)
    phone_no = db.Column(db.String(30))
    message = db.Column(db.Text)
    message_type = db.Column(db.Enum(MessageType))

    user = db.relationship("User", backref="messages")

    def __repr__(self):
        return f"<Message {self.id} – {self.message_type}>"


class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"))
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"))
    status = db.Column(db.Enum(MatchStatus), default=MatchStatus.pending)
    matched_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship("Job", back_populates="matches")
    employee = db.relationship("Employee", back_populates="matches")

    def __repr__(self):
        return f"<Match {self.id} – Job {self.job_id} to Emp {self.employee_id}>"

# ----------------------------------------------------------------------------
# Utility function to seed roles / enums later if needed
# ----------------------------------------------------------------------------

def init_db(app, create=False):
    with app.app_context():
        if create:
            db.drop_all()
        db.create_all()
