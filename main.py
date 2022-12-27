#!/usr/bin/env python3


import io
import os
import re
import time
import socket
import subprocess
import numpy as np
from VAD import VADAudio
from yamnet import VoiceClassifier
from threading import Thread
from datetime import datetime

p = lambda x: print(x, flush=True)


## Init socket and buffer
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
addr = ("0.0.0.0", 4420)
sock.bind(addr)
sock.listen(0)


def stream(client):
    ## Inits
    buf = io.BytesIO()

    # Start audio with VAD
    vad_audio = VADAudio(aggressiveness=1,
                        device=None,
                        input_rate=16000,
                        file=None)

    ## Ingestion helpers
    def grab_data(client, buffer):
        ## Recieve packet of audio and write to buf
        data = client.recv(2)
        if data == b'':
            p("Received no data.")
        size = int.from_bytes(data, "big")
        data = client.recv(size)
        buffer.write(data)
        buffer.seek(-1*size, 1)

    def frame_gen(client, buffer):
        ## Generator for model input
        while True:
            grab_data(client,buffer)
            yield buffer.read(640)

    ## Mainloop
    p("\n\n\nBeginning Uncanny STT.\n")

    # what to run
    whisper = False
    yamnet = True

    if yamnet:
        vc = VoiceClassifier()

    while True:
        try:

            ## Grab first packet for buffer
            grab_data(client,buf)

            last_phrase = ""
            last_command = 0

            ## This loop should continue indefinitely
            wav_data = bytearray()
            frames = vad_audio.vad_collector(frames=frame_gen(client, buf))
            for frame in frames:
                if frame is not None and len(wav_data) < 80000:
                    wav_data.extend(frame)
                else:
                    if whisper:
                        stt(wav_data,vad_audio)

                    if yamnet:
                        classify_voice(vc,wav_data)

                ## reset
                wav_data = bytearray()
                buf.seek(0)
                buf.truncate(0)


        except Exception as e:
            p(f"Exception: {e}")
            if os.path.isfile(wav_fname):
                os.remove(wav_fname)



def stt(wav_data,vad_audio):
    start = time.time()

    ## Write wav file of VAD
    timestamp = datetime.now().strftime("vad_%Y-%m-%d_%H-%M-%S_%f.wav")
    wav_fname = f"samples/{timestamp}"
    vad_audio.write_wav(wav_fname, wav_data)
    wav_data = bytearray()

    ## Run through whisper.cpp
    cmd = [
        './main',
        '-nt',
        '-m','models/ggml-tiny.en.bin',
        '-f', wav_fname
    ]
    output = subprocess.run(cmd, capture_output=True)
    end = time.time()
    length = round(end-start,3)

    ## Process text output
    rawtext = output.stdout.decode("utf-8").strip()

    if len(rawtext) > 2:
        p(f"{rawtext} {length}s")

    newtext = last_phrase + " " + rawtext

    text = newtext.lower()
    text = re.sub(r'[^\w\s]', '', text)

    if len(text) > 2:
        text = text.split(" ")
        for i,word in enumerate(text):
            if word in ['record','clip']:
                if 'this' in text[i:] or 'that' in text[i:]:
                    dt = time.time() - last_command
                    if dt > 10:
                        p(">>> SD BROADCAST CLIP <<<")
                        last_command = time.time()

    ## remove wav file
    os.remove(wav_fname)

    dt = time.time() - last_command
    if dt > 10:
        last_phrase = rawtext


def classify_voice(vc,wav_data):
    out = vc.run(wav_data)
    print(out)


def main():
    p(f"Waiting for a connection on :4420.")
    (client, addr) = sock.accept()
    host, port = client.getpeername()
    p(f"New connection {host} {port}")
    Thread(target=stream, args=(client,)).start()


if __name__ == "__main__":
    main()
