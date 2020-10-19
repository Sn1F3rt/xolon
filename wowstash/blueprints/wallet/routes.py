from time import sleep
from io import BytesIO
from base64 import b64encode
from qrcode import make as qrcode_make
from decimal import Decimal
from flask import request, render_template, session, jsonify
from flask import redirect, url_for, current_app, flash
from flask_login import login_required, current_user
from socket import socket
from datetime import datetime
from wowstash.blueprints.wallet import wallet_bp
from wowstash.library.docker import docker
from wowstash.library.elasticsearch import send_es
from wowstash.library.jsonrpc import Wallet, to_atomic
from wowstash.library.cache import cache
from wowstash.forms import Send, Delete
from wowstash.factory import db
from wowstash.models import User
from wowstash import config


@wallet_bp.route('/wallet/loading')
@login_required
def loading():
    if current_user.wallet_connected and current_user.wallet_created:
        sleep(1)
        return redirect(url_for('wallet.dashboard'))
    return render_template('wallet/loading.html')

@wallet_bp.route('/wallet/dashboard')
@login_required
def dashboard():
    send_form = Send()
    delete_form = Delete()
    _address_qr = BytesIO()
    all_transfers = list()
    wallet = Wallet(
        proto='http',
        host='127.0.0.1',
        port=current_user.wallet_port,
        username=current_user.id,
        password=current_user.wallet_password
    )
    if not docker.container_exists(current_user.wallet_container):
        current_user.clear_wallet_data()
        return redirect(url_for('wallet.loading'))

    if not wallet.connected:
        return redirect(url_for('wallet.loading'))

    address = wallet.get_address()
    transfers = wallet.get_transfers()
    for type in transfers:
        for tx in transfers[type]:
            all_transfers.append(tx)
    balances = wallet.get_balances()
    qr_uri = f'wownero:{address}?tx_description={current_user.email}'
    address_qr = qrcode_make(qr_uri).save(_address_qr)
    qrcode = b64encode(_address_qr.getvalue()).decode()
    seed = wallet.seed()
    spend_key = wallet.spend_key()
    view_key = wallet.view_key()
    send_es({'type': 'load_dashboard', 'user': current_user.email})
    return render_template(
        'wallet/dashboard.html',
        transfers=all_transfers,
        balances=balances,
        address=address,
        qrcode=qrcode,
        send_form=send_form,
        delete_form=delete_form,
        user=current_user,
        seed=seed,
        spend_key=spend_key,
        view_key=view_key,
    )

@wallet_bp.route('/wallet/connect')
@login_required
def connect():
    if current_user.wallet_connected is False:
        wallet = docker.start_wallet(current_user.id)
        port = docker.get_port(wallet)
        current_user.wallet_connected = docker.container_exists(wallet)
        current_user.wallet_port = port
        current_user.wallet_container = wallet
        current_user.wallet_start = datetime.utcnow()
        db.session.commit()

    return 'ok'

@wallet_bp.route('/wallet/create')
@login_required
def create():
    if current_user.wallet_created is False:
        docker.create_wallet(current_user.id)
        current_user.wallet_created = True
        db.session.commit()

    return 'ok'

@wallet_bp.route('/wallet/status')
@login_required
def status():
    data = {
        'created': current_user.wallet_created,
        'connected': current_user.wallet_connected,
        'port': current_user.wallet_port,
        'container': current_user.wallet_container
    }
    return jsonify(data)

@wallet_bp.route('/wallet/send', methods=['GET', 'POST'])
@login_required
def send():
    send_form = Send()
    redirect_url = url_for('wallet.dashboard') + '#send'
    wallet = Wallet(
        proto='http',
        host='127.0.0.1',
        port=current_user.wallet_port,
        username=current_user.id,
        password=current_user.wallet_password
    )
    if send_form.validate_on_submit():
        address = str(send_form.address.data)
        user = User.query.get(current_user.id)

        # Check if Wownero wallet is available
        if wallet.connected is False:
            flash('Wallet RPC interface is unavailable at this time. Try again later.')
            send_es({'type': 'tx_fail_rpc_unavailable', 'user': user.email})
            return redirect(redirect_url)

        # Quick n dirty check to see if address is WOW
        if len(address) not in [97, 108]:
            flash('Invalid Wownero address provided.')
            send_es({'type': 'tx_fail_address_invalid', 'user': user.email})
            return redirect(redirect_url)

        # Check if we're sweeping or not
        if send_form.amount.data == 'all':
            tx = wallet.transfer(address, None, 'sweep_all')
        else:
            # Make sure the amount provided is a number
            try:
                amount = to_atomic(Decimal(send_form.amount.data))
            except:
                flash('Invalid Wownero amount specified.')
                send_es({'type': 'tx_fail_amount_invalid', 'user': user.email})
                return redirect(redirect_url)

            # Send transfer
            tx = wallet.transfer(address, amount)

        # Inform user of result and redirect
        if 'message' in tx:
            msg = tx['message'].capitalize()
            msg_lower = tx['message'].replace(' ', '_').lower()
            flash(f'There was a problem sending the transaction: {msg}')
            send_es({'type': f'tx_fail_{msg_lower}', 'user': user.email})
        else:
            flash('Successfully sent transfer.')
            send_es({'type': 'tx_success', 'user': user.email})

        return redirect(redirect_url)
    else:
        for field, errors in send_form.errors.items():
            flash(f'{send_form[field].label}: {", ".join(errors)}')
        return redirect(redirect_url)
