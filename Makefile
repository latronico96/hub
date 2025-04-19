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
	@echo "  links             - Muestra las URLs disponibles en el proyecto"
	@echo "  updateDependences - Actualiza el archivo requirements.txt con las dependencias actuales"
	@echo "  resetdb           - Reinicia la base de datos (elimina todo)"
	@echo "  cleandb           - Limpia la base de datos (elimina todos los datos)"
	@echo "  help              - Muestra este mensaje de ayuda"

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
	black . --exclude 'env|migrations'
	isort . --skip env

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
	python manage.py flush

