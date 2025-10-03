# Messages

Lightweight Flask app for employee messaging, leave requests, documents and basic admin/employee management.

Quick start (Windows PowerShell)

1. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. (Optional) Set environment variables

```powershell
#$env:SECRET_KEY = 'change-this-in-production'
#$env:DATABASE_URL = 'postgresql://user:password@host:port/database'
```

Notes
- The app will attempt to use the `DATABASE_URL` environment variable (suitable for Render/Heroku). If not set it falls back to the local PostgreSQL connection configured in `app.py`.
- The app automatically calls `db.create_all()` on startup and creates a default admin and a default employee if they do not exist.

Run the app

```powershell
python app.py
```

Then open http://localhost:5000 in your browser.

If you need help switching the database, creating the database user, or adjusting credentials, tell me which database server you're using and I can add precise commands.