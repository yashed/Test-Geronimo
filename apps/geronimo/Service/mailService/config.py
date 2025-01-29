from dataclasses import dataclass


@dataclass
class EmailServiceConfig:
    """Configuration class for email service"""

    email_service_endpoint: str
    token_endpoint: str
    client_id: str
    client_secret: str
