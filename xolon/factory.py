import click
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail, Message
from redis import Redis
from datetime import datetime
from xolon import config


db = SQLAlchemy()
bcrypt = Bcrypt()

mail = None
_SITE_MAINTENANCE = False


def _setup_db(app: Flask):
    uri = 'mysql+pymysql://{user}:{pw}@{host}:{port}/{db}'.format(
        user=config.DB_USER,
        pw=config.DB_PASS,
        host=config.DB_HOST,
        port=config.DB_PORT,
        db=config.DB_NAME
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size': 100,
                                               'pool_recycle': 300
                                               }
    db = SQLAlchemy(app)
    import xolon.models
    db.create_all()


def create_app():
    app = Flask(__name__)
    app.config.from_envvar('FLASK_SECRETS')

    # Setup backends
    _setup_db(app)
    bcrypt = Bcrypt(app)
    login_manager = LoginManager(app)

    global mail
    mail = Mail(app)

    with app.app_context():

        # Login manager
        login_manager.login_view = 'auth.login'
        login_manager.logout_view = 'auth.logout'

        @login_manager.user_loader
        def load_user(user_id):
            from xolon.models import User
            user = User.query.get(user_id)
            return user

        # Template filters
        @app.template_filter('datestamp')
        def datestamp(s):
            d = datetime.fromtimestamp(s)
            return d.strftime('%Y-%m-%d %H:%M:%S')

        @app.template_filter('from_atomic')
        def from_atomic(a):
            from xolon.library.jsonrpc import from_atomic
            atomic = from_atomic(a)
            if atomic == 0:
                return 0
            else:
                return float(atomic)

        # Maintenance
        @app.before_request
        def check_for_maintenance():
            global _SITE_MAINTENANCE
            if _SITE_MAINTENANCE:
                return redirect(url_for('meta.maintenance'))

        # CLI
        @app.cli.command('clean_containers')
        def clean_containers():
            from xolon.library.docker import docker
            docker.cleanup()

        @app.cli.command('reset_wallet')
        @click.argument('user_id')
        def reset_wallet(user_id):
            from xolon.models import User
            user = User.query.get(user_id)
            user.clear_wallet_data()
            print(f'Wallet data cleared for user {user.id}')

        # noinspection PyUnresolvedReferences
        @app.cli.command('init')
        def init():
            import xolon.models
            db.create_all()

        @app.cli.commad('maintenance')
        @click.argument('mode')
        def maintenance(mode):
            global _SITE_MAINTENANCE
            if mode == 'enable':
                _SITE_MAINTENANCE = True

            elif mode == 'disable':
                _SITE_MAINTENANCE = False

            else:
                print('Usage : flask maintenance enable/disable ')

        # Routes/blueprints
        from xolon.blueprints.auth import auth_bp
        from xolon.blueprints.wallet import wallet_bp
        from xolon.blueprints.meta import meta_bp
        app.register_blueprint(meta_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(wallet_bp)

        return app
