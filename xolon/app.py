from xolon.factory import create_app

app = create_app()

app.config.from_envvar('FLASK_SECRETS')

if __name__ == '__main__':
    app.run()
