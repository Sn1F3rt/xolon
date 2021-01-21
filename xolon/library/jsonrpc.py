import json
import requests
from six import integer_types
from decimal import Decimal
from xolon import config


PICO_XOL = Decimal('0.000000000001')


class JSONRPC(object):
    def __init__(self, proto, host, port, username='', password=''):
        self.endpoint = '{}://{}:{}/'.format(
            proto, host, port
        )
        # noinspection PyUnresolvedReferences
        self.auth = requests.auth.HTTPDigestAuth(
            username, password
        )

    def make_rpc(self, method, params=None, json_rpc=True):
        if params is None:
            params = {}

        if json_rpc:
            endpoint = self.endpoint + "json_rpc"

        else:
            endpoint = self.endpoint + method

        # noinspection PyBroadException
        try:
            r = requests.get(
                endpoint,
                data=json.dumps({'method': method, 'params': params}),
                auth=self.auth
            )
            if 'result' in r.json():
                return r.json()['result']
            elif 'error' in r.json():
                return r.json()['error']
            else:
                return r.json()

        except:
            return {}


class Wallet(JSONRPC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'height' in self.height():
            self.connected = True
        else:
            self.connected = False

    def height(self):
        return self.make_rpc('get_height', {})

    def spend_key(self):
        return self.make_rpc('query_key', {'key_type': 'spend_key'})['key']

    def view_key(self):
        return self.make_rpc('query_key', {'key_type': 'view_key'})['key']

    def seed(self):
        return self.make_rpc('query_key', {'key_type': 'mnemonic'})['key']

    def new_address(self, account_index=0, label=None):
        data = {'account_index': account_index, 'label': label}
        _address = self.make_rpc('create_address', data)
        return _address['address_index'], _address['address']

    def get_address(self, account_index=0):
        data = {'account_index': account_index}
        address = self.make_rpc('get_address', data)['address']
        return address

    def get_balances(self, account_index=0):
        data = {'account_index': account_index}
        balance = self.make_rpc('get_balance', data)
        return balance['balance'], balance['unlocked_balance']

    def get_transfers(self, account_index=0):
        data = {
            'account_index': account_index,
            'in': True,
            'out': True,
            'pending': True,
            'failed': True,
            'pool': True
        }
        return self.make_rpc('get_transfers', data)

    def transfer(self, dest_address, atomic_amount, _type='transfer', account_index=0):
        data = {
            'account_index': account_index,
            'priority': 0,
            'unlock_time': 0,
            'get_tx_key': True,
            'get_tx_hex': True,
            'new_algorithm': True,
            'do_not_relay': False,
            'ring_size': 5
        }
        if _type == 'sweep_all':
            data['address'] = dest_address
            transfer = self.make_rpc('sweep_all', data)
        else:
            data['destinations'] = [{
                'address': dest_address,
                'amount': atomic_amount
            }]
            transfer = self.make_rpc('transfer', data)
        return transfer


class Daemon(JSONRPC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def info(self):
        return self.make_rpc('get_info', {}, json_rpc=False)

    def height(self):
        return self.make_rpc('get_height', {}, json_rpc=False)


def to_atomic(amount):
    if not isinstance(amount, (Decimal, float) + integer_types):
        raise ValueError("Amount '{}' doesn't have numeric type. Only Decimal, int, long and "
                         "float (not recommended) are accepted as amounts.")
    return int(amount * 10**12)


def from_atomic(amount):
    return (Decimal(amount) * PICO_XOL).quantize(PICO_XOL)


def as_xolentum(amount):
    return Decimal(amount).quantize(PICO_XOL)


daemon = Daemon(
    proto=config.DAEMON_PROTO,
    host=config.DAEMON_HOST,
    port=config.DAEMON_PORT,
    username=config.DAEMON_USER,
    password=config.DAEMON_PASS
)
