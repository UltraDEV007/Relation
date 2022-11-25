#!/usr/bin/env bash                                                                   
set -eo pipefail

# Create mount directory for service                                                  
mkdir -p $MNT_DIR
                                                                                      
echo "Mounting GCS Fuse."
gcsfuse --debug_gcs --debug_fuse $GCS_BUCKET $MNT_DIR
echo "Mounting completed."

ls -al $MNT_DIR
                                  
/usr/local/bin/uwsgi --ini server.ini &

wait -n  
