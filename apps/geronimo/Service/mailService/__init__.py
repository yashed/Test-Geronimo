# mailService/__init__.py

from .mail_sender import send_mail
from .config import EmailServiceConfig
from .email_service import EmailServiceClient, EmailPayload

__all__ = [
    "send_mail",
    "EmailServiceConfig",
    "EmailServiceClient",
    "EmailPayload",
]
