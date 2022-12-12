#!/bin/bash

# build whisper.cpp
./models/download-ggml-model.sh tiny.en
make

# test whisper
#./main -v -otxt -m models/ggml-tiny.en.bin -f samples/jfk.wav 

# test whisper in python
#printf "\n\n STARTING test.py \n\n"
#./test.py

# run main 
./main.py