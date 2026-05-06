FROM python:3.11-slim

WORKDIR /app

# Спочатку shared/, бо рідко змінюється
COPY shared/ /app/shared/

# Залежності
COPY edge/requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Сам сервіс
COPY edge/ /app/

CMD ["python", "main.py"]
