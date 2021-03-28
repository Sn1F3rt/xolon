from docker import from_env, APIClient
from docker.errors import NotFound, NullResource, APIError
from os.path import expanduser
from secrets import token_urlsafe
from datetime import datetime, timedelta
from time import sleep
from xolon import config
from xolon.models import User
from xolon.factory import db
from xolon.library.jsonrpc import daemon


class Docker(object):
    def __init__(self):
        self.client = from_env()
        self.xolentum_image = getattr(config, 'XOLENTUM_IMAGE', 'xolentum/xolentum')
        self.wallet_dir = expanduser(getattr(config, 'WALLET_DIR', '~/data/wallets'))
        self.listen_port = 8888

    def create_wallet(self, user_id, seed=None):
        u = User.query.get(user_id)
        volume_name = self.get_user_volume(u.id)
        u.wallet_password = token_urlsafe(12)
        db.session.commit()
        if seed:
            command = f"""sh -c "yes '' | xolentum-wallet-cli \
                    --restore-deterministic-wallet \
                    --generate-new-wallet /wallet/{u.id}.wallet \
                    --restore-height 0 \
                    --password {u.wallet_password} \
                    --daemon-address {config.DAEMON_PROTO}://{config.DAEMON_HOST}:{config.DAEMON_PORT} \
                    --daemon-login {config.DAEMON_USER}:{config.DAEMON_PASS} \
                    --trusted-daemon \
                    --electrum-seed '{seed}' \
                    --log-file /wallet/{u.id}-init.log \
                    --command refresh"
                    """
        else:
            command = f"""xolentum-wallet-cli \
                    --generate-new-wallet /wallet/{u.id}.wallet \
                    --restore-height {daemon.info()['height']} \
                    --password {u.wallet_password} \
                    --mnemonic-language English \
                    --daemon-address {config.DAEMON_PROTO}://{config.DAEMON_HOST}:{config.DAEMON_PORT} \
                    --daemon-login {config.DAEMON_USER}:{config.DAEMON_PASS} \
                    --trusted-daemon \
                    --log-file /wallet/{u.id}-init.log \
                    --command version
                    """
        if not self.volume_exists(volume_name):
            self.client.volumes.create(
                name=volume_name,
                driver='local'
            )
        container = self.client.containers.run(
            self.xolentum_image,
            command=command,
            auto_remove=True,
            name=f'init_wallet_{u.id}',
            remove=True,
            detach=True,
            volumes={
                volume_name: {
                    'bind': '/wallet',
                    'mode': 'rw'
                }
            }
        )
        return container.short_id

    def start_wallet(self, user_id):
        u = User.query.get(user_id)
        container_name = f'rpc_wallet_{u.id}'
        volume_name = self.get_user_volume(u.id)
        command = f"""xolentum-wallet-rpc \
        --non-interactive \
        --rpc-bind-port {self.listen_port} \
        --rpc-bind-ip 0.0.0.0 \
        --confirm-external-bind \
        --wallet-file /wallet/{u.id}.wallet \
        --rpc-login {u.id}:{u.wallet_password} \
        --password {u.wallet_password} \
        --daemon-address {config.DAEMON_PROTO}://{config.DAEMON_HOST}:{config.DAEMON_PORT} \
        --daemon-login {config.DAEMON_USER}:{config.DAEMON_PASS} \
        --trusted-daemon \
        --mining-threads 1 \
        --log-file /wallet/{u.id}-rpc.log
        """
        try:
            container = self.client.containers.run(
                self.xolentum_image,
                command=command,
                auto_remove=True,
                name=container_name,
                remove=True,
                detach=True,
                ports={
                    f'{self.listen_port}/tcp': ('127.0.0.1', None)
                },
                volumes={
                    volume_name: {
                        'bind': '/wallet',
                        'mode': 'rw'
                    }
                }
            )
            return container.short_id
        except APIError as e:
            if str(e).startswith('409'):
                container = self.client.containers.get(container_name)
                return container.short_id

    def get_port(self, container_id):
        client = APIClient()
        port_data = client.port(container_id, self.listen_port)
        host_port = port_data[0]['HostPort']
        return int(host_port)

    def container_exists(self, container_id):
        try:
            self.client.containers.get(container_id)
            return True
        except NotFound:
            return False
        except NullResource:
            return False

    def volume_exists(self, volume_id):
        try:
            self.client.volumes.get(volume_id)
            return True
        except NotFound:
            return False
        except NullResource:
            return False

    def stop_container(self, container_id):
        if self.container_exists(container_id):
            c = self.client.containers.get(container_id)
            c.stop()

    def delete_wallet_data(self, user_id):
        volume_name = self.get_user_volume(user_id)
        volume = self.client.volumes.get(volume_name)
        try:
            volume.remove()
            return True
        except Exception as e:
            raise e

    @staticmethod
    def get_user_volume(user_id):
        volume_name = f'user_{user_id}_wallet'
        return volume_name

    def cleanup(self):
        users = User.query.all()
        for u in users:
            # Delete inactive wallet sessions
            if u.wallet_start:
                session_lifetime = getattr(config, 'PERMANENT_SESSION_LIFETIME', 3600)
                expiration_time = u.wallet_start + timedelta(seconds=session_lifetime)
                now = datetime.utcnow()
                # noinspection PyTypeChecker
                time_diff = expiration_time - now
                if time_diff.total_seconds() <= 0:
                    print(f'[+] Found expired container for {u}. killing it')
                    self.stop_container(u.wallet_container)
                    sleep(2)
            # Remove wallet db data if not running but it's in db
            if u.wallet_container and not self.container_exists(u.wallet_container):
                print(f'[+] Found stale data for {u}')
                u.clear_wallet_data()


docker = Docker()
