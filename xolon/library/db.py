from pymysql import connect
from xolon import config


class Database(object):
    def __init__(self):
        self.conn = connect(
            user=config.DB_USER,
            password=config.DB_PASS,
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME
        )

        cursor = self.conn.cursor()
        cursor.execute("SELECT VERSION();")
        results = cursor.fetchone()
        if results:
            self.connected = True
        else:
            self.connected = False
