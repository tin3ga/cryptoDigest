import os

from smtplib import SMTP

APP_EMAIL = os.environ['APP_EMAIL']
APP_PASS = os.environ['APP_PASS']
PERSONAL_EMAIL = os.environ['PERSONAL_EMAIL']
HOST = 'smtp.gmail.com'


class NotificationManager:
    @staticmethod
    def send_email(message):
        with SMTP(host=HOST) as conn:
            conn.starttls()
            conn.login(user=APP_EMAIL, password=APP_PASS)
            conn.sendmail(
                from_addr=APP_EMAIL,
                to_addrs=PERSONAL_EMAIL,
                msg=f'Subject:Weekly Crypto Price Update\n\n{message}'.encode('utf-8')
            )
            return 'Mail Sent'
