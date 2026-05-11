SHELL := /bin/bash

PY := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

.PHONY: help install install-py install-web test lint typecheck dev server web clean smoke seed

help:
	@echo "HypoKiln development tasks"
	@echo ""
	@echo "  make install        — Python + Node deps"
	@echo "  make test           — pytest unit tests"
	@echo "  make typecheck      — TypeScript typecheck on web/"
	@echo "  make dev            — FastAPI :8765 + Next.js :3000 in parallel"
	@echo "  make server         — FastAPI control plane only"
	@echo "  make web            — Next.js dashboard only"
	@echo "  make smoke          — dry-run the pipeline end-to-end"
	@echo "  make seed           — seed demo data for the UI"
	@echo "  make clean          — wipe state + venv + node_modules"

install: install-py install-web

install-py:
	$(PY) -m venv $(VENV)
	$(PIP) install -e ".[dev,control]"

install-web:
	cd web && npm install

test:
	HYPOKILN_SKIP_SKILLS=1 $(PYTEST) tests/ -v

lint:
	$(VENV)/bin/ruff check hypokiln/ tests/ control/

typecheck:
	cd web && npm run typecheck

dev:
	@trap 'kill %1 %2 2>/dev/null; exit' INT; \
	$(MAKE) server & \
	$(MAKE) web & \
	wait

server:
	$(VENV)/bin/uvicorn control.main:app --reload --port 8765

web:
	cd web && npm run dev

smoke:
	$(VENV)/bin/kiln build "Dry run smoke test" --slug smoke --yolo --dry-run || true
	$(VENV)/bin/kiln status

seed:
	$(VENV)/bin/python scripts/seed_demo.py

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache web/node_modules web/.next
	@echo "Note: .hypokiln/state/ and products/ are NOT removed automatically."
	@echo "Run 'rm -rf .hypokiln products' if you want a full reset."
