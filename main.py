import imaplib
import email
from email.header import decode_header
import base64
from bs4 import BeautifulSoup
import re
from config import Config_mail_pass, Config_username, Config_imap_server, Config_bot_token, Config_chat_id
from time import sleep

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

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

def get_email_attachments(imap, msg_num, save_dir="attachments"):
    import os
    os.makedirs(save_dir, exist_ok=True)

    res, data = imap.fetch(str(msg_num).encode(), '(RFC822)')
    msg = email.message_from_bytes(data[0][1])

    files = []

    for part in msg.walk():
        content_disposition = part.get("Content-Disposition")

        if content_disposition and "attachment" in content_disposition:
            filename, encoding = decode_header(part.get_filename())[0]
            if isinstance(filename, bytes):
                filename = filename.decode(encoding or "utf-8", errors="ignore")

            filepath = os.path.join(save_dir, filename)

            with open(filepath, "wb") as f:
                f.write(part.get_payload(decode=True))

            files.append(filepath)

    return files

subject, sender, text = get_email_info(imap, 1030)
print(subject)
print(sender)
print(text)

attachments = get_email_attachments(imap, 1031)
print(attachments)


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def send_custom_text(update: Update, context: ContextTypes.DEFAULT_TYPE, custom_text: str):
    """
    Отправляет переданный текст пользователю
    """
    chat_id = update.effective_chat.id
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=custom_text
    )


# Функция отправки разных типов файлов
async def send_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Отправка документа (любого файла)
    await context.bot.send_document(
        chat_id=chat_id,
        document=open('attachments/11Л.pdf', 'rb'),
        caption="Это документ PDF"
    )
    

app = ApplicationBuilder().token(Config_bot_token).build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("sendfile", send_file))

app.run_polling()