# clean up mbox file in advance of training
# designed to work with gmail mbox files, likely adaptable to other email providers
# to get your mbox file from Google, visit takeout.google.com

# Adam Berger
# June 2023

import sys
import glob
import mailbox
from tqdm import tqdm
from bs4 import BeautifulSoup
import re
import argparse
import subprocess
import warnings

# supress warnings from bs (beautiful soup)
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

EMAIL_SEPARATOR = "**EOM**"
# 100000000 # will split the mbox file into chunks of this # lines each
LINES_PER_CHUNK = 1000000

def canonicalize(email_address):
    # JOE.sm.ith@GMAIL.com -> joesmith@gmail.com
    email_address = email_address.lower()
    idx = email_address.find("@gmail.com")
    if idx > 0:
        prefix = email_address[0:idx]
        prefix = prefix.replace(".", "")
        email_address = prefix + "@gmail.com"
    return email_address

# decode to utf-8 and remove any lines that can't be decoded
def decode(m):
    text = m.get_payload(decode=True).decode('utf-8', errors="ignore")
    return text

def process_mbox(mbox_file):
    print(f"Processing {mbox_file}")
    mbox = mailbox.mbox(mbox_file)
    total_messages = len(mbox)
    print(f"Found {total_messages} messages.", file=sys.stderr)
   
    # segregate messages into sent and received. Some messages will be in both, of course.
    sent_messages_output_file = mbox_file + ".sent"
    received_messages_output_file = mbox_file + ".received"
    fs = open(sent_messages_output_file, "w")
    fr = open(received_messages_output_file, "w")

    # running counters
    n = 0
    n_sent = 0
    n_received = 0
    multipart_messages = 0

    # loop through messages in mbox
    for message in tqdm(mbox):
        n += 1
        f = canonicalize(str(message['From']))
        t = canonicalize(str(message['To']))
        cc = canonicalize(str(message['Cc']))
        bcc = canonicalize(str(message['Bcc']))
        belongs_in_sent_folder = True if my_email_address in str(f) else False
        belongs_in_received_folder = True if my_email_address in str(t) or my_email_address in str(cc) or my_email_address in str(bcc) else False

        # Extract the text content
        text = ""
        if message.is_multipart():
            # If the email is multipart (contains both HTML and plaintext),
            # extract the plaintext part
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

        # Print the processed text to the appropriate file(s)
        if belongs_in_sent_folder:
            fs.write(text + EMAIL_SEPARATOR)
            n_sent += 1
        if belongs_in_received_folder:
            fr.write(text + EMAIL_SEPARATOR)
            n_received += 1

    fr.close()
    fs.close()
    print(f"Processed {n} messages: {n_sent} sent messages, {n_received} received messages, {multipart_messages} multipart messages.", file=sys.stderr)

# script entry point here 

parser = argparse.ArgumentParser(description='clean mbox file')
parser.add_argument('-f', '--file', required=True, help='File path')
parser.add_argument('-e', '--email_address', required=True, help='my email address')
args = parser.parse_args()
mbox_file = args.file
my_email_address = canonicalize(args.email_address)

print("Splitting mbox file into chunks", file=sys.stderr)
command = f"rm -f {mbox_file}.chunk_*"
subprocess.run(command, shell=True)
command = f"split -d -l {LINES_PER_CHUNK} {mbox_file} {mbox_file}.chunk_"
subprocess.run(command, shell=True)

# how many files did we create?
command  = f"ls {mbox_file}.chunk_*"
result = subprocess.run(command, shell=True, capture_output=True)
chunk_files = result.stdout.decode().strip().splitlines()
print(f"Breaking mbox into {len(chunk_files)} chunks")
for chunk_file in chunk_files:
    process_mbox(chunk_file)


print ("Merging intermediate files and cleaning up.")
command = f"cat {mbox_file}.chunk_*.sent > {mbox_file}.sent"
subprocess.run(command, shell=True)
command = f"cat {mbox_file}.chunk_*.received > {mbox_file}.received"
subprocess.run(command, shell=True)
command = f"rm -f {mbox_file}.chunk_*"
subprocess.run(command, shell=True)
