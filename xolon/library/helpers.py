from xolon.models import Event
from xolon.factory import db


def capture_event(user_id, event_type):
    event = Event(
        user=user_id,
        type=event_type
    )
    db.session.add(event)
    db.session.commit()
    return
