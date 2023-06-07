# saves the mailbox dataset to a binary file for training. following was helpful:
# https://github.com/HazyResearch/flash-attention/blob/main/training/src/datamodules/language_modeling_hf.py

import os
import array
from tqdm import tqdm
import numpy as np
import tiktoken 


enc = tiktoken.get_encoding("gpt2")

# number of workers in .map() call
# good number to use is ~order number of cpu cores // 2
num_proc = 8

input_file_path = "foo"
print (f"Starting to read {input_file_path}")
with open(input_file_path, 'r') as f:
    alldata = f.read()
print (f"Finished reading {len(alldata)} bytes.")

# create train/test split (TODO: split randomly, vs. just taking the first 80%)
n1 = int(len(alldata)* 0.8)
n2 = int(len(alldata)* 0.1)
dataset = {}
dataset['train'] = alldata[:n1]
dataset['val']   = alldata[n1:n1+n2]
dataset['test']  = alldata[n1+n2:]

print ("Tokenizing datasets using gpt2 BPE.")
def encode(d):
    encoded_tokens = enc.encode(d)
    return encoded_tokens

# TODO: wrap in tqdm 
encoded_text = {}
for split in ['train', 'val', 'test']:
    print (f"Encoding {split} dataset...")
    encoded_text[split] = encode(dataset[split])
    filename = os.path.join(os.path.dirname(__file__), f'{split}.bin')
    # Convert the encoded text to a byte array
    byte_array = array.array('i', encoded_text[split]).tobytes()
    n = len(encoded_text[split])
    with open(filename, 'wb') as file:
        file.write(byte_array)
    print (f"Wrote {n} symbols to {filename}")

print ("Sanity checking: here's the first 1000 symbols from training split:")
filename = os.path.join(os.path.dirname(__file__), 'train.bin')
with open('train.bin', 'rb') as file:
    encoded_bytes = file.read(1000)
encoded_array = array.array('i')
encoded_array.frombytes(encoded_bytes)
decoded_text = enc.decode(encoded_array.tolist())
print (decoded_text)

