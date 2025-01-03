import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import lanchain_helpr as lh
import logging
import json
import re
from mailService import send_mail


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

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
def test_endpoint():
    logger.info("Test endpoint accessed")
    return {"message": "This is a test endpoint"}


# Define an generat data endpoint
@app.post("/generate_data")
async def generate_data(user: UserRequest, request: Request):
    logger.info("Request URL: %s", request.url)
    logger.info("Generate data endpoint called with user: %s", user.json())

    name = user.name
    company = user.company
    position = user.position
    country = user.country

    try:
        # Generate the data
        logger.debug("Calling generate_data helper function with inputs")
        import json

        response = lh.gather_info(name, position, company, country)
        print(response)
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:

            json_string = json_match.group(0)
            print("Extracted JSON String = ", json_string)

            try:
                parsed_json = json.loads(json_string)

            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
        else:
            print("No valid JSON found in the response.")

        # Send the email
        send_mail(parsed_json)

        # return response
        return {
            "professional_summary": parsed_json.get(
                "personal_summary", "No summary available"
            ),
            "social_media_links": parsed_json.get(
                "social_media_links", "No social media links found."
            ),
            "company_summary": parsed_json.get(
                "company_summary", "No company summary available"
            ),
            "company_competitors": parsed_json.get(
                "company_competitors", "No competitors found"
            ),
            "additional_insights": parsed_json.get(
                "company_news", "No News available."
            ),
        }
    except Exception as e:
        logger.exception("An error occurred while processing the request")
        raise HTTPException(status_code=500, detail="Internal server error")
