# saves the mailbox dataset to a binary file for training
# loosely modeled after karpathy's nanogpt prepare.py script 

import os
import sys
import array
from tqdm import tqdm
import numpy as np
import tiktoken 
import argparse

# the larger the better; you get encoding weirdness at chunk boundaries
ENCODING_CHUNKS_PER_TIC = 1000000

parser = argparse.ArgumentParser(description='prepare mbox file')
parser.add_argument('-f', '--file', required=True, help='File path (output of clean_mailbox.py script)')
parser.add_argument('-n', '--num_bytes', type=int, default=sys.maxsize, help='number of bytes to process (default: all)')
args = parser.parse_args()
file_path = args.file
n_bytes = args.num_bytes or 999999999999

enc = tiktoken.get_encoding("gpt2")

input_file_path = file_path
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

# TODO: wrap in tqdm 
print ("Tokenizing datasets using gpt2 BPE.")
def encode(d):
    num_bytes = len(d)
    num_chunks = int(num_bytes / ENCODING_CHUNKS_PER_TIC) + 1
    print (f"Encoding {num_bytes} bytes using {num_chunks} chunks...")
    full_encoding = []
    for i in tqdm(range(num_chunks)):
        chunk_start = i * ENCODING_CHUNKS_PER_TIC
        chunk_end = min((i+1) * ENCODING_CHUNKS_PER_TIC -1, num_bytes) 
        byte_array = d[chunk_start:chunk_end]
        encoded_chunk = enc.encode(byte_array)   
        full_encoding.extend(encoded_chunk) # append to the full encoding
    return full_encoding

# TODO: wrap in tqdm 
encoded_text = {}
for split in ['train', 'val', 'test']:
    print (f"Encoding {split} dataset...")
    encoded_text[split] = encode(dataset[split])
    filename = os.path.join(os.path.dirname(__file__), f'{split}.bin')
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
#print (decoded_text)

