from . import db

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    therapist_id = db.Column(db.Integer, db.ForeignKey('therapist.id'))

    patient = db.relationship('Patient', back_populates='visits')
    therapist = db.relationship('Therapist', back_populates='visits')
