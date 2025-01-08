import os
from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.security.api_key import APIKeyHeader
import lanchain_helper as lh
import logging
from mailService import send_mail

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Constants
API_KEY_NAME = "GERONIMO-API-KEY"
API_KEY = os.getenv("GERONIMO_API_KEY", "")

# Security dependency
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid API key",
        )
    logger.info("Valid API key provided")
    return api_key


# Create FastAPI instance
app = FastAPI()

# Enable CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware enabled with all origins allowed")


# Define the request body schema
class UserRequest(BaseModel):
    name: str
    company: str
    country: str
    position: str
    interest: str
    email: str


logger.info("UserRequest schema defined")


# Middleware to handle 404 errors
@app.middleware("http")
async def log_unhandled_requests(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == 404:
        logger.warning(
            "Unhandled endpoint accessed: %s %s",
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=404,
            content={
                "code": "404",
                "description": "The requested resource is not available.",
                "message": "Not Found",
            },
        )
    return response


# Define root endpoint
@app.get("/")
async def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the API"}


# Define a test endpoint
@app.get("/test")
async def test_endpoint():
    logger.info("Test endpoint accessed")
    return {"message": "This is a test endpoint"}


# Define a generate data endpoint
@app.post("/generate_data")
async def generate_data(
    user: UserRequest,
    request: Request,
    api_key: str = Security(verify_api_key),
):
    logger.info("Request authenticated with API key")
    logger.info("Request URL: %s", request.url)
    logger.info("Generate data endpoint called with user: %s", user.json())

    name = user.name
    company = user.company
    position = user.position
    country = user.country
    email = user.email

    try:
        # Generate the data
        logger.debug("Calling generate_data helper function with inputs")
        response = lh.generate_data(name, company, position, country)

        # Send the email with the response data
        send_mail(response, email)

        if not response:
            logger.error("Data generation failed for user: %s", user.json())
            raise HTTPException(status_code=404, detail="Data generation failed")

        social_media_links = [
            {"platform": link["platform"], "url": link["url"]}
            for link in response.get("social_media_links", [])
        ]

        logger.info("Data generation successful for user: %s", user.json())
        return {
            "professional_summary": response.get(
                "professional_summary", "No summary available"
            ),
            "social_media_links": social_media_links,
            "company_summary": response.get(
                "company_summary", "No company summary available"
            ),
            "company_competitors": response.get(
                "company_competitors", "No competitors found"
            ),
            "additional_insights": response.get(
                "company_news", "No additional insights available."
            ),
        }
    except Exception as e:
        logger.exception("An error occurred while processing the request")
        raise HTTPException(status_code=500, detail="Internal server error")
