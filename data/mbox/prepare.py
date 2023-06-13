"""
similar to mbox_char/prepare.py, but tokenizing via BPE, not char-level.
"""

import sys
import os
import pickle
import requests
import numpy as np
from tqdm import tqdm
from collections import Counter
import argparse
import subprocess
import tiktoken
from datasets import load_dataset # huggingface datasets


MIN_COUNT = 10 # min count to include in vocab
ENCODING_DATATYPE = np.uint16

# the larger the better; you get encoding weirdness at chunk boundaries
BYTES_PER_CHUNK = 10000000 # 10MB -> 10 minutes    

def process(text):
    ids = enc.encode_ordinary(text) # encode_ordinary ignores any special tokens
    ids.append(enc.eot_token) # add the end of text token, e.g. 50256 for gpt2 bpe
    out = {'ids': ids, 'len': len(ids)}
    return out

def encode(s):
    # writeme
    return [stoi[c] for c in s] # encoder: take a string, output a list of integers

def decode(l):
    # writeme
    return ''.join([itos[i] for i in l]) # decoder: take a list of integers, output a string


# script entry point 
parser = argparse.ArgumentParser(description='prepare mbox file')
parser.add_argument('-f', '--file', required=True, help='File path (output of clean_mailbox.py script)')
args = parser.parse_args()
input_file = args.file
output_prefix = input_file + "."

# count lines in input file 
command  = "wc " + input_file + " | awk '{print $1}'"
result = subprocess.run(command, shell=True, capture_output=True)
num_lines = int(result.stdout.decode().strip())
print (f"num_lines: {num_lines}")
split = int(0.9 * num_lines)
command = f"split -d -l {split} {input_file} {output_prefix}chunk"
subprocess.run(command, shell=True)
command = f"mv {output_prefix}chunk00 {output_prefix}train"
subprocess.run(command, shell=True)
command = f"mv {output_prefix}chunk01 {output_prefix}val"
subprocess.run(command, shell=True)

enc = tiktoken.get_encoding("gpt2")  #TODO: Try 'cl100k_base'
vocab_size = enc.n_vocab

tokenized = {}
for batch in ['train', 'val']:
    input_file = output_prefix + batch

    # read in the data
    lines_read = 0 
    n_tokens = 0
    with open(input_file, "r") as file:
        tokenized[batch] = []
        for line in file:
            lines_read += 1
            line = line.rstrip()  # Remove trailing newline character
            ids = enc.encode_ordinary(line)
            ids.append(enc.eot_token) # add the end of text token, e.g. 50256 for gpt2 bpe  
            n_tokens += len(ids)
            tokenized[batch].extend(ids)
    print(f"read {lines_read} lines from {input_file} and wrote {n_tokens} tokens.")

# export to bin files
train_ids = np.array(tokenized['train'], dtype=ENCODING_DATATYPE)
val_ids = np.array(tokenized['val'], dtype=ENCODING_DATATYPE)
train_ids.tofile(os.path.join(os.path.dirname(__file__), 'train.bin'))
val_ids.tofile(os.path.join(os.path.dirname(__file__), 'val.bin'))

print ("Sanity checking: here's the first 1000 symbols from training split:")
filename = os.path.join(os.path.dirname(__file__), 'train.bin')
encoded_bytes = np.fromfile(filename, dtype=ENCODING_DATATYPE, count=1000)
print(enc.decode(encoded_bytes.tolist()))
