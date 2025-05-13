# Etapa base
FROM python:3.11-slim

# Evita prompts en pip y debconf
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV DJANGO_SETTINGS_MODULE=hub.settings

# Instalar dependencias del sistema necesarias para Python y Celery
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear y usar un directorio de trabajo
WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copiar todo el código
COPY . .

# Comando por defecto (puede sobrescribirse en docker-compose o run)
CMD ["gunicorn", "hub.wsgi:application", "--bind", "0.0.0.0:8000"]
