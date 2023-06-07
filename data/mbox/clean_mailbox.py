# clean up mailbox  

# prerequisites: 
# pip install bs4
# pip install mailbox

import sys
import mailbox
from bs4 import BeautifulSoup
import re
import argparse

EMAIL_SEPARATOR = "**EOM**"

parser = argparse.ArgumentParser(description='pre-prepare mbox file')
parser.add_argument('-f', '--file', help='File path')
parser.add_argument('-n', '--messages', type=int, default=sys.maxsize, help='number of messages to process (default: all)')
args = parser.parse_args()
file_path = args.file
n_messages_to_process = args.messages

mbox_file = file_path;

multipart_messages = 0; # running counter 

# extract text from HTML
def extract_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ')
    return text

# decode to utf-8 and remove any lines that can't be decoded
def decode(m):
    text = m.get_payload(decode=True).decode('utf-8', errors="ignore")
    return text
 
print ("Opening mbox file " + mbox_file, file=sys.stderr);    
mbox = mailbox.mbox(mbox_file)
total_messages = len(mbox)
quota = min (total_messages, n_messages_to_process)
print (f"Found {total_messages} messages.", file=sys.stderr)
print (f"Will process {quota} messages", file=sys.stderr) 

# Iterate over each email in the mbox file
n = 0;
for message in mbox:
    n += 1
    print (EMAIL_SEPARATOR + "\n") 
    if (n % 100 ==0 or n == total_messages ):
        print (f"Processed {n} messages; ; found {multipart_messages} multipart messages.", file=sys.stderr)

    if (n >= quota):
        break;

    # Extract the text content
    if message.is_multipart():
        # If the email is multipart (contains both HTML and plaintext),
        # extract the plaintext part
        multipart_messages +=1
        for part in message.get_payload():
            if part.get_content_type() == 'text/plain':
                text = decode(part)
    else:
        # If the email is not multipart, assume it's HTML and extract the text
        html = decode(message)   # message.get_payload(decode=True).decode('utf-8')
        text = extract_text(html)

    # Remove any remaining HTML tags using regex
    text = re.sub('<[^<]+?>', '', text)

    # Remove extra whitespace
    text = re.sub('<[^<]+?>', '', text)

    # Remove empty lines
    lines = text.splitlines()
    lines = [line for line in lines if line.strip() != ""]
    text =  '\n'.join(lines)

    # Print the processed text
    print(text)
