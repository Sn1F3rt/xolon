# wowstash

A web wallet for noobs who can't use a CLI.

## Setup

```
# Create new database secrets
cp env-example .env
vim .env

# Setup app secrets
cp wowstash/config.{example.py,py}
vim wowstash/config.py

# Run db (postgres) and cache (redis) containers
docker-compose up -d
```
