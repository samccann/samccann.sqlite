.PHONY: help install test lint format security clean

help:  ## Display this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install development dependencies
	pip install -r test-requirements.txt
	pip install pre-commit
	pre-commit install

test:  ## Run all tests
	tox

test-fast:  ## Run tests without Docker
	pytest tests/unit/

lint:  ## Run linting checks
	tox -e lint
	tox -e ansible-lint

format:  ## Format code
	black plugins/
	isort plugins/

security:  ## Run security scans
	bandit -r plugins/
	safety check

clean:  ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -name "*.db" -delete
	find . -name "*.sqlite" -delete
	find . -name "*.sqlite3" -delete

build:  ## Build collection
	ansible-galaxy collection build

install-local:  ## Install collection locally
	ansible-galaxy collection install *.tar.gz --force

docs:  ## Generate documentation
	@echo "Documentation available in README.md and docs/"

ci-test:  ## Run tests as in CI
	tox -e ansible-test-sanity
	tox -e ansible-test-units

integration-test:  ## Run integration tests
	tox -e ansible-test-integration

changelog:  ## Generate changelog
	antsibull-changelog generate

release:  ## Prepare release (build + changelog)
	$(MAKE) changelog
	$(MAKE) build
