from xolon.factory import create_app
from xolon import config

app = create_app()

if __name__ == '__main__':
    app.run()
