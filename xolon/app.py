from flask import redirect, url_for
from xolon.factory import create_app

app = create_app()


@app.before_request
def check_for_maintenance():
    if app.config['SITE_MAINTENANCE']:
        return redirect(url_for('meta.maintenance'))


if __name__ == '__main__':
    app.run()
