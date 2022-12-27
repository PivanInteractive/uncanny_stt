import io
import os
import csv
import time
import numpy as np
import tensorflow as tf




class VoiceClassifier:
    def __init__(
            self,
            model_path="yamnet.tflite",
            class_map_path="yamnet_class_map.csv"
        ):
        self.class_names = class_names_from_csv(open(class_map_path).read())
        
        self.interpreter = tf.lite.Interpreter(model_path)
        self.input_details = self.interpreter.get_input_details()
        self.waveform_input_index = input_details[0]['index']
        self.output_details = self.interpreter.get_output_details()
        self.scores_output_index = output_details[0]['index']
        self.embeddings_output_index = output_details[1]['index']
        self.spectrogram_output_index = output_details[2]['index']

        self.remap = {
            'laugh': [
                'laughter',
                'baby laughter',
                'giggle',
                'snicker',
                'belly laugh',
                '"Chuckle, chortle"'
            ],
            'scream': [
                'shout',
                'bellow',
                'whoop',
                'yell',
                'children shouting',
                'screaming'
            ]
        }
        

    def class_names_from_csv(self,class_map_csv_text):
      class_map_csv = io.StringIO(class_map_csv_text)
      class_names = [display_name for (class_index, mid, display_name) in csv.reader(class_map_csv)]
      class_names = class_names[1:] 
      return class_names
      

    def run(self,waveform):
        self.interpreter.resize_tensor_input(self.waveform_input_index, [len(waveform)], strict=True)
        self.interpreter.allocate_tensors()
        self.interpreter.set_tensor(self.waveform_input_index, waveform)
        
        ## Forward
        self.interpreter.invoke()
        scores = self.interpreter.get_tensor(scores_output_index)

        ## Process scores
        mean = scores.mean(axis=0)
        k = 10
        top_k = np.argsort(-scores.mean(axis=0))[:k]
        top_k_preds = []
        for idx in top_k:
            name,score = self.class_names[idx].lower(),mean[idx]
            top_k_preds.append((name,score))
            
        sums = {'laugh':0,'scream':0}
        for pred in top_k_preds:
            name,score = pred
            if name in self.remap['laugh']:
                sums['laugh'] += score
            if name in self.remap['scream']:
                sums['scream'] += score
        
        return sums
        


