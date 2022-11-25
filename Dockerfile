FROM gcr.io/google.com/cloudsdktool/cloud-sdk:slim

COPY .  /usr/src/app/openrelation-elections
WORKDIR  /usr/src/app/openrelation-elections

ENV MNT_DIR /usr/src/app/gcs
RUN addgroup user && adduser -h /home/user -D user -G user -s /bin/sh

RUN apt-get update \
    && apt-get install -y gcc libc-dev libxslt-dev libxml2 libpq-dev \
    curl \
    gnupg2 \
    tini \
    openssl \
    lsb-release; \
    gcsFuseRepo=gcsfuse-`lsb_release -c -s`; \
    echo "deb http://packages.cloud.google.com/apt $gcsFuseRepo main" | \
    tee /etc/apt/sources.list.d/gcsfuse.list; \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key add -; \
    apt-get update; \
    apt-get install -y gcsfuse \
	&& apt-get clean \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

RUN chmod +x run.sh 
EXPOSE 8080
#CMD ["/usr/local/bin/uwsgi", "--ini", "server.ini"]
CMD [ "/usr/src/app/openrelation-elections/run.sh"] 
