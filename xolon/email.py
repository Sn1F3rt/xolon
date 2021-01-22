from flask_mail import Message, Mail

from xolon import app, config

mail = Mail(app)


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=config.MAIL_DEFAULT_SENDER
    )
    mail.send(msg)
