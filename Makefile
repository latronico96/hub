.PHONY: help run runserver migrate makemigrations shell \
        test lint format coverage check install links updatedependences resetdb cleandb \
        typecheck createsuperuser uninstall-dev

.DEFAULT_GOAL := help

help:
	@echo "Comandos disponibles:"
	@echo "  run               - Levanta servidor, worker y Redis"
	@echo "  runserver         - Levanta solo el servidor Django"
	@echo "  migrate           - Aplica migraciones"
	@echo "  makemigrations    - Crea nuevas migraciones"
	@echo "  shell             - Abre shell interactivo de Django"
	@echo "  test              - Ejecuta tests con coverage"
	@echo "  lint              - Verifica estilo y calidad de código"
	@echo "  format            - Formatea código automáticamente"
	@echo "  coverage          - Genera reporte HTML de cobertura"
	@echo "  check             - Ejecuta verificación completa (lint + test)"
	@echo "  install           - Instala dependencias"
	@echo "  links             - Muestra URLs disponibles"
	@echo "  updatedependences - Actualiza requirements.txt"
	@echo "  resetdb           - Reinicia base de datos completamente"
	@echo "  cleandb           - Limpia datos pero mantiene estructura"
	@echo "  typecheck         - Verificación estática de tipos"
	@echo "  createsuperuser   - Crea usuario administrador"
	@echo "  envtest"
	@echo "  envprod"
	@echo "  envdebug"
	@echo "  uninstall-dev     - Desinstala paquetes de desarrollo"

install:
	pip install -r requirements.txt
	pip install pytest pytest-cov black isort flake8 mypy pylint django-extensions

run: runserver

runserver:
	python manage.py runserver
	
migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

shell:
	python manage.py shell

test:
	pytest --cov=hub --cov=recetario --cov=tests --cov=users --cov-report=term-missing --no-cov-on-fail

lint:
	@echo ">>> Verificando orden de imports (isort)..."
	isort --check-only . --skip env
	@echo ">>> Verificando formato (black)..."
	black --check . --exclude 'env|migrations'
	@echo ">>> Verificando estilo (flake8)..."
	flake8 .
	@echo ">>> Verificando calidad (pylint)..."
	DJANGO_SETTINGS_MODULE=hub.settings pylint --rcfile=.pylintrc hub/ recetario/ tests/ users/

format:
	isort . --skip env
	black . --exclude 'env|migrations'

coverage:
	pytest --cov=hub --cov=recetario --cov=tests --cov=users --cov-report=html
	@echo "Abre htmlcov/index.html en tu navegador para ver el reporte."

check: lint test
	@echo "Verificación completa completada."

links:
	python manage.py show_urls

updatedependences:
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

createsuperuser:
	@echo "Creando superusuario..."
	@python manage.py createsuperuser --email test@admin.com --username admin || \
	(python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(email='test@admin.com', username='admin', password='admin')" && \
	echo "Superusuario creado: email=test@admin.com, password=admin")

envtest:
	@echo "Seteando entorno de TEST..."
	@ENVIRONMENT=test RUNNING_TESTS=1 DJANGO_SETTINGS_MODULE=hub.settings  powershell

envprod:
	@echo "Seteando entorno de PRODUCCIÓN..."
	@ENVIRONMENT=production DJANGO_SETTINGS_MODULE=hub.settings powershell

envdebug:
	@echo "Seteando entorno de DESARROLLO (debug)..."
	@ENVIRONMENT=development DJANGO_SETTINGS_MODULE=hub.settings powershell

uninstall-dev:
	pip uninstall -y black flake8 isort mypy mypy-extensions django-stubs django-stubs-ext \
	djangorestframework-stubs pylint pylint-django pylint-plugin-utils types-PyYAML \
	types-requests pytest pytest-cov pytest-django pytest-env coverage django-extensions \
	iniconfig pathspec platformdirs pluggy pycodestyle pyflakes tomlkit wcwidth