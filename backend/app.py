from flask import Flask, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv
import os
from models import db

# -------------------------------------------------------------------
# 1. Load environment variables
# -------------------------------------------------------------------
load_dotenv(dotenv_path=".env")
print("Environment variables loaded successfully")

# -------------------------------------------------------------------
# 2. Create Flask app – point static_folder to the React build folder
# -------------------------------------------------------------------
app = Flask(
    __name__,                        # use the double-underscore version!
    static_folder="../my-react-app", # serves /index.html, /img, etc.
    static_url_path=""               # root URL → that folder
)
CORS(app)

# Session secret
app.secret_key = os.getenv("SECRET_KEY", "ggj")  # fallback if missing

# -------------------------------------------------------------------
# 3. Database config (MySQL via PyMySQL)
# -------------------------------------------------------------------
print("🔌  Using SQLAlchemy DB URL from DATABASE_URL")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('DATABASE_URL')



app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_TYPE"] = "filesystem"  # simple on-disk sessions

# -------------------------------------------------------------------
# 4. Initialise extensions
# -------------------------------------------------------------------

db.init_app(app)
migrate = Migrate(app, db)
Session(app)

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
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return send_file(os.path.join(root_dir, "index.html"))

# -------------------------------------------------------------------
# 7. Start server
# -------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
