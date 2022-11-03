#!/usr/bin/env python3


import subprocess

cmd = [
    './main',
    '-nt',
    '-m','models/ggml-tiny.en.bin',
    '-f', 'samples/jfk.wav'
]

for i in range(3):
    output = subprocess.run(cmd, capture_output=True)
    print("\n")
    text = output.stdout.decode("utf-8").strip().split(" ")
    print(f"PROCESS OUTPUT: {text}")
    print("\n"*4)