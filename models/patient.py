from . import db

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    dob = db.Column(db.Date)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))

    visits = db.relationship('Visit', back_populates='patient')
    attachments = db.relationship('Attachment', back_populates='patient')
    calendar_events = db.relationship('CalendarEvent', back_populates='patient')
