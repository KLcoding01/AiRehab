from . import db

class Therapist(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    credentials = db.Column(db.String(80))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    availability = db.Column(db.String(255))
    npi = db.Column(db.String(20))
    pt_license = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, default=False)
    
    visits = db.relationship('Visit', back_populates='therapist')

