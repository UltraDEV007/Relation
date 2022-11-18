FROM gcr.io/google.com/cloudsdktool/cloud-sdk:slim

COPY .  /usr/src/app/openrelation-elections
WORKDIR  /usr/src/app/openrelation-elections

FROM python:3.9-slim

RUN addgroup user && adduser -h /home/user -D user -G user -s /bin/sh

COPY .  /usr/src/app/openrelation-elections
WORKDIR  /usr/src/app/openrelation-elections

RUN apt-get update \
    && apt-get install -y gcc libc-dev libxslt-dev libxml2 libpq-dev \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

EXPOSE 8080
CMD ["/usr/local/bin/uwsgi", "--ini", "server.ini"]