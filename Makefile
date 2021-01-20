.PHONY: format help

# Help system from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup Python virtual environment
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

up: ## Bring up backend containers
	docker-compose up -d

down: ## Bring down backend containers
	docker-compose down

dev: ## Start development server
	./bin/dev

dbinit: ## Initialize database schema
	./bin/dbinit

dbshell: ## Start interactive session with database
	docker-compose exec db psql -U xolon