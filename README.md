# Mail_tg

## Запуск 
1) - создание config.py 
``` python
Config_mail_pass = "" # временный пароль api
Config_username = "" # почта mail.ru
Config_imap_server = "imap.mail.ru" 
Config_bot_token = "" # токет телеграм бота
Config_chat_id = # id клиента тип int
```
2) - Соборка образа 
``` bash
docker build -t mail_tg .
```
3) - Запуск
``` bash 
docker run -d --restart unless-stopped --name mail_tg_container mail_tg
```