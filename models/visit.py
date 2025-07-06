from . import db

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)

    patient = db.relationship('Patient', back_populates='visits')
