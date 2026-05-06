FROM python:3.11-slim

WORKDIR /app

COPY shared/ /app/shared/

COPY hub/requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY hub/ /app/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
