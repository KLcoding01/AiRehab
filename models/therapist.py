from . import db

class Therapist(db.Model):
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

    visits = db.relationship("Visit", back_populates="therapist", cascade="all, delete-orphan")
    schedule_events = db.relationship('ScheduleEvent', back_populates='therapist', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Therapist {self.first_name} {self.last_name}>"
