from flask import request, render_template, session, redirect, url_for, make_response, jsonify
from wowstash.blueprints.meta import meta_bp
from wowstash.library.jsonrpc import daemon
from wowstash.library.cache import cache
from wowstash.library.db import Database
from wowstash.library.docker import Docker


@meta_bp.route('/')
def index():
    return render_template('meta/index.html', node=daemon.info(), info=cache.get_coin_info())

@meta_bp.route('/faq')
def faq():
    return render_template('meta/faq.html')

@meta_bp.route('/terms')
def terms():
    return render_template('meta/terms.html')

@meta_bp.route('/privacy')
def privacy():
    return render_template('meta/privacy.html')

@meta_bp.route('/health')
def health():
    return make_response(jsonify({
        'redis': cache.redis.ping(),
        'postgres': Database().connected,
        'docker': Docker().client.ping()
    }), 200)

# @app.errorhandler(404)
# def not_found(error):
#     return make_response(jsonify({
#         'error': 'Page not found'
#     }), 404)
