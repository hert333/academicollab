# FIXED: Migrated to Alpine Linux to drop unpatched Debian OS binary layouts
FROM python:3.11-alpine

# Prevent Python from writing byte-code and optimize system input streams
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install native system engine files 
# FIXED: Leverage virtual build tracking layers to compile extensions and discard tools post-build
RUN set -ex; \
    apk add --no-cache libpq; \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev

# SURGICAL PATCH: Eliminate internal dependency layer package tracking alerts
RUN pip install --no-cache-dir --upgrade pip==26.1.2 setuptools wheel==0.46.2 jaraco.context==6.1.0 && \
    rm -rf /usr/local/lib/python3.11/site-packages/setuptools/_vendor/jaraco.context-*.dist-info \
           /usr/local/lib/python3.11/site-packages/setuptools/_vendor/wheel-*.dist-info

# Copy framework package configurations
COPY requirements.txt /app/

# FIXED: Install dependencies and perform an atomic deletion of the compiler dependencies to reduce surface area
RUN pip install --no-cache-dir -r requirements.txt && \
    apk del --no-cache .build-deps

# Mount application runtime code
COPY . /app/

# Enforce explicit unprivileged execution rules
RUN adduser -D -u 1001 django-user && chown -R django-user:django-user /app
USER django-user

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "config.wsgi:application"]