import requests
import base64
import json
from dataclasses import dataclass
from typing import List, Dict, Optional
from urllib.parse import urljoin
from .config import EmailServiceConfig


@dataclass
class EmailPayload:
    """Data class for email payload"""

    app_uuid: str
    to: List[str]
    cc: List[str]
    frm: str
    subject: str
    template_id: str
    content_key_val_pairs: Dict[str, str]

    def to_json(self):
        """Convert payload to JSON string"""
        return json.dumps(self.__dict__)


class EmailServiceClient:
    """Client for handling email service operations"""

    def __init__(self, config: EmailServiceConfig):
        """
        Initialize email service client

        Args:
            config: EmailServiceConfig object containing service configuration
        """
        self.config = config
        self.access_token = None

    def _get_access_token(self) -> str:
        """
        Get OAuth2 access token using client credentials

        Returns:
            str: Access token

        Raises:
            requests.exceptions.RequestException: If token retrieval fails
        """
        token_data = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        response = requests.post(self.config.token_endpoint, data=token_data)
        response.raise_for_status()

        token_info = response.json()
        return token_info["access_token"]

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers with authorization token

        Returns:
            Dict[str, str]: Headers dictionary
        """
        if not self.access_token:
            self.access_token = self._get_access_token()

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def encode_template(template_content: str) -> str:
        """
        Encode email template content in base64

        Args:
            template_content: Template content to encode

        Returns:
            str: Base64 encoded template content
        """
        return base64.b64encode(template_content.encode()).decode()

    def send_email(self, payload: EmailPayload) -> Dict:
        """
        Send email using the email service

        Args:
            payload: EmailPayload object containing email details

        Returns:
            Dict: Response from the email service

        Raises:
            requests.exceptions.RequestException: If email sending fails
        """
        headers = self._get_headers()
        endpoint = urljoin(self.config.email_service_endpoint, "/send-smtp-email")

        response = requests.post(endpoint, headers=headers, data=payload.to_json())
        response.raise_for_status()
        return response.json()
