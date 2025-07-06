from . import db

class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.String(512))

    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=True)
    therapist_id = db.Column(db.Integer, db.ForeignKey('therapist.id'), nullable=True)

    # Relationships
    patient = db.relationship('Patient', backref='calendar_events')
    therapist = db.relationship('Therapist', backref='calendar_events')
