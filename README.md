# Xolon

Web wallet for Xolentum.

## Setup

```
# Create new database secrets
cp env-example .env
vim .env

# Setup app secrets
cp xolon/config.{example.py,py}
vim xolon/config.py

# Run db (postgres) and cache (redis) containers
docker-compose up -d
```
