#!/bin/bash

set -eou pipefail

function cleanup(){
    echo "Cleaning up..."
    docker compose stop
    docker compose down -v
}

trap cleanup EXIT

docker compose build
docker compose watch

read -n1 -rsp $'\nPress any key to exit....\n'
