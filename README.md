# Xolon

> A web wallet for Xolentum

## Table of Contents

- [About](#about)
- [Installation](#installation)
  * [Requirements](#requirements)
  * [Setup](#setup)
- [Running](#running)
  * [Development](#development)
  * [Production](#production)
- [Maintenance](#maintenance)
- [Donations](#donations)
- [License](#license)
  

## About

Xolon is an [*open-source*](https://github.com/sohamb03/xolon), [*custodial*](https://atomicwallet.io/custodial-non-custodial-wallets-comparison) web wallet for the [***Xolentum***](https://www.xolentum.org) cryptocurrency.

It is powered by Flask, MySQL, Redis and Grafana, all within Docker containers. 

## Installation

### Requirements

The requirements for Xolon are as follows:

* `docker` and `docker-compose`
* `python3` (tested on **v3.8.5**)
* `git` and `make`
* `Nginx` (for production)

### Setup

**Do not run the web wallet as root!** Use a user without SSH access to prevent any security vulnerabilities.

```
sudo adduser xolon
sudo passwd -l xolon
sudo su - xolon
``` 

> Commands prefixed with `sudo` are to be run as a user with escalated privileges

Clone the GitHub repository:  
```
git clone https://github.com/sohamb03/xolon
```

Firstly, edit the files `.env` and `xolon/config.py` and setup the necessary configurations. Note that the database credentials in `xolon/config.py` must be the same as in`.env`.

Run the following command to setup the dependencies:
```
make setup
```

Start the backend containers:
```
make up
```

Now, initialize the databases:
```
./bin/cmd init
```

## Running

### Development

To launch the development server, use:
```
make dev
```

### Production

For production, `gunicorn` and `nginx` is recommended. Run the process as a system service using the example `xolon.service` file bundled with this repository. After editing the file to change the paths, move it to the `/etc/systemd/system` directory.

Make sure the data folder has permissions to allow both `root` and `xolon` users to access it. It is recommended to add `root` to the `xolon` user group and give the user permissions to the data folder:

```
sudo usermod -aG xolon root
sudo chown -R xolon:xolon /home/xolon/xolon/data
``` 

Start Xolon as a system service.
```
sudo systemctl daemon-reload && sudo systemctl enable xolon --now
```

Now proxy pass your FQDN (can be a sub-domain) to the UNIX socket using the sample `xolon.nginx.conf` file provided. 

Add the `nginx` user to our `xolon` user group and give the necessary permissions so as to allow Nginx to access content within the `xolon` user's home directory:

```
sudo usermod -aG xolon nginx
sudo chmod 710 /home/xolon
```

Test the Nginx configuration:

```
sudo nginx -t
```

Restart Nginx:

```
sudo systemctl restart nginx
```

## Maintenance

This application comes with built-in capabilities to regulate traffic during maintenance. When needed, the maintenance mode can be turned on with:

```
./bin/cmd maintenance enable
```

And the application will immediately switch to the maintenance mode, redirecting users to a static page until the mode is disabled with:

```
./bin/cmd maintenance disable
```

## Donations

The application itself is free to use but it's development and maintenance are not. If you find the application useful, please consider donating to the [Xolentum Development Fund](https://www.xolentum.org/community/funding/).

#### Xolentum

Address: `Xwmjr3jep6H6FBzLJjkj7v59qJQqLJyK5K67hiJPnJ1hVsvDUr4LPDXYFoPhBXMMoDJK4i27UdvAAhHShuxaY96r1NuL4n5jF`

View Key: `4cf37fb01f76badcc998a0de1388677f95b9e0a33a57f0d6de626334ebbb2bfb`

#### BitCoin

Address: `1DyqVvN4KR5Rxdf3zGpA6gRBHsN5uR29nf`

#### Monero

Address: `49EPmSiHM9ibXxdgNmPFeKcoqjY1WKMtx4BGLGXREXZ2CzYsXDjfVfuRZivR3kGFqWAELbJJwrmia2qsGvScZZFkHZLE5Ef`

View Key: `b2666a4868005092dc1369f4fe33bd372ead8fec4b56830b0409bb6046b16792`

## License

[BSD-3-Clause License](LICENSE)

Copyright &copy; 2021 Sayan Bhattacharyya, The Xolentum Project