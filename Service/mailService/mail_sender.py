# mailService/mail_sender.py

import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Personalization

# Load environment variables
load_dotenv(override=True)

# SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

print("SENDGRID_API_KEY: ", SENDGRID_API_KEY)

if not SENDGRID_API_KEY:
    raise ValueError("SENDGRID_API_KEY is not set in the environment variables!")


def send_mail(response_data, SendTo):
    """
    Send an email using SendGrid API

    Args:
        response_data (dict): The data to be sent in the email
        SendTo (str): The email address to send the email to

    """

    print("mail data = ", response_data)
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    print("SendGrid client", sg)

    # Prepare dynamic data for the email template
    dynamic_data = {
        "subject": "Geronimo Lead Response ",
        "name": response_data.get("name", "N/A"),
        "job_title": response_data.get("job_title", "N/A"),
        "email": response_data.get("email", "N/A"),
        "social_media_links": (
            response_data.get("social_media_links", {"error": "No data found"})
            if isinstance(response_data.get("social_media_links"), list)
            else [
                {
                    "platform": "Error",
                    "url": response_data.get("social_media_links", {}).get(
                        "error", "Unknown error"
                    ),
                }
            ]
        ),
        "person_profile": response_data.get(
            "professional_summary", "No Personal Detail Available"
        ),
        "company": response_data.get("company", "N/A"),
        "company_overview": response_data.get(
            "company_summary", "No Company Detail Available"
        ),
        "company_competitors": response_data.get("company_competitors", "").split(", "),
        "company_news": (
            response_data.get("company_news", [{"error": "No data found"}])
            if isinstance(response_data.get("company_news"), list)
            else [
                {
                    "title": "Error",
                    "url": "",
                    "description": response_data.get("company_news", {}).get(
                        "error", "Unknown error"
                    ),
                }
            ]
        ),
    }

    print("Dynamic Data -", dynamic_data)

    # Create the email object
    # message = Mail(from_email=Email("geronimo.test.01@gmail.com"))
    message = Mail(from_email=Email("geronimo.wso2@gmail.com"))

    # message.template_id = "d-a6c1b0ab7ad84f74b399bb7f28d07998"
    message.template_id = "d-0422142c3c364898967a74e36d6f72a7"

    personalization = Personalization()
    personalization.add_to(Email("yashedthisara2001@gmail.com"))
    personalization.add_to(Email(SendTo))

    personalization.subject = "AI Generated Content of the Lead"
    personalization.dynamic_template_data = dynamic_data
    message.add_personalization(personalization)

    # Send the email using SendGrid API
    try:
        response = sg.send(message)
        print("Status Code:", response.status_code)
        print("Response Body:", response.body)
        print("Response Headers:", response.headers)
        return "Email sent successfully"
    except Exception as e:
        print(f"Error: {str(e)}")
        return "Email sending failed"
