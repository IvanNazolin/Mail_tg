import imaplib
import email
from email.header import decode_header
import base64
from bs4 import BeautifulSoup
import re
from config import Config_mail_pass, Config_username, Config_imap_server

mail_pass = Config_mail_pass
username = Config_username
imap_server = Config_imap_server

imap = imaplib.IMAP4_SSL(imap_server)
imap.login(username, mail_pass)


print(imap.select("INBOX"))

print(imap.search(None, 'ALL')) # номера всех писем 

print(imap.search(None, "UNSEEN")) # номера не просмотренных писам

print(imap.uid('search', "UNSEEN", "ALL")) # неизменяемый номер 

def get_email_info(imap, msg_num):
    res, data = imap.fetch(str(msg_num).encode(), '(RFC822)')
    msg = email.message_from_bytes(data[0][1])

    subject = msg.get("Subject")
    if subject:
        subject, encoding = decode_header(subject)[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="ignore")
    else:
        subject = "(без темы)"

    sender = msg.get("From") or "(неизвестный отправитель)"

    text_msg = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                charset = part.get_content_charset() or "utf-8"
                text_msg = part.get_payload(decode=True).decode(charset, errors="ignore")
                break

            elif content_type == "text/html" and not text_msg:
                charset = part.get_content_charset() or "utf-8"
                html = part.get_payload(decode=True).decode(charset, errors="ignore")
                text_msg = BeautifulSoup(html, "html.parser").get_text()
    else:
        charset = msg.get_content_charset() or "utf-8"
        text_msg = msg.get_payload(decode=True).decode(charset, errors="ignore")

    return subject, sender, text_msg.strip()