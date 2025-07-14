from flask import Flask, send_file, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
import os
from models import db
from flask_jwt_extended import JWTManager

# -------------------------------------------------------------------
# 1. Load environment variables
# -------------------------------------------------------------------
load_dotenv()

# -------------------------------------------------------------------
# 2. Create Flask app – point static_folder to the React build folder
# -------------------------------------------------------------------
app = Flask(
    __name__,
    static_folder="../my-react-app",  # serves /index.html, /img, etc.
    static_url_path=""
)

# -------------------------------------------------------------------
# 3. App Configurations
# -------------------------------------------------------------------
app.secret_key = os.getenv("SECRET_KEY", "ggj")  # fallback if missing

# Database config
print("🔌  Using SQLAlchemy DB URL from DATABASE_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('DATABASE_URL')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# JWT config
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your-very-secret-key")
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False  # Set True in production with HTTPS
app.config["JWT_ACCESS_COOKIE_PATH"] = "/"
app.config["JWT_REFRESH_COOKIE_PATH"] = "/token/refresh"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False  # Enable for production

# -------------------------------------------------------------------
# 4. Initialise extensions
# -------------------------------------------------------------------
CORS(app)
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# -------------------------------------------------------------------
# 5. Register all routes from routes.py (single-file blueprint)
# -------------------------------------------------------------------
from routes import routes_bp
app.register_blueprint(routes_bp)

# -------------------------------------------------------------------
# 6. Fallback – serve index.html for any unknown path (optional)
#    This makes “/contact”, “/about”, etc. work with client-side routing.
# -------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("index.html"), 404

# -------------------------------------------------------------------
# 7. Start server
# -------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
