# Site meta
SITE_NAME = 'Xolentum Web Wallet'

# Daemon
DAEMON_PROTO = 'http'
DAEMON_HOST = 'localhost'
DAEMON_PORT = 13580
DAEMON_USER = ''
DAEMON_PASS = ''

# Wallets
WALLET_DIR = './data/wallets'
XOLENTUM_IMAGE = 'xolentum/xolentum:latest'

# Security
PASSWORD_SALT = 'salt here'  # database salts
SECRET_KEY = 'secret session key here'  # encrypts the session token

# Session
PERMANENT_SESSION_LIFETIME = 1800  # 60 minute session expiry
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
DB_PORT = 5432
DB_NAME = 'xolon'
DB_USER = 'xolon'
DB_PASS = 'password'

# Development
TEMPLATES_AUTO_RELOAD = True

# Social
SOCIAL = {
    'envelope': 'mailto:atom@xolentum.org',
    'facebook': 'https://facebook.com/xolentum/',
    'medium': 'https://medium.com/@xolentum/',
    'twitter': 'https://twitter.com/@xolentum',
    'discord': 'https://chat.xolentum.org/'
}
