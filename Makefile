# -*- coding: utf-8 -*-
# :Project:   LasaurApp -- Makefile
# :Created:   sab 11 giu 2016 21:32:51 CEST
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2016 Stefan Hechenberger <stefan@nortd.com> and others,
#             see AUTHORS.txt
#

export TOPDIR := $(CURDIR)
export VENVDIR := $(TOPDIR)/env
export PYTHON := $(VENVDIR)/bin/python
export SHELL := /bin/bash
export SYS_PYTHON := $(shell which python3)

ACTIVATE_SCRIPT := $(VENVDIR)/bin/activate
PIP := $(VENVDIR)/bin/pip
REQUIREMENTS_TIMESTAMP := $(VENVDIR)/requirements.timestamp
REQUIREMENTS := requirements.txt
DOCS_REQUIREMENTS_TIMESTAMP := $(VENVDIR)/docs-requirements.timestamp
DOCS_REQUIREMENTS := docs-requirements.txt
REPO := $(shell git config --get remote.origin.url)

.PHONY: all
all: virtualenv

help::
	@echo
	@echo "Python virtualenv related targets"
	@echo "================================="
	@echo

help::
	@echo -e "virtualenv\n\tsetup the Python virtualenv and install required packages"

.PHONY: virtualenv
virtualenv: $(VENVDIR) requirements

$(VENVDIR):
	@echo "Bootstrapping Python 3 virtualenv..."
	@$(SYS_PYTHON) -m venv $@
	@sed --in-place \
		 --expression='s/"x(env) " != x/"x($(notdir $(TOPDIR))) " != x/' \
		 --expression='s/PS1="(env) \$$PS1"/PS1="($(notdir $(TOPDIR))) $$PS1"/' \
		 $(ACTIVATE_SCRIPT)
	@$(MAKE) upgrade-pip

help::
	@echo -e "upgrade-pip\n\tupgrade pip"

.PHONY: upgrade-pip
upgrade-pip:
	@echo "Upgrading pip..."
	@$(PIP) install --upgrade pip

help::
	@echo -e "requirements\n\tinstall/update required Python packages"

.PHONY: requirements
requirements: $(REQUIREMENTS_TIMESTAMP)

$(REQUIREMENTS_TIMESTAMP): requirements.txt
	@if expr "$(shell $(PIP) --version)" : "pip 1.*" > /dev/null; then $(MAKE) upgrade-pip; fi
	@echo "Installing pre-requirements..."
	@PATH=$(TOPDIR)/bin:$(PATH) $(PIP) install -r $(REQUIREMENTS) | grep --line-buffered -v '^   '
	@touch $@

help::
	@echo -e "docs-requirements\n\tinstall/update required Python packages"

.PHONY: docs-requirements
docs-requirements: $(DOCS_REQUIREMENTS_TIMESTAMP)

$(DOCS_REQUIREMENTS_TIMESTAMP): requirements.txt
	@echo "Installing docs requirements..."
	@PATH=$(TOPDIR)/bin:$(PATH) $(PIP) install -r $(DOCS_REQUIREMENTS) | grep --line-buffered -v '^   '
	@touch $@

help::
	@echo -e "docs\n\t compile documentation"

.PHONY: docs
docs: $(DOCS_REQUIREMENTS_TIMESTAMP)
	@echo "Compiling documentation..."
	@source $(VENVDIR)/bin/activate && cd docs &&  $(MAKE) html
	@$(PYTHON) -m webbrowser $(TOPDIR)/docs/_build/html/index.html

help::
	@echo -e "push-docs\n\t push documentation to gh-pages"

.PHONY: push-docs
.ONESHELL:
push-docs: docs
	@echo "Pushing docs to gh-pages branch"
	cd docs/_build/html
	touch .nojekyll
	git init
	git add .
	git commit -m "Deployed to Github Pages"
	git push --force --quiet $(REPO) master:gh-pages
