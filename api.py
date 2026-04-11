import os
import sys
import threading
import subprocess
import logging
import sqlite3
# Lazy import pandas inside functions to save RAM on startup
# import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_talisman import Talisman

# App Configuration
print(">>> INITIALIZING LEADSFLOW PRO 3.0 API...", flush=True)
app = Flask(__name__)
CORS(app)
# Health check must be allowed via HTTP for Render
Talisman(app, content_security_policy=None, force_https=False)

app.config['SECRET_KEY'] = 'leadsflow-3.0-ultra-rebuild'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Paths
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = "/data" if os.path.exists("/data") else ROOT
DB_NAME = "leads_production_v3.db"
DB_PATH = f'sqlite:///{os.path.join(DATA_ROOT, DB_NAME)}'
app.config['SQLALCHEMY_DATABASE_URI'] = DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    niche = db.Column(db.String(100))
    location = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    leads = db.relationship('Lead', backref='batch', lazy=True)

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=False)
    name = db.Column(db.String(200))
    website = db.Column(db.String(500))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(200))
    social = db.Column(db.String(500))
    source = db.Column(db.String(100))
    score = db.Column(db.Float)

@login_manager.user_loader
def load_user(uid): return User.query.get(int(uid))

# Global Status
hunt_status = {"is_running": False, "progress": "Ready", "percent": 0, "last_result": None}

def run_hunt(ctx, user_id, niche, location, count):
    with ctx:
        try:
            hunt_status.update({"is_running": True, "progress": "Launching Engine v33.0 (Eternal Titan)...", "percent": 5, "last_result": None})
            print(f">>> STARTING HUNT: {niche} in {location}", flush=True)
            
            batch = Batch(user_id=user_id, niche=niche, location=location)
            db.session.add(batch)
            db.session.commit()

            engine_path = os.path.join(ROOT, "engine.py")
            csv_path = os.path.join(ROOT, "leads.csv")
            if os.path.exists(csv_path): os.remove(csv_path)

            proc = subprocess.Popen(
                [sys.executable, engine_path, niche, location, str(count)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True
            )

            full_log = []
            while True:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None: break
                if line:
                    line = line.strip()
                    full_log.append(line)
                    print(f"ENGINE: {line}", flush=True)
                    if line.startswith("PROGRESS:"):
                        parts = line.split(":")
                        if len(parts) >= 4:
                            curr, total, msg = int(parts[1]), int(parts[2]), parts[3]
                            pct = int((curr / total) * 90) + 5
                            hunt_status.update({"progress": msg, "percent": pct})

            proc.wait(timeout=900)
            exit_code = proc.returncode
            hunt_status.update({"progress": f"Analysis finished (exit={exit_code})", "percent": 100})

            if os.path.exists(csv_path):
                import csv
                with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        db.session.add(Lead(
                            batch_id=batch.id, 
                            name=row.get('Company Name', 'Unknown'), 
                            website=row.get('Website', 'None'),
                            phone=row.get('WhatsApp', 'None'), 
                            email=row.get('Email ID', 'None'), 
                            social=row.get('Social', 'None'),
                            source=row.get('Source', 'v33.0'),
                            score=float(row.get('Score', 5.0))
                        ))
                    db.session.commit()
                hunt_status["last_result"] = f"Success: Eternal Titan successfully synchronized registry prospects."
            else:
                log_tail = " | ".join(full_log[-5:]) if full_log else "No output"
                hunt_status["last_result"] = f"Failure: 0 leads. Log: {log_tail}"

        except Exception as e:
            print(f">>> HUNT SYSTEM ERROR: {e}", flush=True)
            hunt_status["last_result"] = f"Critical Error: {str(e)}"
        finally:
            hunt_status["is_running"] = False

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET': return send_from_directory(ROOT, 'login.html')
    data = request.json or {}
    user = User.query.filter_by(username=data.get('username')).first()
    if user and check_password_hash(user.password_hash, data.get('password')):
        login_user(user, remember=True)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 401

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET': return send_from_directory(ROOT, 'register.html')
    data = request.json or {}
    if User.query.filter_by(username=data.get('username')).first(): return jsonify({"status": "error"}), 400
    user = User(username=data.get('username'), password_hash=generate_password_hash(data.get('password')))
    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)
    return jsonify({"status": "success"})

# Health Check for Render
@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "db": "connected"}), 200

# Better DB Initialization
def init_db():
    with app.app_context():
        try:
            db.create_all()
            print(">>> Database initialized successfully.", flush=True)
        except Exception as e:
            print(f">>> DB Init Error: {e}", flush=True)

@app.route('/api/batches', methods=['GET'])
@login_required
def get_batches():
    batches = Batch.query.filter_by(user_id=current_user.id).order_by(Batch.timestamp.desc()).all()
    return jsonify([{
        "id": b.id, "niche": b.niche, "location": b.location, "timestamp": b.timestamp.strftime("%Y-%m-%d"),
        "lead_count": len(b.leads)
    } for b in batches])

@app.route('/hunt', methods=['POST'])
@login_required
def hunt():
    if hunt_status["is_running"]: return jsonify({"status": "error"}), 400
    d = request.json
    threading.Thread(target=run_hunt, args=(app.app_context(), current_user.id, d.get('niche'), d.get('location'), d.get('count', 10))).start()
    return jsonify({"status": "accepted"}), 202

@app.route('/status')
@login_required
def status(): return jsonify(hunt_status)

@app.route('/data')
@login_required
def get_data():
    batches = Batch.query.filter_by(user_id=current_user.id).order_by(Batch.timestamp.desc()).all()
    return jsonify([{
        "id": b.id, "niche": b.niche, "location": b.location, "timestamp": b.timestamp.strftime("%Y-%m-%d"),
        "leads": [{"Name": l.name, "Website": l.website, "Phone": l.phone, "Email": l.email, "Social": l.social, "Score": l.score} for l in b.leads]
    } for b in batches])

@app.route('/export/csv')
@login_required
def export_csv():
    import io
    from flask import make_response
    batches = Batch.query.filter_by(user_id=current_user.id).all()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["Niche", "Location", "Company", "Website", "Email", "Phone", "Score"])
    writer.writeheader()
    for b in batches:
        for l in b.leads:
            writer.writerow({
                "Niche": b.niche, "Location": b.location, "Company": l.name,
                "Website": l.website, "Email": l.email, "Phone": l.phone, "Score": l.score
            })
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=leads_export.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/')
@login_required
def index(): return send_from_directory(ROOT, 'index.html')

@app.route('/logout')
def logout(): logout_user(); return jsonify({"status": "success"})

# Ensure DB is ready
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
