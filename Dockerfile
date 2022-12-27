# syntax=docker/dockerfile:1

FROM ubuntu:latest AS build

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/root/src:env/lib/python3/site-packages/

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    python3 \
    python3-pip \
    portaudio19-dev \
    ffmpeg \
    libasound2

RUN pip3 install PyAudio webrtcvad numpy tensorflow

WORKDIR /src
COPY . /src

EXPOSE 4420

ENTRYPOINT ["/src/run.sh"]