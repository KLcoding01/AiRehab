from . import db

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))

    visits = db.relationship('Visit', back_populates='patient', cascade="all, delete-orphan")
    attachments = db.relationship('Attachment', back_populates='patient', cascade="all, delete-orphan")
