from wowstash.factory import create_app
from wowstash import config

app = create_app()

if __name__ == '__main__':
    app.run()
