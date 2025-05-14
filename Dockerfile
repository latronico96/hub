# Etapa base
FROM python:3.13-alpine

# Evita prompts en pip y debconf
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV DJANGO_SETTINGS_MODULE=hub.settings

# Instalar dependencias del sistema necesarias para Python y Celery
RUN apk update && apk add --no-cache \
    build-base \
    postgresql-dev \
    curl

# Crear y usar un directorio de trabajo
WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install gunicorn \
    && pip install -r requirements.txt

# Copiar todo el código
COPY . .

# Comando por defecto (puede sobrescribirse en docker-compose o run)
CMD ["gunicorn", "hub.wsgi:application", "--bind", "0.0.0.0:8000"]
