FROM python:3.13-alpine

ARG ENVIRONMENT=production
ENV ENVIRONMENT=${ENVIRONMENT}
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=hub.settings

RUN apk update && apk add --no-cache \
    build-base \
    postgresql-dev \
    curl

WORKDIR /app

COPY requirements.txt .
COPY requirements-dev.txt* ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && if [ "$ENVIRONMENT" = "development" ] && [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi

# Solo copiar el código si no se va a montar por volumen (como en producción)
COPY . .

CMD ["gunicorn", "hub.wsgi:application", "--bind", "0.0.0.0:8000"]
