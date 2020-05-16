FROM python:3.8-alpine

COPY requirements.txt /app/
COPY aaisp2mqtt.py /app/
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python", "/app/aaisp2mqtt.py"]
