PYTHON ?= python3
UVICORN ?= uvicorn
APP_MODULE ?= app.main:app

.PHONY: install run test bootstrap-vault clone-vault rebuild-site lint-wiki pull-vault commit-vault push-vault

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(UVICORN) $(APP_MODULE) --host 0.0.0.0 --port 8000 --reload

test:
	$(PYTHON) -m pytest -q

bootstrap-vault:
	./scripts/bootstrap_vault.sh

clone-vault:
	./scripts/clone_vault.sh

rebuild-site:
	./scripts/rebuild_site.sh

lint-wiki:
	./scripts/lint_wiki.sh

pull-vault:
	@if [ ! -d wiki_vault/.git ]; then echo "wiki_vault is not a git repo"; exit 1; fi
	cd wiki_vault && git pull --ff-only

commit-vault:
	@if [ ! -d wiki_vault/.git ]; then echo "wiki_vault is not a git repo"; exit 1; fi
	@if [ -z "$(m)" ]; then echo "Usage: make commit-vault m='message'"; exit 1; fi
	cd wiki_vault && git add . && git commit -m "$(m)"

push-vault:
	@if [ ! -d wiki_vault/.git ]; then echo "wiki_vault is not a git repo"; exit 1; fi
	cd wiki_vault && git push
