# 1️ Imagen base ligera con Python
FROM python:3.12-slim

# 2️ Variables de entorno recomendadas
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3️ Directorio de trabajo dentro del contenedor
WORKDIR /app

# 4️ Dependencias del sistema necesarias para PostgreSQL
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5️ Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6️ Copiar todo el proyecto
COPY . .

# 7️ Recolectar archivos estáticos
RUN python manage.py collectstatic --noinput

# 8️ Comando de arranque (producción)
CMD ["gunicorn", "ecommerce_snake.wsgi:application", "--bind", "0.0.0.0:8000"]
