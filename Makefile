.PHONY: help runserver migrate makemigrations shell test lint format coverage check

help:
	@echo "Comandos disponibles:"
	@echo "  runserver         - Levanta el servidor local (localhost:8000)"
	@echo "  migrate           - Aplica migraciones"
	@echo "  makemigrations    - Crea nuevas migraciones"
	@echo "  shell             - Abre el shell de Django"
	@echo "  test              - Corre los tests con coverage"
	@echo "  lint              - Corre black, isort y flake8"
	@echo "  format            - Formatea el código (black + isort)"
	@echo "  coverage          - Genera reporte HTML de cobertura"
	@echo "  check             - Corre linting + tests + coverage"

runserver:
	python manage.py runserver

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

shell:
	python manage.py shell

test:
	coverage run -m pytest
	coverage report -m

lint:
	black --check . --exclude 'env|migrations'
	isort --check-only . --skip env
	flake8 . --exclude=env,migrations,__pycache__

format:
	black .
	isort .

coverage:
	coverage html
	@echo "Abrí htmlcov/index.html en tu navegador para ver el reporte."

# ✅ Comando todo-en-uno
check: lint test
	coverage
	@echo "Todo en uno: linting + tests + coverage"
	@echo "Si todo salió bien, no hay errores."
	@echo "Si hubo errores, revisá los mensajes anteriores para más detalles."
	@echo "Si no hay errores, ¡felicitaciones! Todo está en orden."
