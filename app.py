import flask
print("==== FLASK VERSION IS:", flask.__version__, "====")
print("==== FLASK MODULE FILE:", flask.__file__, "====")
print("==== FLASK OBJECT DIR:", dir(flask.Flask), "====")

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from models.patient import db, Patient
from models.visit import Visit
from models.attachment import Attachment
from config import Config
import os
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# --- Create DB (local testing) ---
@app.before_first_request
def create_tables():
    db.create_all()

# --- Home / Patients List ---
@app.route('/')
def index():
    patients = Patient.query.all()
    return render_template('index.html', patients=patients)

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
