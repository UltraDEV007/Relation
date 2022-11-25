#!/usr/bin/env bash                                                                   |FROM node:16-slim                                                                     
set -eo pipefail                                                                      |
                                                                                      |## Install system dependencies, `gcsfuse` in particular.
# Create mount directory for service                                                  |RUN set -e; \
mkdir -p $MNT_DIR                                                                     |    apt-get update -y && apt-get install -y \
                                                                                      |    curl \
echo "Mounting GCS Fuse."                                                             |    gnupg2 \
gcsfuse --debug_gcs --debug_fuse $GCS_BUCKET $MNT_DIR                                 |    tini \
echo "Mounting completed."                                                            |    openssl \
                                                                                      |    lsb-release; \
ls -al $MNT_DIR     

/usr/local/bin/uwsgi --ini server.ini &

wait -n  
