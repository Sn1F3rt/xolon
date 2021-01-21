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
from xolon.blueprints.wallet import wallet_bp
from xolon.library.docker import docker
from xolon.library.helpers import capture_event
from xolon.library.jsonrpc import Wallet, to_atomic
from xolon.library.cache import cache
from xolon.forms import Send, Delete, Restore
from xolon.factory import db
from xolon.models import User
from xolon import config


@wallet_bp.route('/wallet/setup', methods=['GET', 'POST'])
@login_required
def setup():
    if current_user.wallet_created:
        return redirect(url_for('wallet.dashboard'))
    else:
        restore_form = Restore()
        if restore_form.validate_on_submit():
            c = docker.create_wallet(current_user.id, restore_form.seed.data)
            cache.store_data(f'init_wallet_{current_user.id}', 30, c)
            capture_event(current_user.id, 'restore_wallet')
            current_user.wallet_created = True
            db.session.commit()
            return redirect(url_for('wallet.loading'))
        else:
            return render_template(
                'wallet/setup.html',
                restore_form=restore_form
            )


@wallet_bp.route('/wallet/loading')
@login_required
def loading():
    if current_user.wallet_connected and current_user.wallet_created:
        return redirect(url_for('wallet.dashboard'))

    if current_user.wallet_created is False:
        return redirect(url_for('wallet.setup'))

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
        sleep(1.5)
        return redirect(url_for('wallet.loading'))

    address = wallet.get_address()
    transfers = wallet.get_transfers()
    for type in transfers:
        for tx in transfers[type]:
            all_transfers.append(tx)
    balances = wallet.get_balances()
    qr_uri = f'xolentum:{address}?tx_description={current_user.email}'
    address_qr = qrcode_make(qr_uri).save(_address_qr)
    qrcode = b64encode(_address_qr.getvalue()).decode()
    seed = wallet.seed()
    spend_key = wallet.spend_key()
    view_key = wallet.view_key()
    capture_event(current_user.id, 'load_dashboard')
    return render_template(
        'wallet/dashboard.html',
        transfers=all_transfers,
        sorted_txes=get_sorted_txes(transfers),
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
    if current_user.wallet_created is False:
        data = {
            'result': 'fail',
            'message': 'Wallet not yet created'
        }
        return jsonify(data)

    if current_user.wallet_connected is False:
        wallet = docker.start_wallet(current_user.id)
        port = docker.get_port(wallet)
        current_user.wallet_connected = docker.container_exists(wallet)
        current_user.wallet_port = port
        current_user.wallet_container = wallet
        current_user.wallet_start = datetime.utcnow()
        db.session.commit()
        capture_event(current_user.id, 'start_wallet')
        data = {
            'result': 'success',
            'message': 'Wallet has been connected'
        }
    else:
        data = {
            'result': 'fail',
            'message': 'Wallet is already connected'
        }

    return jsonify(data)


@wallet_bp.route('/wallet/create')
@login_required
def create():
    if current_user.wallet_created is False:
        c = docker.create_wallet(current_user.id)
        cache.store_data(f'init_wallet_{current_user.id}', 30, c)
        capture_event(current_user.id, 'create_wallet')
        current_user.wallet_created = True
        db.session.commit()
        return redirect(url_for('wallet.loading'))
    else:
        return redirect(url_for('wallet.dashboard'))


@wallet_bp.route('/wallet/status')
@login_required
def status():
    user_vol = docker.get_user_volume(current_user.id)
    create_container = cache.get_data(f'init_wallet_{current_user.id}')
    data = {
        'created': current_user.wallet_created,
        'connected': current_user.wallet_connected,
        'port': current_user.wallet_port,
        'container': current_user.wallet_container,
        'volume': docker.volume_exists(user_vol),
        'initializing': docker.container_exists(create_container)
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

        # Check if Xolentum wallet is available
        if wallet.connected is False:
            flash('Wallet RPC interface is unavailable at this time. Try again later.')
            capture_event(user.id, 'tx_fail_address_invalid')
            return redirect(redirect_url)

        # Quick n dirty check to see if address is XOL
        if len(address) not in [97, 108]:
            flash('Invalid Xolentum address provided.')
            capture_event(user.id, 'tx_fail_address_invalid')
            return redirect(redirect_url)

        # Check if we're sweeping or not
        if send_form.amount.data == 'all':
            tx = wallet.transfer(address, None, 'sweep_all')
        else:
            # Make sure the amount provided is a number
            # noinspection PyBroadException
            try:
                amount = to_atomic(Decimal(send_form.amount.data))

            except:
                flash('Invalid Xolentum amount specified.')
                capture_event(user.id, 'tx_fail_amount_invalid')
                return redirect(redirect_url)

            # Send transfer
            tx = wallet.transfer(address, amount)

        # Inform user of result and redirect
        if 'message' in tx:
            msg = tx['message'].capitalize()
            msg_lower = tx['message'].replace(' ', '_').lower()
            flash(f'There was a problem sending the transaction: {msg}')
            capture_event(user.id, f'tx_fail_{msg_lower}')
        else:
            flash('Successfully sent transfer.')
            capture_event(user.id, 'tx_success')

        return redirect(redirect_url)
    else:
        for field, errors in send_form.errors.items():
            flash(f'{send_form[field].label}: {", ".join(errors)}')
        return redirect(redirect_url)


def get_sorted_txes(_txes):
    total = 0
    txes = {}
    sorted_txes = {}
    for tx_type in _txes:
        for t in _txes[tx_type]:
            txes[t['txid']] = {
                'type': tx_type,
                'amount': t['amount'],
                'timestamp': t['timestamp'],
                'fee': t['fee']
            }

    for i in sorted(txes.items(), key=lambda x: x[1]['timestamp']):
        if i[1]['type'] == 'in':
            total += i[1]['amount']
        elif i[1]['type'] == 'out':
            total -= i[1]['amount']
            total -= i[1]['fee']
        sorted_txes[i[0]] = {
            'type': i[1]['type'],
            'amount': i[1]['amount'],
            'timestamp': i[1]['timestamp'],
            'total': total
        }
    return sorted_txes
