# GlowingSpork.io — Flask Web App

A cosmic, space-themed Flask website with Flask-Login authentication and YAML-driven configuration.

## Project Structure

```
glowingspork/
├── app.py                      # Main Flask app + Flask-Login setup
├── requirements.txt
├── config/
│   ├── app.yml                 # App settings, branding, routes
│   └── users.yml               # User credentials (hashed passwords)
├── static/
│   └── spork-hero.jpg          # Background image
└── templates/
    ├── base.html               # Shared layout (nav, starfield, flash messages)
    ├── index.html              # Home page
    ├── about.html              # About page
    ├── contact.html            # Contact page
    ├── login.html              # Login form
    ├── dashboard.html          # Protected dashboard (login required)
    ├── settings.html           # Admin-only config viewer
    └── error.html              # 403 / 404 error page
```

## Setup & Run

```bash
pip install -r requirements.txt

# Development (auto-reload on code changes, set debug: true in app.yml)
gunicorn -c gunicorn.conf.py wsgi:app

# Production (explicit workers, no reload)
gunicorn wsgi:app --workers 4 --bind 0.0.0.0:5000

# The host/port/debug/workers are all read from gunicorn.conf.py → config/app.yml
```

## Default Credentials

| Username | Password   | Role  |
|----------|------------|-------|
| admin    | spork123   | admin |
| captain  | cosmos99   | user  |

## Configuration

### config/app.yml
- `app` — secret key, debug mode, host/port
- `branding` — site title, tagline, logo text (injected into all templates)
- `session` — session lifetime in minutes
- `login` — redirect path after login, max attempts
- `routes.public` — paths that don't require login
- `routes.protected` — paths that enforce login (checked in `before_request`)

### config/users.yml
Add users with hashed passwords:
```bash
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('yourpassword'))"
```

Then add to users.yml:
```yaml
- username: "newuser"
  password_hash: "scrypt:..."
  display_name: "New User"
  role: "user"          # admin | user
  avatar_initials: "NU"
```

## Route Protection

- **`/login_required` decorator** — on `/dashboard` and `/settings`
- **`admin_required` decorator** — on `/settings` (role check on top of login)
- **`before_request` hook** — enforces `routes.protected` list from `app.yml`

## Changing the Secret Key

Edit `config/app.yml`:
```yaml
app:
  secret_key: "your-long-random-secret-here"
```
Generate one with: `python3 -c "import secrets; print(secrets.token_hex(32))"`
