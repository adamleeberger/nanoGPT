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

def canonicalize(email_address):
    # joe.sm.ith@gmail.com -> joesmith@gmail.com
    email_address = email_address.lower()
    idx = email_address.find("@gmail.com")
    if idx > 0:
        prefix = email_address[0:idx]
        prefix = prefix.replace(".", "")
        email_address = prefix + "@gmail.com" 
    return email_address

# extract text from HTML
def extract_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ')
    return text

parser = argparse.ArgumentParser(description='pre-prepare mbox file')
parser.add_argument('-f', '--file', required=True, help='File path')
parser.add_argument('-e', '--email_address', required=True, help='my email address')
parser.add_argument('-n', '--messages', type=int, default=sys.maxsize, help='number of messages to process (default: all)')
args = parser.parse_args()
mbox_file = args.file
n_messages_to_process = args.messages or 999999999 
my_email_address = canonicalize(args.email_address)

multipart_messages = 0; # running counter 

# decode to utf-8 and remove any lines that can't be decoded
def decode(m):
    text = m.get_payload(decode=True).decode('utf-8', errors="ignore")
    return text
 
print ("Opening mbox file " + mbox_file, file=sys.stderr);    
mbox = mailbox.mbox(mbox_file)

output_prefix = mbox_file + ".cleaned"

total_messages = len(mbox)
quota = min (total_messages, n_messages_to_process)
print (f"Found {total_messages} messages.", file=sys.stderr)
print (f"Will process {quota} messages", file=sys.stderr) 
print (f"Writing to {output_prefix}.sent and {output_prefix}.received", file=sys.stderr)

# segregate messages into sent and received. Some messages will be in both, of course. 
sent_messages_output_file     = output_prefix + ".sent"
received_messages_output_file = output_prefix + ".received"
fs = open(sent_messages_output_file, "w")
fr = open(sent_messages_output_file, "w")

n = 0
n_sent = 0
n_received = 0;
for message in mbox:
    n += 1
    if (n % 100 ==0 or n==total_messages):
        print (f"Processed {n} messages: {n_sent} sent messages, {n_received} received messages, {multipart_messages} multipart messages.", file=sys.stderr)

    if (n >= quota):
        break;

    f = canonicalize(str(message['From']))
    t = canonicalize(str(message['To']))
    cc = canonicalize(str(message['Cc']))
    bcc = canonicalize(str(message['Bcc']))

    belongs_in_sent_folder = True if my_email_address in str(f) else False
    belongs_in_received_folder = True if my_email_address in str(t) or my_email_address in str(cc) or my_email_address in str(bcc) else False
    if (not belongs_in_received_folder and not belongs_in_sent_folder):
            print (f"From: {f}; To: {t};", file=sys.stderr)

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

    # Print the processed text to the appropriate file(s)
    if belongs_in_sent_folder:
        fs.write(text + EMAIL_SEPARATOR)
        n_sent += 1
    if belongs_in_received_folder:
        fr.write(text + EMAIL_SEPARATOR)
        n_received += 1

fr.close()
fs.close()
