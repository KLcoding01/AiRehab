from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from models import db, Patient, Visit, Attachment, CalendarEvent, Therapist
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

# ------- OPEN AI -------
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None
MODEL = "gpt-4o-mini"

# ------- LOGIN MANAGER -------
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Therapist.query.get(int(user_id))

# ------- CREATE TABLES & ADMIN IF NONE -------
with app.app_context():
    db.create_all()
    # --- Admin user creation ---
    if not Therapist.query.filter_by(username="Kelvin").first():
        hashed_pw = generate_password_hash("Thanh123!")
        admin = Therapist(
            username="Kelvin",
            password=hashed_pw,
            first_name="Kelvin123!",
            last_name="Lam",
            credentials="PT",
            email="admin@example.com",
            phone="555-555-5555",
            availability="M-F",
            npi="0000000000",
            pt_license="LICENSE123",
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()
        
def parse_dob(dob_str):
    if not dob_str:
        return None
    for fmt in ("%m-%d-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(dob_str, fmt).date()
        except ValueError:
            continue
    return None

# ----- ROUTES -----

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
    
# --- Login, Forgot Password ----
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Therapist.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')
    
#---- Calendar ----

@app.route('/calendar')
@login_required
def calendar_view():
    return render_template('calendar.html')
    
#---- Visit Detail, Form, Add Visit ----

@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
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

@app.route('/patients')
@login_required
def patient_list():
    patients = Patient.query.all()
    return render_template('patient_list.html', patients=patients)
    
@app.route('/patients/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template('patient_detail.html', patient=patient)

@app.route('/patients/<int:patient_id>/visits/add', methods=['GET', 'POST'])
@login_required
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

@app.route('/visits/<int:visit_id>')
@login_required
def visit_detail(visit_id):
    visit = Visit.query.get_or_404(visit_id)
    return render_template('visit_detail.html', visit=visit)
    
# ------- Therapist Detail, Add, Remove -------

@app.route('/admin/add_therapist', methods=['GET', 'POST'])
@login_required
def add_therapist():
    if not current_user.is_admin:
        abort(403)  # Forbidden

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        credentials = request.form.get('credentials')
        email = request.form.get('email')
        phone = request.form.get('phone')
        pt_license = request.form.get('pt_license')
        npi = request.form.get('npi')
        availability = request.form.get('availability')

        if Therapist.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return render_template('add_therapist.html')

        hashed_pw = generate_password_hash(password)
        new_therapist = Therapist(
            username=username,
            password=hashed_pw,
            first_name=first_name,
            last_name=last_name,
            credentials=credentials,
            email=email,
            phone=phone,
            pt_license=pt_license,
            npi=npi,
            availability=availability,
            is_admin=bool(request.form.get('is_admin'))
        )
        db.session.add(new_therapist)
        db.session.commit()
        flash("New therapist created!", "success")
        return redirect(url_for('patient_list'))  # Or some admin page

    return render_template('add_therapist.html')
    
#---PT BUILDER ----
@app.route('/pt_builder')
@login_required
def pt_builder():
    return render_template('pt_builder.html')
    
 # --- Attachment/Upload ---
@app.route('/patients/<int:patient_id>/attachments/upload', methods=['POST'])
@login_required
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

@app.route('/attachments/<filename>')
@login_required
def get_attachment(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
