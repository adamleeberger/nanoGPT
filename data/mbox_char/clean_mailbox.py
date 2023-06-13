# clean up mbox file in advance of training
# designed to work with gmail mbox files, likely adaptable to other email providers
# to get your mbox file from Google, visit takeout.google.com

# Adam Berger
# June 2023

import sys
#import glob
import mailbox
from tqdm import tqdm
from bs4 import BeautifulSoup
import re
import argparse
import subprocess
import warnings

# suppress beautiful soup warnings 
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

EMAIL_SEPARATOR = "\n\n**EOM**\n\n"
LINES_PER_CHUNK = 10000000  # will split the mbox file into chunks of this # lines each for processing in parallel

# decode to utf-8 and remove any lines that can't be decoded
def decode(m):
    text = m.get_payload(decode=True).decode('utf-8', errors="ignore")
    return text

def process_mbox(input_file, output_file):
    print(f"Processing {input_file}")
    mbox = mailbox.mbox(input_file)
    total_messages = len(mbox)
    print(f"Found {total_messages} messages.", file=sys.stderr)
    f = open(output_file, "w")

    # running counters
    n = 0
    multipart_messages = 0

    # loop through messages in mbox
    for message in mbox:
        n += 1

        # Extract the text content
        text = ""
        if message.is_multipart():
            # If the email is multipart (contains both HTML and plaintext), extract the plaintext part
            multipart_messages += 1
            for part in message.get_payload():
                if part.get_content_type() == 'text/plain':
                    text = decode(part)
        else:
            # If the email is not multipart, assume it's HTML and extract the text
            html = decode(message)
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator=' ')
      
        # Remove any remaining HTML tags using regex
        text = re.sub('<[^<]+?>', '', text)

        # Remove empty lines
        lines = text.splitlines()
        lines = [line for line in lines if line.strip() != ""]
        text = '\n'.join(lines)

        # save the processed text 
        f.write(text + EMAIL_SEPARATOR)
         
    f.close()
    print(f"Processed {n} messages: {multipart_messages} multipart messages.", file=sys.stderr)

# script entry point here 
parser = argparse.ArgumentParser(description='clean mbox file')
parser.add_argument('-f', '--file', required=True, help='File path')
args = parser.parse_args()
input_file = args.file
chunk_file_prefix = input_file + ".chunk_"
output_file = input_file + ".clean"

print("Deleting old chunkfiles", file=sys.stderr)
command = f"rm -f {chunk_file_prefix}*"
subprocess.run(command, shell=True)
print("Creating new chunkfiles", file=sys.stderr)
command = f"split -d -l {LINES_PER_CHUNK} {input_file} {chunk_file_prefix}"
subprocess.run(command, shell=True)

# how many files did we create?
command  = f"ls {chunk_file_prefix}*"
result = subprocess.run(command, shell=True, capture_output=True)
chunk_files = result.stdout.decode().strip().splitlines()
for chunk_file in chunk_files:
    process_mbox(chunk_file, chunk_file+ ".clean")

print ("Merging intermediate files and cleaning up.")
command = f"cat {chunk_file_prefix}*.clean > {output_file}"
subprocess.run(command, shell=True)
command = f"rm -f {chunk_file_prefix}*"
subprocess.run(command, shell=True)
