#!/usr/bin/env python3


import io
import os
import socket
import subprocess
import numpy as np
from utils import *
from threading import Thread


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
            yield buffer.read()

    ## Mainloop
    print("\n"*3,"Beginning VAD to WAV.","\n")
    
    while True:
        ## Grab first packet for buffer
        grab_data(client,buf)
        
        ## This loop should continue indefinitely
        wav_data = bytearray()
        frames = vad_audio.vad_collector(frames=frame_gen(client, buf))
        for frame in frames:
            if frame is not None:
                wav_data.extend(frame)
            else:
                ## Write wav file of VAD
                wav_fname = f"samples/{datetime.now().strftime("vad_%Y-%m-%d_%H-%M-%S_%f.wav")}"
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
                text = output.stdout.decode("utf-8").strip().split(" ")

                ## parse text
                for i,word in enumerate(text):
                    if word == "uncanny":
                        if word[i+1] == "clip" and word[i+2] == "that":
                            print("SD BROADCAST: Uncanny Clip That")

                        if word[i+1] == "record" and word[i+2] == "this":
                            print("SD BROADCAST: Uncanny Record This")
                        
                ## cleanup
                os.remove(wav_fname)
                buf.seek(0)
                buf.truncate(0)

        #if buf.tell() > (3 * 16000 * 2): # 3 seconds of 16kHz samples at 16bit (2 bytes)
        #    ## Reset buffer
        #    #print(f"Buffer is full. {buf.tell()}")
        #    buf.seek(0)
        #    buf.truncate(0)


def main():
    print(f"Waiting for a connection on :4420.")
    (client, addr) = sock.accept()
    host, port = client.getpeername()
    print(f"New connection {host} {port}")
    Thread(target=stream_stt, args=(client,)).start()


if __name__ == "__main__":
    main()
