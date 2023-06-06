# clean up mailbox  

# prerequisites: 
# pip install bs4
# pip install mailbox

import sys
import mailbox
from bs4 import BeautifulSoup
import re

# Path to your mbox file
mbox_file = './start.mbox'

# running counter 
multipart_messages = 0;

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
print (f"Found {total_messages} messages.", file=sys.stderr)

# Iterate over each email in the mbox file
n = 0;
for message in mbox:
    n += 1
    if (n % 100 ==0 or n == total_messages ):
        print (f"Processed {n} messages; ; found {multipart_messages} multipart messages.", file=sys.stderr)

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
