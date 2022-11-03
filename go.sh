#!/bin/bash

MOD="au_py"

sudo docker build --target=build -t $MOD .
if [[ -z $1 ]]; then
    sudo docker run --privileged -e PROD=0 -e AUX=172.31.63.104 --rm --network host -t $MOD
fi