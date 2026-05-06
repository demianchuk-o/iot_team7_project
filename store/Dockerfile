FROM python:3.11-slim

WORKDIR /app

# Install build deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Спочатку shared/, бо рідко змінюється — кращий cache
COPY shared/ /app/shared/

# Залежності
COPY store/requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Сам сервіс
COPY store/ /app/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
