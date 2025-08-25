clean: ## Clean up cache and temporary files
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

# ==============================================================================
# Define dependencies
# ==============================================================================
MEETX_APP       := raven
BASE_IMAGE_NAME := insidious000
# VERSION         := 0.1.1
VERSION         := $(shell poetry version -s)
API_IMAGE       := $(BASE_IMAGE_NAME)/$(MEETX_APP):$(VERSION)

# ==============================================================================
# General Commands
# ==============================================================================

init:
	poetry new $(MEETX_APP)

track-tree:
	poetry show --tree

track-latest:
	poetry show --latest

install:
	poetry add $(cat requirements.txt)

update:
	poetry update package

dev-install:
	poetry add --dev ruff

run:
	lsof -i :8000 | awk 'NR!=1 {print $$2}' | xargs -r kill -9
	poetry run python3 app/main.py

# Use this when package is removed
lock:
	poetry lock

ruff: ## Run ruff check (use 'make lint-fix' to auto-fix)
	poetry run ruff check .

# ==============================================================================
# Versioning
# ==============================================================================

version:
	@if [ -z "$(SEMVER)" ]; then \
		poetry version; \
	else \
		poetry version $(SEMVER); \
	fi

version-help:
	@echo "Usage: make version SEMVER=<bump_type>"
	@echo ""
	@echo "Available bump types:"
	@echo "  show         Show current version"
	@echo "  patch        Bump patch version (0.0.X)"
	@echo "  minor        Bump minor version (0.X.0)"
	@echo "  major        Bump major version (X.0.0)"
	@echo "  preminor     Bump preminor version (0.X.0a0)"
	@echo "  premajor     Bump premajor version (X.0.0a0)"
	@echo "  prerelease   Bump prerelease version (0.0.0aX)"

print-version:
	@echo $(VERSION)

# make version SEMVER=x.x.x

# ==============================================================================
# Development Commands
# ==============================================================================

migrate:
	poetry run alembic revision --autogenerate -m "$(msg)"
	poetry run alembic upgrade head

migrate-generate: ## Generate a new migration file
	@if [ -z "$(msg)" ]; then \
		echo "Usage: make migrate-generate msg='your migration message'"; \
		exit 1; \
	fi
	poetry run alembic revision --autogenerate -m "$(msg)"

migrate-up: ## Run database migrations
	poetry run alembic upgrade head

migrate-down: ## Rollback last migration
	poetry run alembic downgrade -1

migrate-status: ## Show migration status
	poetry run alembic current

migrate-history: ## Show migration history
	poetry run alembic history

migrate-reset: ## Reset database (WARNING: This will delete all data!)
	@echo "WARNING: This will delete all data in the database!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	poetry run alembic downgrade base
	poetry run alembic upgrade head

prettier: lint-fix format

lint-fix: ## Run linting with auto-fix
	poetry run ruff check --fix .

format: ## Format code
	poetry run ruff format .

# ==============================================================================
# Docker TBD
# ==============================================================================

VOSK_LANGUAGE := en
VOSK_NAME     := vosk
VOSK_IMAGE    := alphacep/kaldi-$(VOSK_LANGUAGE)

vosk-en:
	docker run -d \
		--name $(VOSK_NAME)-$(VOSK_LANGUAGE) \
		-p 2700:2700 \
		--network meetx \
		$(VOSK_IMAGE)


docker-push:
	docker login

	docker build \
		--platform=linux/amd64 \
		-f zarf/docker/dockerfile.api \
		-t $(API_IMAGE) \
		--build-arg BUILD_REF=$(VERSION) \
		--build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
		.
	docker push insidious000/meetx:$(VERSION)
	
	docker build \
		--platform=linux/amd64 \
		-f zarf/docker/dockerfile.api \
		-t $(API_IMAGE) \
		-t $(BASE_IMAGE_NAME)/$(MEETX_APP):latest \
		--build-arg BUILD_REF=$(VERSION) \
		--build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
		.

	docker push insidious000/meetx:latest

compose:
	docker compose \
		--env-file .env \
		-p noura \
		-f zarf/compose/docker_compose.yaml \
		up -d

composervice:
	docker compose \
		--env-file .env \
		-p noura \
		-f zarf/compose/docker_compose.yaml \
		up -d --no-deps --build $(service)

network-ls:
	docker network ls

network-create:
	docker network create --driver bridge $(network)

network-prune:
	docker network prune

network:
	docker network inspect meetx

accessdb:
	docker exec -it postgres psql -U postgres


# test: ## Run tests
# 	poetry run pytest -v

# test-cov: ## Run tests with coverage
# 	poetry run pytest --cov=app --cov-report=html --cov-report=term-missing

# test-coverage: ## Run tests with coverage and generate HTML report
# 	poetry run pytest --cov=app.routers.users --cov-report=html tests/user/

# test-user: ## Run only user tests
# 	poetry run pytest -v tests/user/

# test-user-cov: ## Run user tests with coverage
# 	poetry run pytest --cov=app.routers.users --cov-report=html --cov-report=term-missing tests/user/

# test-specific: ## Run specific test file (usage: make test-specific FILE=tests/user/test_create_user.py)
# 	poetry run pytest -v $(FILE)

# test-create-user: ## Run create user tests specifically
# 	poetry run pytest -v tests/user/test_create_user.py

# test-create-user-cov: ## Run create user tests with coverage
# 	poetry run pytest --cov=app.routers.users --cov-report=html tests/user/test_create_user.py

# docs: ## Open Swagger documentation in browser
# 	@echo "Checking if server is running on port 8000..."
# 	@if lsof -i :8000 > /dev/null 2>&1; then \
# 		echo "Server is running. Opening Swagger docs..."; \
# 		open http://localhost:8000/docs; \
# 	else \
# 		echo "Server is not running on port 8000."; \
# 		echo "Please start the server first with: make dev"; \
# 		echo "Then run: make docs"; \
# 	fi






# migrate: ## Generate a new migration
# 	poetry run alembic revision --autogenerate -m "$(message)"



# init-db: ## Initialize database with first migration
# 	poetry run alembic revision --autogenerate -m "Initial migration"
# 	poetry run alembic upgrade head



# docker-build: ## Build Docker image
# 	docker-compose build

# docker-up: ## Start services with Docker Compose
# 	docker-compose up -d

# docker-down: ## Stop Docker services
# 	docker-compose down

# docker-logs: ## View Docker logs
# 	docker-compose logs -f

# pre-commit: ## Install pre-commit hooks
# 	poetry run pre-commit install

# check: lint type-check test ## Run all checks (lint, type-check, test)

# # Development workflow
# setup: install pre-commit ## Initial project setup
# 	@echo "Project setup complete! Run 'make dev' to start the development server."

# # Production commands
# build: clean lint type-check test ## Build for production
# 	@echo "Build successful!"

# # Database performance commands
# db-analyze: ## Analyze database performance
# 	poetry run python -m scripts.db_performance analyze

# db-benchmark: ## Benchmark database queries
# 	poetry run python -m scripts.db_performance benchmark

# db-stats: ## Update database statistics
# 	poetry run python -m scripts.db_performance update-stats

# db-performance: ## Run full database performance analysis
# 	poetry run python -m scripts.db_performance full


# docker-build:
# 	docker build \
# 		--platform=linux/amd64 \
# 		-f zarf/docker/dockerfile.meetx \
# 		-t $(API_IMAGE) \
# 		--build-arg BUILD_REF=$(VERSION) \
# 		--build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
# 		.

# docker-run:
# 	docker run -d \
# 		--platform=linux/amd64 \
# 		--name $(MEETX_APP) \
# 		-p 8000:8000 \
# 		$(API_IMAGE)

# poetry run ruff check . --preview

ollama:
	lsof -i :11434 | awk 'NR!=1 {print $$2}' | xargs -r kill -9
	ollama serve