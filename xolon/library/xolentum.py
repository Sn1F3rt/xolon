import requests
import six
import json
import operator
from tipbot import config
from decimal import Decimal


PICOXOL = Decimal('0.000000000001')

class Wallet(object):
    def __init__(self):
        self.host = config.WALLET_HOST
        self.port = config.WALLET_PORT
        self.proto = config.WALLET_PROTO
        self.username = config.WALLET_USER
        self.password = config.WALLET_PASS
        self.endpoint = '{}://{}:{}/json_rpc'.format(
            self.proto, self.host, self.port
        )
        self.auth = requests.auth.HTTPDigestAuth(
            self.username, self.password
        )

        try:
            r = self.height()
            height = r['height']
            self.connected = True
        except:
            self.connected = False

    def make_wallet_rpc(self, method, params={}):
        r = requests.get(
            self.endpoint,
            data=json.dumps({'method': method, 'params': params}),
            auth=self.auth
        )
        # print(r.status_code)
        if 'error' in r.json():
            return r.json()['error']
        else:
            return r.json()['result']

    def height(self):
        return self.make_wallet_rpc('get_height', {})

    def spend_key(self):
        return self.make_wallet_rpc('query_key', {'key_type': 'spend_key'})['key']

    def view_key(self):
        return self.make_wallet_rpc('query_key', {'key_type': 'view_key'})['key']

    def seed(self):
        return self.make_wallet_rpc('query_key', {'key_type': 'mnemonic'})['key']

    def accounts(self):
        accounts = []
        _accounts = self.make_wallet_rpc('get_accounts')
        idx = 0
        self.master_address = _accounts['subaddress_accounts'][0]['base_address']
        for _acc in _accounts['subaddress_accounts']:
            assert idx == _acc['account_index']
            accounts.append(_acc['account_index'])
            idx += 1
        return accounts

    def new_account(self, label=None):
        _account = self.make_wallet_rpc('create_account', {'label': label})
        return _account['account_index']

    def addresses(self, account=0, addr_indices=None):
        qdata = {'account_index': account}
        if addr_indices:
            qdata['address_index'] = addr_indices
        _addresses = self.make_wallet_rpc('get_address', qdata)
        addresses = [None] * (max(map(operator.itemgetter('address_index'), _addresses['addresses'])) + 1)
        for _addr in _addresses['addresses']:
            addresses[_addr['address_index']] = _addr['address']
        return addresses

    def new_address(self, account=0, label=None):
        data = {'account_index': account, 'label': label}
        _address = self.make_wallet_rpc('create_address', data)
        return (_address['address_index'], _address['address'])

    def balances(self, account=0):
        data = {'account_index': account}
        _balance = self.make_wallet_rpc('get_balance', data)
        return (from_atomic(_balance['balance']), from_atomic(_balance['unlocked_balance']))

    def transfer(self, dest_address, amount, priority, account):
        data = {
            'account_index': account,
            'destinations': [{'address': dest_address, 'amount': to_atomic(amount)}],
            'priority': priority,
            'unlock_time': 0,
            'get_tx_key': True,
            'get_tx_hex': True,
            'new_algorithm': True,
            'do_not_relay': False,
            'ring_size': 5
        }
        transfer = self.make_wallet_rpc('transfer', data)
        return transfer


def to_atomic(amount):
    if not isinstance(amount, (Decimal, float) + six.integer_types):
        raise ValueError("Amount '{}' doesn't have numeric type. Only Decimal, int, long and "
                "float (not recommended) are accepted as amounts.")
    return int(amount * 10**11)

def from_atomic(amount):
    return (Decimal(amount) * PICOXOL).quantize(PICOXOL)

def as_xolentum(amount):
    return Decimal(amount).quantize(PICOXOL)
