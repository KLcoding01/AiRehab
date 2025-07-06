from . import db

class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=True)
    therapist_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(512))

    # Relationship to Patient if needed
    patient = db.relationship('Patient', backref='calendar_events')
