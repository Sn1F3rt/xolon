# Site meta
SITE_NAME = 'WOW Stash'

# Daemon
DAEMON_PROTO = 'http'
DAEMON_HOST = 'node.suchwow.xyz'
DAEMON_PORT = 34568
DAEMON_USER = ''
DAEMON_PASS = ''

# Wallets
WALLET_DIR = './data/wallets'
XOLENTUM_IMAGE = 'lalanza808/xolentum:v0.9.0.0'

# Security
PASSWORD_SALT = 'salt here' # database salts
SECRET_KEY = 'secret session key here' # encrypts the session token

# Session
PERMANENT_SESSION_LIFETIME = 1800 # 60 minute session expiry
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
DB_PASS = 'zzzzzzzzz'

# Development
TEMPLATES_AUTO_RELOAD = True
ELASTICSEARCH_ENABLED = False

# Social
SOCIAL = {
    'envelope': 'mailto:admin@domain.co',
    'twitter': 'https://twitter.com/your_twitter_handle',
    'comment': 'https://webchat.freenode.net/?room=#xolentum',
    'reddit': 'https://reddit.com/r/xolentum'
}
