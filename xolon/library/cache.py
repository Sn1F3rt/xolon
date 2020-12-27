from json import loads as json_loads
from json import dumps as json_dumps
from requests import get as r_get
from datetime import timedelta
from redis import Redis
from xolon import config


class Cache(object):
    def __init__(self):
        self.redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)

    def store_data(self, item_name, expiration_minutes, data):
        self.redis.setex(
            item_name,
            timedelta(minutes=expiration_minutes),
            value=data
        )

    def get_coin_info(self):
        info = self.redis.get("coin_info")
        if info:
            return json_loads(info)
        else:
            data = {
                'localization': False,
                'tickers': False,
                'market_data': True,
                'community_data': False,
                'developer_data': False,
                'sparkline': False
            }
            headers = {'accept': 'application/json'}
            url = 'https://api.coingecko.com/api/v3/coins/xolentum'
            # noinspection PyBroadException
            try:
                r = r_get(url, headers=headers, data=data)
                info = {
                    'genesis_date': r.json()['genesis_date'],
                    'market_cap_rank': r.json()['market_cap_rank'],
                    'current_price': r.json()['market_data']['current_price']['usd'],
                    'market_cap': r.json()['market_data']['market_cap']['usd'],
                    'total_volume': r.json()['market_data']['total_volume']['usd'],
                    'last_updated': r.json()['last_updated']
                }
                self.store_data("coin_info", 15, json_dumps(info))
                return info

            except:
                return {}


cache = Cache()
