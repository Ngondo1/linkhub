from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin_username = "admin"
    admin_phone = "0768620877"
    admin_password = "Myself@04"
    admin_name = "System Admin"
    admin_county = "Nairobi"
    admin_town = "Nairobi"
    admin_age = 30
    admin_gender = "Male"
    admin_level_of_education = "Degree"
    admin_profession = "Administrator"
    admin_marital_status = "Single"
    admin_religion = "None"
    admin_ethnicity = "Kenyan"
    admin_description = "Superuser for system management."

    admin = User.query.filter_by(role="admin").first()
    if not admin:
        admin = User(
            username=admin_username,
            phone_no=admin_phone,
            name=admin_name,
            role="admin",
            password_hash=generate_password_hash(admin_password),
            county=admin_county,
            town=admin_town,
            age=admin_age,
            gender=admin_gender,
            level_of_education=admin_level_of_education,
            profession=admin_profession,
            marital_status=admin_marital_status,
            religion=admin_religion,
            ethnicity=admin_ethnicity,
            description=admin_description
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created!")
    else:
        print("Admin user already exists.")