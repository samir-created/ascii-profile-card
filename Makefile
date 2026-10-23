# Build your card locally. Just run:  make
# It sets itself up on first run, redoes only what changed, and opens the cards.
# `make help` lists the other commands.

VENV := .venv
PYTHON := $(VENV)/bin/python
OPEN := $(if $(filter Darwin,$(shell uname -s)),open,xdg-open)
# Python for a new .venv: 3.12 matches the GitHub Action; fall back to whatever python3 is
BASE_PYTHON := $(or $(shell command -v python3.12 2>/dev/null),python3)
PHOTO := $(firstword $(wildcard photo.jpg photo.jpeg photo.png photo.webp))
STATE := .cache

.DEFAULT_GOAL := all
.PHONY: all help portrait build preview gallery test reset clean

all: $(STATE)/built ## Set up if needed, rebuild what changed, open the cards
	$(OPEN) dark_mode.svg
	$(OPEN) light_mode.svg

help: ## Show these commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

# --- setup, done automatically and only when the requirements change ---------------------

$(STATE)/deps: requirements.txt
	@test -x $(PYTHON) || $(BASE_PYTHON) -m venv $(VENV)
	$(PYTHON) -m pip install -q --upgrade pip
	$(PYTHON) -m pip install -q -r requirements.txt
	@mkdir -p $(STATE) && touch $@

$(STATE)/photo-deps: requirements-photo.txt | $(STATE)/deps
	$(PYTHON) -m pip install -q -r requirements-photo.txt
	@touch $@

# --- portrait: redone only when the photo or the portrait settings change ------------------
# (so hand edits to ascii.txt survive until you change one of those)

$(STATE)/portrait-settings: config.yml | $(STATE)/deps
	@$(PYTHON) -c "import yaml, json; print(json.dumps((yaml.safe_load(open('config.yml')) or {}).get('portrait'), sort_keys=True))" > $@.new
	@cmp -s $@.new $@ && rm $@.new || mv $@.new $@

ifneq ($(PHOTO),)
ascii.txt: $(PHOTO) $(STATE)/portrait-settings card/portrait.py | $(STATE)/photo-deps
	$(PYTHON) -m card.portrait
endif

# --- cards: rebuilt when the config, portrait or code change -------------------------------

$(STATE)/built: config.yml ascii.txt $(wildcard card/*.py) | $(STATE)/deps
	$(PYTHON) -m card.build
	@touch $@

# --- explicit commands ---------------------------------------------------------------------

portrait: | $(STATE)/photo-deps ## Redo the portrait from the photo now
	$(PYTHON) -m card.portrait

build: | $(STATE)/deps ## Rebuild the cards now
	$(PYTHON) -m card.build

preview: all ## Same as plain `make`

gallery: | $(STATE)/deps ## Render every style option into examples/
	$(PYTHON) -m card.gallery

test: | $(STATE)/deps ## Run the tests
	$(PYTHON) -m unittest discover -s tests

reset: ## Start over: delete .venv and the build state
	rm -rf $(VENV) $(STATE)

clean: ## Remove Python caches
	find . -path ./$(VENV) -prune -o -name __pycache__ -prune -exec rm -rf {} +
