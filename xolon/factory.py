import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from redis import Redis
from datetime import datetime
from xolon import config


db = SQLAlchemy()
bcrypt = Bcrypt()


def _setup_db(app: Flask):
    uri = 'postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}'.format(
        user=config.DB_USER,
        pw=config.DB_PASS,
        host=config.DB_HOST,
        port=config.DB_PORT,
        db=config.DB_NAME
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

        # Routes/blueprints
        from xolon.blueprints.auth import auth_bp
        from xolon.blueprints.wallet import wallet_bp
        from xolon.blueprints.meta import meta_bp
        app.register_blueprint(meta_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(wallet_bp)

        return app
