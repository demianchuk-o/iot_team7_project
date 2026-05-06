FROM python:3.11-slim

WORKDIR /usr/agent

COPY shared/ /usr/agent/shared/

COPY agent/requirements.txt /usr/agent/
RUN pip install --no-cache-dir -r /usr/agent/requirements.txt

COPY agent/src/ /usr/agent/

CMD ["python", "main.py"]
