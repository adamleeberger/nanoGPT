"""
inspired by shakespeare_char/prepare.py

Encoding is at the character level 
 """


import sys
import os
import pickle
import requests
import numpy as np
import array
from tqdm import tqdm
from collections import Counter
import argparse

MIN_COUNT = 10 # min count to include in vocab
UNKNOWN_CHAR = "*"
ENCODING_DATATYPE = np.uint16

# the larger the better; you get encoding weirdness at chunk boundaries
BYTES_PER_CHUNK = 10000000 # 10MB -> 10 minutes    

parser = argparse.ArgumentParser(description='prepare mbox file')
parser.add_argument('-f', '--file', required=True, help='File path (output of clean_mailbox.py script)')
parser.add_argument('-n', '--num_bytes', type=int, default=sys.maxsize, help='number of bytes to process (default: all)')
args = parser.parse_args()
input_file_path = args.file
n_bytes = args.num_bytes or 999999999999

with open(input_file_path, 'r') as f:
    data = f.read()
print(f"length of dataset in characters: {len(data):,}")

print("Generating vocabulary...")
histogram = Counter(data)
stoi = {}  # maps chars -> idx
itos = {}  # vice versa

 # reserve 0 for UNKNOWN_CHAR
itos[0] = UNKNOWN_CHAR 
idx = 1     
stoi[UNKNOWN_CHAR] = 0  

for character, count in sorted(histogram.items(), key=lambda x: x[1], reverse=True):
    if count >= MIN_COUNT: 
        stoi[character] = idx     
        itos[idx] = character
        idx += 1
        print(f"{character}, Count: {count}")
    else: 
        stoi[character] = 0  # map all unknown chars to 0
vocab_size = idx 
print("vocabulary:", list(itos.values()))
print(f"vocab size: {vocab_size:,}")
print(f"Unknown char: {UNKNOWN_CHAR}")  

def encode(s):
    return [stoi[c] for c in s] # encoder: take a string, output a list of integers
def decode(l):
    return ''.join([itos[i] for i in l]) # decoder: take a list of integers, output a string

# create the train and test splits
n = len(data)
train_data = data[:int(n*0.9)]
val_data = data[int(n*0.9):]

# encode both to integers
train_ids = encode(train_data)
val_ids = encode(val_data)
print(f"train has {len(train_ids):,} tokens")
print(f"val has {len(val_ids):,} tokens")

# export to bin files
train_ids = np.array(train_ids, dtype=ENCODING_DATATYPE)
val_ids = np.array(val_ids, dtype=ENCODING_DATATYPE)
train_ids.tofile(os.path.join(os.path.dirname(__file__), 'train.bin'))
val_ids.tofile(os.path.join(os.path.dirname(__file__), 'val.bin'))

# save the meta information as well, to help us encode/decode later
meta = {
    'vocab_size': vocab_size,
    'itos': itos,
    'stoi': stoi,
}
with open(os.path.join(os.path.dirname(__file__), 'meta.pkl'), 'wb') as f:
    pickle.dump(meta, f)

print ("Sanity checking: here's the first 1000 symbols from training split:")
filename = os.path.join(os.path.dirname(__file__), 'train.bin')
encoded_bytes = np.fromfile(filename, dtype=ENCODING_DATATYPE, count=1000)
print(decode(encoded_bytes.tolist()))
