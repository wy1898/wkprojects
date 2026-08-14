PYTHON ?= python3
PYTHONPATH := src

.PHONY: help install web start check test report

help:
	@echo "Linux Server Acceptance Platform"
	@echo ""
	@echo "Available commands:"
	@echo "  make install  Install Python dependencies from requirements.txt"
	@echo "  make web      Start the Flask WebUI on http://127.0.0.1:8000"
	@echo "  make start    Check Python, set PYTHONPATH, and start WebUI"
	@echo "  make check    Run server-check inventory"
	@echo "  make test     Run the pytest suite"
	@echo "  make report   Generate a demo acceptance report"

install:
	$(PYTHON) -m pip install -r requirements.txt

web:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m server_acceptance.web

start:
	@command -v $(PYTHON) >/dev/null 2>&1 || (echo "Python executable not found: $(PYTHON)" && exit 1)
	@$(PYTHON) --version
	@echo "Starting Linux服务器验收平台 at http://127.0.0.1:8000"
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m server_acceptance.web

check:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m server_acceptance inventory

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q

report:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m server_acceptance validate --profile demo --output reports/latest.json
