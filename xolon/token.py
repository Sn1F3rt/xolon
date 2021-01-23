from itsdangerous import URLSafeTimedSerializer
from xolon import config


def generate_token(email):
    serializer = URLSafeTimedSerializer(config.SECRET_KEY)
    return serializer.dumps(email, salt=config.PASSWORD_SALT)


def validate_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(config.SECRET_KEY)
    # noinspection PyBroadException
    try:
        email = serializer.loads(
            token,
            salt=config.PASSWORD_SALT,
            max_age=expiration
        )
    except:
        return False
    return email
