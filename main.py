import imaplib
import email
from email.header import decode_header
import base64
from bs4 import BeautifulSoup
import re
from config import Config_mail_pass, Config_username, Config_imap_server, Config_bot_token, Config_chat_id
from time import sleep
import asyncio
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

async def send_custom_text(update: Update, context: ContextTypes.DEFAULT_TYPE, custom_text: str):    
    await context.bot.send_message(
        chat_id=Config_chat_id,
        text=custom_text
    )

async def send_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Отправка документа (любого файла)
    await context.bot.send_document(
        chat_id=chat_id,
        document=open('attachments/11Л.pdf', 'rb'),
        caption="Это документ PDF"
    )
    
app = ApplicationBuilder().token(Config_bot_token).build()

async def process_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    while True:
        try:
            imap.select("INBOX")
            
            status, data = imap.search(None, 'UNSEEN')
            
            if status != 'OK' or not data[0]:
                print("Пусто")
                await asyncio.sleep(30)
                continue
            
            mail_ids = data[0].decode('utf-8').split()
            
            for mail_id in mail_ids:
                # Получаем информацию о письме
                subject, sender, text = get_email_info(imap, mail_id)
                
                # Также получаем вложения отдельно
                attachments = get_email_attachments(imap, mail_id)
                
                email_match = re.search(r'<([^>]+)>', sender)
                if email_match:
                    clean_sender = email_match.group(1)
                else:
                    clean_sender = sender
                
                clean_text = re.sub(r'<[^>]+>', '', text)
                
                # Формируем сообщение
                message = f"📧 От: {clean_sender}\n"
                message += f"📌 Тема: {subject}\n\n"
                
                if clean_text:
                    message += f"📝 Текст:\n{clean_text[:500]}"
                    if len(clean_text) > 500:
                        message += "..."
                
                # Отправляем текстовую часть
                await send_custom_text(update, context, message)
                
                # Отправляем вложения если они есть
                if attachments:
                    for filename, file_data in attachments:
                        try:
                            # Используем временный файл
                            temp_path = f"temp_{filename}"
                            with open(temp_path, 'wb') as f:
                                f.write(file_data)
                            
                            await context.bot.send_document(
                                chat_id=Config_chat_id,
                                document=open(temp_path, 'rb'),
                                caption=f"Вложение: {filename}"
                            )
                            
                            # Удаляем временный файл
                            import os
                            os.remove(temp_path)
                            
                        except Exception as e:
                            print(f"Ошибка отправки вложения {filename}: {e}")
                            await send_custom_text(update, context, f"⚠️ Не удалось отправить: {filename}")
                
                # Помечаем как прочитанное
                imap.store(mail_id, '+FLAGS', '\\Seen')
                print(f"Письмо {mail_id} обработано, вложений: {len(attachments) if attachments else 0}")
            
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Ошибка: {e}")
            await asyncio.sleep(30)

def get_email_attachments(imap, msg_num):
    """Получает вложения из письма"""
    attachments = []
    
    try:
        res, data = imap.fetch(str(msg_num).encode(), '(RFC822)')
        msg = email.message_from_bytes(data[0][1])
        
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition"))
                
                # Проверяем, является ли часть вложением
                if "attachment" in content_disposition or "filename" in content_disposition:
                    filename = part.get_filename()
                    
                    if filename:
                        # Декодируем имя файла
                        if isinstance(filename, bytes):
                            filename = filename.decode()
                        
                        filename, encoding = decode_header(filename)[0]
                        if isinstance(filename, bytes):
                            filename = filename.decode(encoding or 'utf-8', errors='ignore')
                        
                        file_data = part.get_payload(decode=True)
                        if file_data:
                            attachments.append((filename, file_data))
    
    except Exception as e:
        print(f"Ошибка при получении вложений: {e}")
    
    return attachments
app.add_handler(CommandHandler("process", process_and_send))

app.run_polling()