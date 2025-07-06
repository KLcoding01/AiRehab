from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .patient import Patient
from .therapist import Therapist
from .visit import Visit
from .attachment import Attachment
from .calendar_event import CalendarEvent
