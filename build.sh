#!/bin/bash

set -e

OLD_PWD=$(pwd)
cd $(dirname $0)

IMAGE_NAME="scheduled-events-api"

systemctl is-active --quiet docker || systemctl start docker

docker build -t ${IMAGE_NAME} .
docker save -o ${IMAGE_NAME}.tar ${IMAGE_NAME}
gzip -f ${IMAGE_NAME}.tar

echo; echo "scp ${IMAGE_NAME}.tar.gz to the server and load it with:"
echo "docker load -i ${IMAGE_NAME}.tar.gz"

cd $OLD_PWD
