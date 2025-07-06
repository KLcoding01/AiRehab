from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from models import db, Patient, Visit, Attachment, CalendarEvent
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import os
from datetime import datetime
from openai import OpenAI
from flask_migrate import Migrate
from calendar_routes import calendar_bp



app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)
app.register_blueprint(calendar_bp)

#======= OPEN AI=======
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None
MODEL = "gpt-4o-mini"

# ====== LOGIN MANAGER ======
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Therapist.query.get(int(user_id))

# ====== CREATE TABLES & ADMIN IF NONE ======
with app.app_context():
    db.create_all()
    # Only run this once! Add a default admin user if none exists:
    if not Therapist.query.filter_by(username="admin").first():
        hashed_pw = generate_password_hash("admin123")
        admin = Therapist(
            username="admin",
            password=hashed_pw,
            first_name="Admin",
            last_name="User",
            credentials="PT",
            email="admin@example.com",
            phone="555-555-5555",
            availability="M-F",
            npi="0000000000",
            pt_license="LICENSE123",
        )
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created: username=admin, password=admin123")

def parse_dob(dob_str):
    """
    Parse DOB string in MM-DD-YYYY or MM/DD/YYYY format.
    Returns a date object or None if invalid.
    """
    if not dob_str:
        return None
    for fmt in ("%m-%d-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(dob_str, fmt).date()
        except ValueError:
            continue
    return None

# ====== ROUTES ======

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Therapist.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Forgot-password, reset-password, register, dashboard routes ---

# --- Create DB (local testing) ---
@app.before_request
def create_tables():
    db.create_all()

# --- Home / Patients List ---
@app.route('/')
def index():
    patients = Patient.query.all()
    return render_template('index.html', patients=patients)

# --- Calendar Detail ---
@app.route('/calendar')
def calendar_view():
    return render_template('calendar.html')
    
# --- Add Patient ---
@app.route('/patients/add', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        dob = request.form.get('date_of_birth')
        email = request.form.get('email')
        phone = request.form.get('phone')
        patient = Patient(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=datetime.strptime(dob, '%Y-%m-%d') if dob else None,
            email=email, phone=phone
        )
        db.session.add(patient)
        db.session.commit()
        flash('Patient added!')
        return redirect(url_for('index'))
    return render_template('patient_form.html')
    
# --- Patient List---
@app.route('/patients')
def patient_list():
    patients = Patient.query.all()
    return render_template('patient_list.html', patients=patients)
    
# --- Patient Detail ---
@app.route('/patients/<int:patient_id>')
def patient_detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template('patient_detail.html', patient=patient)

# --- Add Visit ---
@app.route('/patients/<int:patient_id>/visits/add', methods=['GET', 'POST'])
def add_visit(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == 'POST':
        date = request.form['date']
        notes = request.form.get('notes')
        visit = Visit(patient_id=patient.id, date=datetime.strptime(date, '%Y-%m-%d'), notes=notes)
        db.session.add(visit)
        db.session.commit()
        flash('Visit added!')
        return redirect(url_for('patient_detail', patient_id=patient.id))
    return render_template('visit_form.html', patient=patient)

# --- Visit Detail ---
@app.route('/visits/<int:visit_id>')
def visit_detail(visit_id):
    visit = Visit.query.get_or_404(visit_id)
    return render_template('visit_detail.html', visit=visit)

# --- PT Builder ---
@app.route('/pt_builder')
@login_required
def pt_builder():
    return render_template('pt_builder.html')
    
# --- File Upload (Attachment) ---
@app.route('/patients/<int:patient_id>/attachments/upload', methods=['POST'])
def upload_attachment(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    file = request.files['file']
    if file:
        filename = file.filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        attachment = Attachment(patient_id=patient.id, filename=filename)
        db.session.add(attachment)
        db.session.commit()
        flash('File uploaded!')
    return redirect(url_for('patient_detail', patient_id=patient.id))

# --- Download Attachment ---
@app.route('/attachments/<filename>')
def get_attachment(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Run ---
if __name__ == '__main__':
    app.run(debug=True)
