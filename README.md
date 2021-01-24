# Xolon

> A web wallet for Xolentum

## About

Xolon is an *open-source*, [*custodial*](https://atomicwallet.io/custodial-non-custodial-wallets-comparison) web wallet for the [***Xolentum***](https://www.xolentum.org) cryptocurrency.

It is powered by Flask, MariaDB, Redis and Grafana, all within Docker containers. 

## Installation

### Requirements

The requirements for Xolon are as follows:

* `docker` and `docker-compose`
* `python3` (tested on **v3.8.5**)
* `make`

### Setup

First edit the files `.env` and `xolon/config.py` and setup the necessary configurations. Note that the database credentials in `xolon/config.py` must be the same as in`.env`.

Clone the GitHub repository:  
```
git clone https://github.com/sohamb03/xolon
```

Run the following command to setup the dependencies:
```
make setup
```

Initialie the backend containers:
```
make up
```

Now, initialize the databases:
```
./bin/cmd init
```

### Running

Launch the development server:
```
make dev
```

For production, `gunicorn` and `nginx` is used. Run the process as a system service using the example `xolon.service` file bundled with this repository. After editing the file to match the paths, move it to the `/etc/systemd/system` directory.

Start Xolon service.
```
systemctl daemon-reload && systemctl enable xolon --now
```

Now proxy pass your FQDN (can be a sub-domain) to the UNIX socket using the sample `nginx.conf` file provided. 

## License

[BSD-3-Clause License](LICENSE)

Copyright &copy; 2021 Sayan Bhattacharyya, The Xolentum Project