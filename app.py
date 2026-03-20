import os
import yaml
from datetime import timedelta
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import check_password_hash

# ── Load YAML configs ─────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(__file__)

def load_yaml(filename):
    path = os.path.join(BASE_DIR, "config", filename)
    with open(path, "r") as f:
        return yaml.safe_load(f)

app_cfg   = load_yaml("app.yml")
users_cfg = load_yaml("users.yml")

# ── Flask app setup ───────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key      = app_cfg["app"]["secret_key"]
app.config["DEBUG"] = app_cfg["app"]["debug"]

session_mins = app_cfg["session"].get("lifetime_minutes", 60)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=session_mins)

@app.context_processor
def inject_globals():
    return {
        "branding": app_cfg["branding"],
        "current_user": current_user,
    }

# ── Flask-Login setup ─────────────────────────────────────────────────────────

login_manager = LoginManager(app)
login_manager.login_view             = "login"
login_manager.login_message          = "Please log in to access that page."
login_manager.login_message_category = "warning"

class User(UserMixin):
    def __init__(self, data):
        self.id              = data["username"]
        self.username        = data["username"]
        self.password_hash   = data["password_hash"]
        self.display_name    = data.get("display_name", data["username"])
        self.role            = data.get("role", "user")
        self.avatar_initials = data.get("avatar_initials", data["username"][:2].upper())

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"

USER_STORE = {u["username"]: User(u) for u in users_cfg["users"]}

@login_manager.user_loader
def load_user(user_id):
    return USER_STORE.get(user_id)

# ── Role-based decorator ──────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated

# ── Route protection from YAML ────────────────────────────────────────────────

protected_routes = app_cfg["routes"].get("protected", [])

@app.before_request
def enforce_protected_routes():
    if request.path in protected_routes and not current_user.is_authenticated:
        flash("You must be logged in to access that page.", "warning")
        return redirect(url_for("login", next=request.path))

# ── Public routes ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = USER_STORE.get(username)
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)
            return redirect(app_cfg["login"]["redirect_after_login"])
        else:
            error = "Invalid credentials. Check your username and password."

    return render_template("login.html", error=error)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

# ── Protected routes ──────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/settings")
@admin_required
def settings():
    return render_template(
        "settings.html",
        app_cfg=app_cfg,
        users=[{"username": u.username, "display_name": u.display_name,
                "role": u.role} for u in USER_STORE.values()]
    )

# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403,
                           message="Access Denied — Admin clearance required."), 403

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404,
                           message="Signal Lost — Page not found."), 404

# Entry point is wsgi.py — run with:
#   gunicorn wsgi:app
# or see gunicorn.conf.py for full config
