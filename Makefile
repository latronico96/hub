.PHONY: help runserver migrate makemigrations shell test lint format coverage check install \
        links updateDependences resetdb cleandb typecheck

help:
	@echo "Comandos disponibles:"
	@echo "  runserver          - Levanta el servidor local (localhost:8000)"
	@echo "  migrate            - Aplica migraciones"
	@echo "  makemigrations     - Crea nuevas migraciones"
	@echo "  shell              - Abre el shell de Django"
	@echo "  test               - Corre los tests con coverage"
	@echo "  lint               - Corre black, isort, flake8, pylint y mypy"
	@echo "  format             - Formatea el código (black + isort)"
	@echo "  coverage           - Genera reporte HTML de cobertura"
	@echo "  check              - Corre linting + tests + coverage"
	@echo "  links              - Muestra las URLs disponibles en el proyecto"
	@echo "  updateDependences  - Actualiza el archivo requirements.txt con las dependencias actuales"
	@echo "  resetdb            - Reinicia la base de datos (elimina todo)"
	@echo "  cleandb            - Limpia la base de datos (elimina todos los datos)"
	@echo "  typecheck          - Corre mypy para chequeo de tipos"
	@echo "  install            - Instala las dependencias requeridas"
	@echo "  help               - Muestra este mensaje de ayuda"

install:
	pip install -r requirements.txt
	pip install pytest pytest-cov black isort flake8 mypy pylint django-extensions

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
	@echo ">>> Ejecutando isort..."
	isort --check-only . --skip env || echo "Isort encontró problemas de orden."
	@echo ">>> Ejecutando black..."
	black --check . --exclude 'env|migrations' || echo "Black encontró problemas de formato."
	@echo ">>> Ejecutando flake8..."
	flake8 . || echo "Flake8 encontró problemas de estilo."
	@echo ">>> Ejecutando pylint..."
	pylint --rcfile=.pylintrc hub/ recetario/ tests/ users/ core/ || true
	@echo ">>> Ejecutando mypy..."
	mypy . || true

format:
	isort . --skip env
	black . --exclude 'env|migrations'

coverage:
	coverage html
	@echo "Abrí htmlcov/index.html en tu navegador para ver el reporte."

check: lint test coverage
	@echo "Todo en uno: linting + tests + coverage"
	@echo "Si todo salió bien, no hay errores."
	@echo "Si hubo errores, revisá los mensajes anteriores para más detalles."
	@echo "Si no hay errores, ¡felicitaciones! Todo está en orden."

links:
	python manage.py show_urls

updateDependences:
	pip freeze > requirements.txt

resetdb:
	rm -f db.sqlite3
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "*/migrations/*.pyc" -delete
	python manage.py makemigrations
	python manage.py migrate

cleandb:
	python manage.py flush --no-input

typecheck:
	mypy .
