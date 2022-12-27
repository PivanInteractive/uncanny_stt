import wave
import queue
import pyaudio
import webrtcvad
import collections
import numpy as np


class VADAudio(object):
    def __init__(self, callback=None, device=None, input_rate=16000, file=None, aggressiveness=2):
           """Filter & segment audio with voice activity detection."""
 
           self.FORMAT = pyaudio.paInt16
           # Network/VAD rate-space
           self.RATE_PROCESS = 16000
           self.CHANNELS = 1
           self.BLOCKS_PER_SECOND = 50
            
           def proxy_callback(in_data, frame_count, time_info, status):
               if self.chunk is not None:
                   in_data = self.wf.readframes(self.chunk)
               callback(in_data)
               return (None, pyaudio.paContinue)

           if callback is None: callback = lambda in_data: self.buffer_queue.put(in_data)
           self.buffer_queue = queue.Queue()
           self.device = device
           self.input_rate = input_rate
           self.sample_rate = self.RATE_PROCESS
           self.block_size = int(self.RATE_PROCESS / float(self.BLOCKS_PER_SECOND))
           self.block_size_input = int(self.input_rate / float(self.BLOCKS_PER_SECOND))
           self.pa = pyaudio.PyAudio()
           self.vad = webrtcvad.Vad(aggressiveness)

           kwargs = {
               'format': self.FORMAT,
               'channels': self.CHANNELS,
               'rate': self.input_rate,
               'input': True,
               'frames_per_buffer': self.block_size_input,
               'stream_callback': proxy_callback,
           }

           self.chunk = None
           # if not default device
           if self.device:
               kwargs['input_device_index'] = self.device
           elif file is not None:
               self.chunk = 320
               self.wf = wave.open(file, 'rb')

           #self.stream = self.pa.open(**kwargs)
           #self.stream.start_stream()
            
            
    def resample(self, data, input_rate):
           data16 = np.fromstring(string=data, dtype=np.int16)
           resample_size = int(len(data16) / self.input_rate * self.RATE_PROCESS)
           resample = signal.resample(data16, resample_size)
           resample16 = np.array(resample, dtype=np.int16)
           return resample16.tostring()
    
    
    def read_resampled(self):
           ## Return a block of audio data resampled to 16000hz, blocking if necessary.
           return self.resample(data=self.buffer_queue.get(),
                                input_rate=self.input_rate)

    def read(self):
       return self.buffer_queue.get()
        
        
    def write_wav(self, filename, data):
           #print(f"write wav {filename}")
           wf = wave.open(filename, 'wb')
           wf.setnchannels(self.CHANNELS)
           # wf.setsampwidth(self.pa.get_sample_size(FORMAT))
           assert self.FORMAT == pyaudio.paInt16
           wf.setsampwidth(2)
           wf.setframerate(self.sample_rate)
           wf.writeframes(data)
           wf.close()
            
    frame_duration_ms = property(lambda self: 1000 * self.block_size // self.sample_rate)
    
    def frame_generator(self):
       if self.input_rate == self.RATE_PROCESS:
           while True:
               yield self.read()
       else:
           while True:
               yield self.read_resampled()
            

    def vad_collector(self, padding_ms=200, ratio=0.65, frames=None):
           """Generator that yields series of consecutive audio frames comprising each utterence, separated by yielding a single None.
               Determines voice activity by ratio of frames in padding_ms. Uses a buffer to include padding_ms prior to being triggered.
               Example: (frame, ..., frame, None, frame, ..., frame, None, ...)
                         |---utterence---|        |---utterence---|
           """
           if frames is None: frames = self.frame_generator()
           num_padding_frames = padding_ms // self.frame_duration_ms
           ring_buffer = collections.deque(maxlen=num_padding_frames)
           triggered = False

           for frame in frames:

               is_speech = self.vad.is_speech(frame, self.sample_rate)

               if not triggered:
                   ring_buffer.append((frame, is_speech))
                   num_voiced = len([f for f, speech in ring_buffer if speech])
                   if num_voiced > ratio * ring_buffer.maxlen:
                       triggered = True
                       for f, s in ring_buffer:
                           yield f
                       ring_buffer.clear()

               else:
                   yield frame
                   ring_buffer.append((frame, is_speech))
                   num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                   if num_unvoiced > ratio * ring_buffer.maxlen:
                       triggered = False
                       yield None
                       ring_buffer.clear()
