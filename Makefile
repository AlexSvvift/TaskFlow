.PHONY: install run test

install:
	python -m pip install -r requirements.txt

run:
	python run.py

test:
	python -m pytest
