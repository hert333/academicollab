FROM python:3.11-slim

# Enforce optimal Python runtime execution constraints
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system-level dependencies required for runtime execution and cryptographic wrappers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# FIXED: Leverage Docker layer caching by separating dependency maps from source code modifications
COPY requirements.txt /app/

# Execute locked framework installation phase inside the isolated build layer
RUN pip install --no-cache-dir -r requirements.txt

# Copy remaining source code tree assets into the working space
COPY . /app/

# FIXED: Create an unprivileged user boundary and reassign directory tree access permissions
RUN useradd -u 1001 django-user && chown -R django-user:django-user /app
USER django-user

EXPOSE 8000

# Bind production-ready multi-threaded WSGI worker pooling structure to listen on port 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "config.wsgi:application"]