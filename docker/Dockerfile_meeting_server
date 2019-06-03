FROM python:3.7-alpine

WORKDIR /mdt_server
COPY . .

RUN apk add build-base
RUN pip install -r requirements.txt

ENV MDT_SERVER_CONFIG config.container
ENV PYTHONPATH /mdt_server

CMD ["python", "meeting_server.py"]