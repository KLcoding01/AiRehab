from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, abort
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
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
elif os.environ.get('RENDER'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/data/airehab.db'
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
    
# ----- ROUTES -----
   
@app.route('/')
def index():
    return redirect(url_for('dashboard'))
    # or: return render_template('index.html')
    
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
    
#---- Calendar ----

@app.route('/calendar')
@login_required
def calendar_view():
    return render_template('calendar.html')
    
@app.route('/api/events', methods=['GET'])
def get_events():
    therapist_id = request.args.get('therapist_id')
    query = CalendarEvent.query
    if therapist_id:
        query = query.filter_by(therapist_id=therapist_id)
    events = query.all()
    return jsonify([
        {
            'id': e.id,
            'title': e.title,
            'start': e.start.isoformat(),
            'end': e.end.isoformat(),
            'extendedProps': {
                'therapist_id': e.therapist_id,
                'patient_id': e.patient_id
            }
        } for e in events
    ])

@app.route('/api/events', methods=['POST'])
def create_event():
    data = request.json
    event = CalendarEvent(
        title=data['title'],
        start=datetime.fromisoformat(data['start']),
        end=datetime.fromisoformat(data['end']),
        therapist_id=data['therapist_id'],
        patient_id=data['patient_id']
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({'id': event.id}), 201

@app.route('/api/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.json
    event = CalendarEvent.query.get_or_404(event_id)
    event.title = data['title']
    event.start = datetime.fromisoformat(data['start'])
    event.end = datetime.fromisoformat(data['end'])
    event.therapist_id = data['therapist_id']
    event.patient_id = data['patient_id']
    db.session.commit()
    return jsonify({'message': 'Event updated'})

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    event = CalendarEvent.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({'message': 'Event deleted'})
    
#---- Visit Detail, Form, Add Visit ----

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        p = Patient(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            dob=request.form.get('dob'),
            phone=request.form.get('phone', ''),
            email=request.form.get('email', '')
        )
        db.session.add(p)
        db.session.commit()
        flash('Patient added!')
        return redirect(url_for('patient_list'))
    return render_template('patient_form.html', patient=None)

@app.route('/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    p = Patient.query.get_or_404(patient_id)
    if request.method == 'POST':
        p.first_name = request.form['first_name']
        p.last_name = request.form['last_name']
        p.dob = request.form.get('dob')
        p.phone = request.form.get('phone', '')
        p.email = request.form.get('email', '')
        db.session.commit()
        flash('Patient updated!')
        return redirect(url_for('patient_list'))
    return render_template('patient_form.html', patient=p)


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

# ------------------ API ------------------

@app.route('/api/patient_list', methods=['GET'])
def get_patients():
    patients = Patient.query.all()
    return jsonify([
        {'id': p.id, 'first_name': p.first_name, 'last_name': p.last_name}
        for p in patients
    ])
    
@app.route('/api/patients', methods=['POST'])
def api_add_patient():  # <-- RENAMED to avoid collision!
    data = request.json
    patient = Patient(first_name=data['first_name'], last_name=data['last_name'])
    db.session.add(patient)
    db.session.commit()
    return jsonify({'id': patient.id}), 201

# ---- API Endpoints ----

@app.route('/api/therapist_list', methods=['GET'])
def get_therapists():
    therapists = Therapist.query.all()
    return jsonify([
        {'id': t.id, 'first_name': t.first_name, 'last_name': t.last_name}
        for t in therapists
    ])

@app.route('/api/therapists', methods=['POST'])
def api_add_therapist():
    data = request.json
    therapist = Therapist(first_name=data['first_name'], last_name=data['last_name'])
    db.session.add(therapist)
    db.session.commit()
    return jsonify({'id': therapist.id}), 201


# ---- Admin-Only Add Therapist (Full fields) ----

@app.route('/admin/add_therapist', methods=['GET', 'POST'])
@login_required
def admin_add_therapist():
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
        is_admin = bool(request.form.get('is_admin'))

        if Therapist.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return render_template('therapist_form.html', form_title="Add Therapist (Admin)", therapist=None)

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
            is_admin=is_admin
        )
        db.session.add(new_therapist)
        db.session.commit()
        flash("New therapist created!", "success")
        return redirect(url_for('therapist_list'))

    return render_template('therapist_form.html', form_title="Add Therapist (Admin)", therapist=None)

# ---- Classic List/Add/Edit/Delete ----

@app.route('/therapist_list')
@login_required
def therapist_list():
    therapists = Therapist.query.all()
    return render_template('therapist_list.html', therapists=therapists)

@app.route('/therapist_add', methods=['GET', 'POST'])
@login_required
def therapist_add():
    # If you want to restrict to admin, add:
    # if not current_user.is_admin: abort(403)
    if request.method == 'POST':
        t = Therapist(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            credentials=request.form.get('credentials', ''),
            phone=request.form.get('phone', ''),
            email=request.form.get('email', '')
        )
        db.session.add(t)
        db.session.commit()
        flash('Therapist added!')
        return redirect(url_for('therapist_list'))
    return render_template('therapist_form.html', form_title="Add Therapist", therapist=None)

@app.route('/therapist_edit/<int:therapist_id>', methods=['GET', 'POST'])
@login_required
def therapist_edit(therapist_id):
    t = Therapist.query.get_or_404(therapist_id)
    if request.method == 'POST':
        t.first_name = request.form['first_name']
        t.last_name = request.form['last_name']
        t.credentials = request.form.get('credentials', '')
        t.phone = request.form.get('phone', '')
        t.email = request.form.get('email', '')
        t.pt_license = request.form.get('pt_license', '')
        t.npi = request.form.get('npi', '')
        t.availability = request.form.get('availability', '')
        db.session.commit()
        flash('Therapist updated!')
        return redirect(url_for('therapist_list'))
    return render_template('therapist_form.html', form_title="Edit Therapist", therapist=t)

@app.route('/therapist_delete/<int:therapist_id>', methods=['POST'])
@login_required
def therapist_delete(therapist_id):
    t = Therapist.query.get_or_404(therapist_id)
    db.session.delete(t)
    db.session.commit()
    flash('Therapist deleted!')
    return redirect(url_for('therapist_list'))

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
