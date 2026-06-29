# Convenience targets for the ChatGPT Health triage evaluation.
# Override the interpreter if needed, e.g.:  make run PYTHON=/opt/anaconda3/bin/python3

PYTHON ?= python3
OUTPUT ?= results

.PHONY: help run test venv clean

help:
	@echo "make run    - reproduce workbook + figures into $(OUTPUT)/"
	@echo "make test   - reproduce into build/test_run/ (leaves results/ untouched)"
	@echo "make venv   - create .venv and install dependencies"
	@echo "make clean  - remove build/ and __pycache__"
	@echo ""
	@echo "Override the interpreter:  make run PYTHON=/opt/anaconda3/bin/python3"

run:
	$(PYTHON) code/run_all.py --output $(OUTPUT)

test:
	$(PYTHON) code/run_all.py --output build/test_run
	@echo "Wrote build/test_run/ — compare against results/ without overwriting it."

venv:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt
	@echo "Done. Activate with: source .venv/bin/activate"

clean:
	rm -rf build .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
