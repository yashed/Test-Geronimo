# mailService/__init__.py

from .mail_sender import send_mail
from .mailer import send_email_choreo

__all__ = ["send_mail", "send_email_choreo"]
