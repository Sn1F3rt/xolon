from flask_mail import Message
from xolon.factory import mail
from xolon.config import MAIL_DEFAULT_SENDER


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=MAIL_DEFAULT_SENDER
    )
    mail.send(msg)
