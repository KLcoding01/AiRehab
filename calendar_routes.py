# calendar_routes.py

from flask import Blueprint, jsonify, request
from models.calendar_event import CalendarEvent
from models import db
from datetime import datetime

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/api/events', methods=['GET'])
def get_events():
    events = CalendarEvent.query.all()
    return jsonify([
        {
            'id': e.id,
            'title': e.title,
            'start': e.start.isoformat(),
            'end': e.end.isoformat(),
            'patient_id': e.patient_id,
            'therapist_id': e.therapist_id,
            'description': e.description
        } for e in events
    ])

@calendar_bp.route('/api/events', methods=['POST'])
def add_event():
    data = request.get_json()
    event = CalendarEvent(
        title=data['title'],
        start=datetime.fromisoformat(data['start']),
        end=datetime.fromisoformat(data['end']),
        patient_id=data.get('patient_id'),
        therapist_id=data.get('therapist_id'),
        description=data.get('description')
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({'status': 'success', 'id': event.id}), 201

@calendar_bp.route('/api/events/<int:event_id>', methods=['PUT'])
def edit_event(event_id):
    data = request.get_json()
    event = CalendarEvent.query.get(event_id)
    event.title = data['title']
    event.start = datetime.fromisoformat(data['start'])
    event.end = datetime.fromisoformat(data['end'])
    event.patient_id = data.get('patient_id')
    event.therapist_id = data.get('therapist_id')
    event.description = data.get('description')
    db.session.commit()
    return jsonify({'status': 'success'
