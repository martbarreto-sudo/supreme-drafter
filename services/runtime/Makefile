# NEXUM TIER 0 — atalhos de desenvolvimento local.

.PHONY: up down logs test test-integration psql

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f

# Testes unitarios (fakes, sem infra): deseleciona os de integracao.
test:
	cd $(CURDIR) && python3 -m pytest nexum -q -m "not integration"

# Testes de integracao (requer `make up`).
test-integration:
	python3 -m pytest nexum -q -m integration

psql:
	docker compose exec postgres psql -U nexum -d nexum
