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

    print("mail data = ", response_data)
    sg = SendGridAPIClient(SENDGRID_API_KEY)

    # Prepare dynamic data for the email template
    dynamic_data = {
        "name": response_data.get("name", "N/A"),
        "job_title": response_data.get("job_title", "N/A"),
        "email": response_data.get("email", "N/A"),
        "social_media_links": [
            {"platform": link["platform"], "url": link["url"]}
            for link in response_data.get("social_media_links", [])
        ],
        "person_profile": response_data.get(
            "professional_summary", "No Personal Detail Available"
        ),
        "company": response_data.get("company", "N/A"),
        "company_overview": response_data.get(
            "company_summary", "No Company Detail Available"
        ),
        "company_competitors": response_data.get("company_competitors", "").split(", "),
        "company_news": [
            {
                "title": news_item.get("title", ""),
                "url": news_item.get("url", ""),
                "description": news_item.get("description", ""),
            }
            for news_item in response_data.get("company_news", [])
        ],
    }

    print("Dynamic Data -", dynamic_data)

    # Create the email object
    message = Mail(from_email=Email("geronimo.test.01@gmail.com"))
    message.template_id = "d-a6c1b0ab7ad84f74b399bb7f28d07998"

    personalization = Personalization()
    personalization.add_to(Email("yashedthisara2001@gmail.com"))  # Main recipient

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
