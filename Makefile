VENV_PATH = .venv

ifeq ($(OS), Windows_NT)
    # Windows
	SHELL = cmd.exe
    PYTHON := $(if $(wildcard $(VENV_PATH)/Scripts/python.exe), \
                $(VENV_PATH)/Scripts/python.exe, \
                python)
else
    # Linux / Mac
    PYTHON := $(if $(wildcard $(VENV_PATH)/bin/python), \
                $(VENV_PATH)/bin/python, \
                python)
endif

install-requirements:
	$(PYTHON) -m pip install -r ./app/requirements.txt

black:
	$(PYTHON) -m black -l 120 -S ./app ./tests

isort:
	$(PYTHON) -m isort -l 120 --profile black ./app ./tests

autoflake:
	$(PYTHON) -m autoflake --in-place --remove-all-unused-imports --remove-unused-variables --expand-star-imports --recursive ./app ./tests

check-black:
	$(PYTHON) -m black --check --diff -l 120 -S ./app ./tests

check-isort:
	$(PYTHON) -m isort -l 120 --profile black ./app ./tests -c

check-flake8:
	$(PYTHON) -m flake8 --ignore=W503,E711,E712,W291,E704 --max-line-length=120 ./app ./tests

pytest:
	$(PYTHON) -m pytest ./tests

module_map:
	$(PYTHON) ./scripts/generate_module_map.py app

lint: autoflake isort black

check: check-black check-isort check-flake8
