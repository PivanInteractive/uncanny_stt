#!/bin/bash

TAG="v$(date +'%Y%m%d%H%M%S')"
CONTAINER=au_py

aws ecr get-login --no-include-email | xargs sudo
sudo docker tag $CONTAINER 123473854105.dkr.ecr.us-west-2.amazonaws.com/$CONTAINER
sudo docker push 123473854105.dkr.ecr.us-west-2.amazonaws.com/$CONTAINER

#sudo docker tag $CONTAINER us.gcr.io/uncanny-224823/$CONTAINER
#sudo docker push us.gcr.io/uncanny-224823/$CONTAINER

git tag $TAG
echo "Tagged new prod version with $TAG"
