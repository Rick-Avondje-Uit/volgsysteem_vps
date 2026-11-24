from django.core.mail.backends.base import BaseEmailBackend
from utils.email import send_mail as custom_send_mail

class CustomEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):

        for message in email_messages:
            custom_send_mail(
                message.subject,
                message.body,
                message.to,
            )
        return len(email_messages)