import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Personalization
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


def send_mail(responce):

    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))

    dynamic_data = {
        "name": "Yashed Thisara",
        "job_title": "Software Engineer",
        "email": "yashedthisara2001@gmail.com",
        "social_media_links": [
            {"platform": "LinkedIn", "url": "https://www.linkedin.com/in/yashed"},
            {"platform": "GitHub", "url": "https://github.com/yashedthisara"},
        ],
        "company": "WSO2",
        "company_overview": "WSO2 specializes in API management and identity solutions.",
        "company_competitors": ["IBM", "Oracle", "MuleSoft", "Red Hat"],
    }

    # Create the email message
    message = Mail(from_email=Email("geronimo.test.01@gmail.com"))
    message.template_id = "d-a6c1b0ab7ad84f74b399bb7f28d07998"

    # Personalization for the recipient
    personalization = Personalization()
    personalization.add_to(Email("yashedthisara2001@gmail.com"))
    personalization.dynamic_template_data = dynamic_data
    message.add_personalization(personalization)

    # Send the email using SendGrid API
    try:
        response = sg.send(message)
        print("Status Code:", response.status_code)
        print("Response Body:", response.body)
        print("Response Headers:", response.headers)
    except Exception as e:
        print(f"Error: {str(e)}")
