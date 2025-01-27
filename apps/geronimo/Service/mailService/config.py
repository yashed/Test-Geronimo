import os
from dotenv import load_dotenv

# Load environment variables from .env locally
load_dotenv()

# Use placeholders for testing locally
SERVICE_URL = os.getenv(
    "CHOREO_GERONIMO_MAILSERVICE_SERVICEURL", "https://mock-service-url.com"
)
CONSUMER_KEY = os.getenv("CHOREO_GERONIMO_MAILSERVICE_CONSUMERKEY", "mock-consumer-key")
CONSUMER_SECRET = os.getenv(
    "CHOREO_GERONIMO_MAILSERVICE_CONSUMERSECRET", "mock-consumer-secret"
)
TOKEN_URL = os.getenv(
    "CHOREO_GERONIMO_MAILSERVICE_TOKENURL", "https://mock-token-url.com"
)
API_KEY = os.getenv("CHOREO_API_KEY", "mock-api-key")


print("SERVICE_URL: ", SERVICE_URL)
print("CONSUMER_KEY: ", CONSUMER_KEY)
print("CONSUMER_SECRET: ", CONSUMER_SECRET)
print("TOKEN_URL: ", TOKEN_URL)
print("API_KEY: ", API_KEY)

if not all([SERVICE_URL, CONSUMER_KEY, CONSUMER_SECRET, TOKEN_URL, API_KEY]):
    raise ValueError("One or more required environment variables are missing")
