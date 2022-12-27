#!/bin/bash

MOD="au_py"

sudo docker build --target=build -t $MOD .
if [[ -z $1 ]]; then
    sudo docker run --privileged --rm --network host -t $MOD
fi
