from flask import redirect, url_for, render_template, make_response, jsonify
from xolon.blueprints.meta import meta_bp
from xolon.library.jsonrpc import daemon
from xolon.library.cache import cache
from xolon.library.db import Database
from xolon.library.docker import Docker
from xolon.library.helpers import on_maintenance


@meta_bp.route('/')
def index():
    return render_template('meta/index.html', node=daemon.info(), info=cache.get_coin_info())


@meta_bp.route('/faq')
def faq():
    return render_template('meta/faq.html')


@meta_bp.route('/terms_of_service')
def terms_of_service():
    return render_template('meta/terms-of-service.html')


@meta_bp.route('/privacy_policy')
def privacy_policy():
    return render_template('meta/privacy-policy.html')


@meta_bp.route('/health')
def health():
    return make_response(jsonify({
        'redis': cache.redis.ping(),
        'mysql': Database().connected,
        'docker': Docker().client.ping()
    }), 200)


@meta_bp.route('/maintenance')
def maintenance():
    if on_maintenance():
        return render_template('meta/maintenance.html'), 503

    else:
        return redirect(url_for('meta.index'))


# @app.errorhandler(404)
# def not_found(error):
#     return make_response(jsonify({
#         'error': 'Page not found'
#     }), 404)
