from datetime import datetime
from elasticsearch import Elasticsearch
from xolon import config


def send_es(data):
    if getattr(config, 'ELASTICSEARCH_ENABLED', False):
        try:
            es = Elasticsearch(
                [getattr(config, 'ELASTICSEARCH_HOST', 'localhost')]
            )
            now = datetime.utcnow()
            index_ts = now.strftime('%Y%m%d')
            data['datetime'] = now
            es.index(
                index="{}-{}".format(
                    getattr(config, 'ELASTICSEARCH_INDEX_NAME', 'xolon'),
                    index_ts
            ), body=data)
        except Exception as e:
            print('Could not capture event in Elasticsearch: ', e)
            pass # I don't really care if this logs...
