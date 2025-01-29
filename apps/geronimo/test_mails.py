# Example 1: Basic Usage
from Service.mailService import EmailServiceConfig, EmailServiceClient, EmailPayload


def send_simple_email():
    # Initialize configuration
    config = EmailServiceConfig(
        email_service_endpoint="https://your-email-service.com",
        token_endpoint="https://your-auth-service.com/token",
        client_id="your_client_id",
        client_secret="your_client_secret",
    )

    # Create email client
    client = EmailServiceClient(config)

    # Create email payload
    payload = EmailPayload(
        app_uuid="your-app-uuid",
        to=["recipient@example.com"],
        cc=[],
        frm="sender@example.com",
        subject="Test Email",
        template_id="template123",
        content_key_val_pairs={
            "name": "John Doe",
            "message": "Hello from our service!",
        },
    )

    # Send email
    try:
        response = client.send_email(payload)
        print(f"Email sent successfully: {response}")
        return response
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise


# Example 2: Using with Template Encoding
def send_email_with_template():
    config = EmailServiceConfig(
        email_service_endpoint="https://your-email-service.com",
        token_endpoint="https://your-auth-service.com/token",
        client_id="your_client_id",
        client_secret="your_client_secret",
    )

    client = EmailServiceClient(config)

    # Encode your template
    template_content = """
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Welcome, {{name}}!</h1>
        <p>{{message}}</p>
    </body>
    </html>
    """
    encoded_template = client.encode_template(template_content)

    payload = EmailPayload(
        app_uuid="your-app-uuid",
        to=["recipient@example.com"],
        cc=["cc1@example.com", "cc2@example.com"],
        frm="sender@example.com",
        subject="Welcome Email",
        template_id="welcome_template",
        content_key_val_pairs={
            "name": "John Doe",
            "message": "Thank you for joining us!",
            "template_content": encoded_template,
        },
    )

    try:
        response = client.send_email(payload)
        print(f"Email with template sent successfully: {response}")
        return response
    except Exception as e:
        print(f"Failed to send email with template: {e}")
        raise


# Example 3: Service Class Implementation
class EmailService:
    def __init__(self, config: EmailServiceConfig):
        self.client = EmailServiceClient(config)

    def send_welcome_email(self, user_email: str, user_name: str):
        payload = EmailPayload(
            app_uuid="your-app-uuid",
            to=[user_email],
            cc=[],
            frm="welcome@yourcompany.com",
            subject="Welcome to Our Service",
            template_id="welcome_template",
            content_key_val_pairs={
                "name": user_name,
                "welcome_message": "We're excited to have you on board!",
            },
        )

        return self.client.send_email(payload)

    def send_alert_email(self, alert_type: str, recipients: list, alert_data: dict):
        payload = EmailPayload(
            app_uuid="your-app-uuid",
            to=recipients,
            cc=[],
            frm="alerts@yourcompany.com",
            subject=f"Alert: {alert_type}",
            template_id="alert_template",
            content_key_val_pairs={"alert_type": alert_type, "alert_data": alert_data},
        )

        return self.client.send_email(payload)


# Example usage of the EmailService class
def main():
    # Initialize configuration
    config = EmailServiceConfig(
        email_service_endpoint="https://your-email-service.com",
        token_endpoint="https://your-auth-service.com/token",
        client_id="your_client_id",
        client_secret="your_client_secret",
    )

    # Create email service
    email_service = EmailService(config)

    # Send welcome email
    try:
        email_service.send_welcome_email(
            user_email="newuser@example.com", user_name="John Doe"
        )
    except Exception as e:
        print(f"Failed to send welcome email: {e}")

    # Send alert email
    try:
        email_service.send_alert_email(
            alert_type="System Warning",
            recipients=["admin@example.com", "support@example.com"],
            alert_data={"severity": "high", "message": "System resources running low"},
        )
    except Exception as e:
        print(f"Failed to send alert email: {e}")


if __name__ == "__main__":
    main()
