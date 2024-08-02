.PHONY: init
init:
	python3 -m virtualenv .venv
	source .venv/bin/activate
	pip install -r requirements.txt

.PHONY: test
test:
	pytest

.PHONY: check
check:
	python setup.py check

.PHONY: ruff
ruff:
	ruff check .
	ruff format --check .

.PHONY: mypy
mypy:
	mypy .

.PHONY: coverage
coverage:
	pytest --verbose --cov-report term --cov-report html --cov=django_sam tests

.PHONY: publish
publish:
	pip install twine build
	python -m build
	# twine upload dist/*
	rm -rf build dist .egg django_sam.egg-info
