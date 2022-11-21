.PHONY: build deploy lint test run_api run_worker

DIR:=$(strip $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST)))))

build:
	@$(DIR)/scripts/build

deploy:
	@$(DIR)/scripts/deploy

lint:
	@$(DIR)/scripts/lint

test:
	@$(DIR)/scripts/test

run_api:
	@$(DIR)/scripts/run_api

run_worker:
	@$(DIR)/scripts/run_worker
