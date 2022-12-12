#!/usr/bin/env python3


import io
import os
import re
import time
import socket
import subprocess
import numpy as np
from utils import *
from threading import Thread
from datetime import datetime


## Init socket and buffer
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
addr = ("0.0.0.0", 4420)
sock.bind(addr)
sock.listen(0)


def stream_stt(client):
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
            print("Received no data.")
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
    print("\n"*3,"Beginning Uncanny STT.","\n")
    
    while True:
        try:

            ## Grab first packet for buffer
            grab_data(client,buf)
            
            ## This loop should continue indefinitely
            wav_data = bytearray()
            frames = vad_audio.vad_collector(frames=frame_gen(client, buf))
            for frame in frames:
                if frame is not None:
                    wav_data.extend(frame)
                else:
                    start = time.time()

                    ## Write wav file of VAD
                    timestamp = datetime.now().strftime("vad_%Y-%m-%d_%H-%M-%S_%f.wav")
                    wav_fname = f"samples/{timestamp}"
                    vad_audio.write_wav(wav_fname, wav_data)
                    wav_data = bytearray()
                    #print(f"Saving utterance as {wav_fname}")

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

                    rawtext = output.stdout.decode("utf-8").strip()

                    if len(rawtext) > 2:
                        print(f"{rawtext} {length}s")

                    text = rawtext.lower()
                    text = re.sub(r'[^\w\s]', '', text)

                    if len(text) > 2:
                        text = text.split(" ")
                        for i,word in enumerate(text):
                            if word in ['record','clip']:
                                if text[i:] in ['this','that']:
                                    print("SD BROADCAST: RECORD CLIP")


                        '''
                        ## Nobodys perfect. When screaming or talking fast, these mistake for uncanny
                        ## Improved by using larger whisper model or slowing speech down before passing to model
                        uncanny_mistakes = [
                            "oh can he","on kenny", "oh kenny", 
                            "and can you", "im kenny", "on any", 
                            "unkenny", "im danny"
                        ]
                        for mistake in uncanny_mistakes:
                            text = text.replace(mistake,"uncanny")

                        #print(f"{text} {length}s")

                        ## parse command
                        text = text.split(" ")
                        for i,word in enumerate(text):
                            if word == "uncanny":
                                if "clip" in text[i:]:
                                    print("SD BROADCAST: Uncanny Clip (clip of last 10 sec)")

                                if "record" in text[i:]:
                                    print("SD BROADCAST: Uncanny Record (clip of next 10 sec)")

                        '''
                            
                    ## cleanup
                    os.remove(wav_fname)
                    buf.seek(0)
                    buf.truncate(0)

            #if buf.tell() > (3 * 16000 * 2): # 3 seconds of 16kHz samples at 16bit (2 bytes)
            #    ## Reset buffer
            #    #print(f"Buffer is full. {buf.tell()}")
            #    buf.seek(0)
            #    buf.truncate(0)

        except Exception as e:
            print(e)
            pass


def main():
    print(f"Waiting for a connection on :4420.")
    (client, addr) = sock.accept()
    host, port = client.getpeername()
    print(f"New connection {host} {port}")
    Thread(target=stream_stt, args=(client,)).start()


if __name__ == "__main__":
    main()
