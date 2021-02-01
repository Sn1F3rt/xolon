from xolon.models import Event, Internal
from xolon.factory import db


def capture_event(user_id, event_type):
    event = Event(
        user=user_id,
        type=event_type
    )
    db.session.add(event)
    return db.session.commit()


def on_maintenance():
    # noinspection PyBroadException
    try:
        db.session.commit()

    except:
        db.session.rollback()
        db.session.close()

    return Internal.query.filter_by(key='SITE_MAINTENANCE').first().value


def set_maintenance(enable=False):
    db.session.commit()
    rec = Internal.query.filter_by(key='SITE_MAINTENANCE').first()
    rec.value = enable
    db.session.add(rec)
    db.session.commit()
