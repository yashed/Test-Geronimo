# mailService/mail_sender.py

import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Personalization

# Load environment variables
load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

if not SENDGRID_API_KEY:
    raise ValueError("SENDGRID_API_KEY is not set in the environment variables!")


def send_mail(response_data):
    """Main function to send an email."""
    print("Send Grid Key:", SENDGRID_API_KEY)
    sg = SendGridAPIClient(SENDGRID_API_KEY)

    # Prepare dynamic data for the email template
    dynamic_data = {
        "name": response_data.get("name", ""),
        "job_title": response_data.get("position", ""),
        "email": response_data.get("email", ""),
        "social_media_links": [],
    }

    social_links = response_data.get("social_media_links", "")
    if social_links:
        for link in social_links.split("\n"):
            parts = link.split(" - ")
            if len(parts) == 2:
                platform, url = parts[0].strip(), parts[1].strip()
                dynamic_data["social_media_links"].append(
                    {"platform": platform, "url": url}
                )

    dynamic_data["person_profile"] = response_data.get("professional_summary", "")
    dynamic_data["job_title"] = response_data.get("position", "")
    dynamic_data["company"] = response_data.get("company", "")
    dynamic_data["company_overview"] = response_data.get("company_summary", "")
    dynamic_data["company_competitors"] = response_data.get(
        "company_competitors", ""
    ).split("\n")

    print("Dynamic Data -", dynamic_data)

    # Create the email object
    message = Mail(from_email=Email("geronimo.test.01@gmail.com"))
    message.template_id = "d-27e17b14c8f0406b9d745bdee528f9a6"

    personalization = Personalization()
    personalization.add_to(Email("yashedthisara2001@gmail.com"))
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
