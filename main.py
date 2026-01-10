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