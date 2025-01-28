import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use environment variables or fallback values for local testing
SERVICE_URL = os.getenv("CHOREO_TEST_GERONIMO_MAILSERVICE_SERVICEURL")
CONSUMER_KEY = os.getenv("CHOREO_TEST_GERONIMO_MAILSERVICE_CONSUMERKEY")
CONSUMER_SECRET = os.getenv("CHOREO_TEST_GERONIMO_MAILSERVICE_CONSUMERSECRET")
TOKEN_URL = os.getenv("CHOREO_TEST_GERONIMO_MAILSERVICE_TOKENURL")
API_KEY = os.getenv("CHOREO_API_KEY")

# Print variables to verify
print("SERVICE_URL: ", SERVICE_URL)
print("CONSUMER_KEY: ", CONSUMER_KEY)
print("CONSUMER_SECRET: ", CONSUMER_SECRET)
print("TOKEN_URL: ", TOKEN_URL)
print("API_KEY: ", API_KEY)

# Ensure all variables are set
if not all([SERVICE_URL, CONSUMER_KEY, CONSUMER_SECRET, TOKEN_URL, API_KEY]):
    raise ValueError("One or more required environment variables are missing")
