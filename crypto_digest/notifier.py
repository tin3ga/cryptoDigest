import os
from email.message import EmailMessage
from email.utils import formataddr
from ssl import create_default_context

from smtplib import SMTP

HOST = 'smtp.gmail.com'


class NotificationManager:
    def __init__(self, app_email=None, app_pass=None, personal_email=None):
        self.app_email = app_email or os.environ['APP_EMAIL']
        self.app_pass = app_pass or os.environ['APP_PASS']
        self.personal_email = personal_email or os.environ['PERSONAL_EMAIL']

    def send_email(self, subject, text_body, html_body):
        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = formataddr(('CryptoDigest', self.app_email))
        message['To'] = self.personal_email
        message.set_content(text_body)
        message.add_alternative(html_body, subtype='html')

        with SMTP(host=HOST) as conn:
            conn.starttls(context=create_default_context())
            conn.login(user=self.app_email, password=self.app_pass)
            conn.send_message(message)

        return True
