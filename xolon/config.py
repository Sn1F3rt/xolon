# Site meta
SITE_NAME = 'Xolentum Web Wallet'
PROJECT_NAME = 'The Xolentum Project'
PROJECT_WEB = 'https://www.xolentum.org'

# Daemon
DAEMON_PROTO = 'http'
DAEMON_HOST = 'localhost'
DAEMON_PORT = 13580
DAEMON_USER = ''
DAEMON_PASS = ''

# Wallets
WALLET_DIR = './data/wallets'
XOLENTUM_IMAGE = 'xolentum/xolentum:v0.3.0.0'

# Security
PASSWORD_SALT = 'salt here'  # database salts
SECRET_KEY = 'secret session key here'  # encrypts the session token

# Session
PERMANENT_SESSION_LIFETIME = 3600  # 60 minute session expiry
SESSION_COOKIE_NAME = 'xolon'
SESSION_COOKIE_DOMAIN = '127.0.0.1'
SESSION_COOKIE_SECURE = False
SESSION_USE_SIGNER = True
SESSION_PERMANENT = True

# Redis
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Database
DB_HOST = 'localhost'
DB_PORT = 3306
DB_NAME = 'xolon'
DB_USER = 'xolon'
DB_PASS = 'password'

# Email
MAIL_SERVER = 'smtp.example.com'
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = ''
MAIL_PASSWORD = ''
MAIL_DEFAULT_SENDER = ('Xolon', 'xolon@example.com')

# Recaptcha
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''

# Development
TEMPLATES_AUTO_RELOAD = True
MAIL_DEBUG = True

# Maintenance
SITE_MAINTENANCE = False

# Social
SOCIAL = {
    'envelope': 'mailto:atom@xolentum.org',
    'github': 'https://github.com/sohamb03/xolon/issues',
    'twitter': 'https://twitter.com/@xolentum',
    'discord': 'https://discord.gg/FTJ4tDQ',
    'telegram': 'https://t.me/xolentum/'
}
