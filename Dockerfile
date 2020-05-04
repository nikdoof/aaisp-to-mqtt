FROM python:3.8-alpine

COPY requirements.txt /app/
COPY aaisp-to-mqtt.py /app/
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["/usr/bin/python", "/app/aaisp-to-mqtt.py"]
