from wowstash.library.jsonrpc import wallet
from wowstash.models import Transaction
from wowstash.factory import db


# @app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({
        'error': 'Page not found'
    }), 404)

# @app.cli.command('initdb')
def init_db():
    db.create_all()

# @app.cli.command('send_transfers')
def send_transfers():
    txes = Transaction.query.all()
    for i in txes:
        print(i)
    # tx = wallet.transfer(
    #     0, current_user.subaddress_index, address, amount
    # )
