all: init

init:
	pip install -r test_requirements.txt
	pip install -r requirements.txt

.PHONY: lint
lint:
	@isort --atomic --skip pb --skip .venv .
	@flake8 --config ./.flake8 .

.PHONY: unit-test
unit-test: lint
	@echo "----- Running tests -----"
	python -m unittest discover tests "*_tests.py"

.PHONY: testcov
testcov:
	@echo "----- Running tests with coverage -----"
	@coverage run --source=harvester -m unittest discover tests "*_tests.py"
	@coverage xml
	@coverage report
