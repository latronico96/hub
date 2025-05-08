.PHONY: help run runserver runworker startredis stopredis migrate makemigrations shell \
        test lint format coverage check install links updatedependences resetdb cleandb \
        typecheck createsuperuser

.DEFAULT_GOAL := help

help:
	@echo "Comandos disponibles:"
	@echo "  run               - Levanta servidor, worker y Redis"
	@echo "  runserver         - Levanta solo el servidor Django"
	@echo "  runworker         - Levanta solo el worker de Celery"
	@echo "  runflower         - Levanta solo el mangement de flower"
	@echo "  startredis        - Inicia contenedor Redis"
	@echo "  stopredis         - Detiene y elimina contenedor Redis"
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

install:
	pip install -r requirements.txt
	pip install pytest pytest-cov black isort flake8 mypy pylint django-extensions

run: startredis runserver runworker

runserver:
	python manage.py runserver

startredis:
	@echo "Deteniendo Redis si está corriendo..."
	-docker stop redis
	@echo "Eliminando contenedor si existe..."
	-docker rm redis
	@echo "Iniciando Redis..."
	docker run -d -p 6379:6379 --name redis redis:7.0

stopredis:
	@echo "Deteniendo Redis..."
	-docker stop redis
	@echo "Eliminando contenedor..."
	-docker rm redis

runworker:
	python -m celery -A hub worker --loglevel=info --pool=solo

runflower:
	python -m celery -A hub --broker=redis://localhost:6379/0 flower --port=5555
	
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
	pylint --rcfile=.pylintrc hub/ recetario/ tests/ users/

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