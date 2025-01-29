import os
from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.security.api_key import APIKeyHeader
import Helper.langchain_helper as lh
import logging
from Service.queue.queue_manager import start_worker, task_queue
from Service.queue.database_manager import DatabaseManager
from dotenv import load_dotenv

load_dotenv(override=True)

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
print("GERONIMO_API_KEY: ", API_KEY)

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
    allow_headers=["*", "GERONIMO-API-KEY"],
)
logger.info("CORS middleware enabled with all origins allowed")


# Define the request body schema
class EmailInfo(BaseModel):
    subject: str
    from_: str  # need to use from_ as from is a reserved keyword
    to: list[str]
    cc: list[str]


class LeadInfo(BaseModel):
    firstName: str
    lastName: str
    email: str
    phone: str
    jobTitle: str
    company: str
    country: str
    state: str
    areaOfInterest: str
    contactReason: str
    industry: str
    canHelpComment: str


class ExternalRequest(BaseModel):
    emailInfo: EmailInfo
    leadInfo: LeadInfo


# Define the request body schema for sending an email
class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str


logger.info("Request schemas defined")


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


# @app.post("/send_email")
# async def send_email(
#     email_request: EmailRequest,
# ):
#     """
#     Endpoint to test sending email through Choreo email service.
#     """
#     try:
#         response = send_email_choreo(
#             to_email=email_request.to,
#             subject=email_request.subject,
#             body=email_request.body,
#         )
#         return {"message": "Email sent successfully", "response": response}
#     except Exception as e:
#         logger.exception("Error sending email: %s", e)
#         raise HTTPException(status_code=500, detail="Internal server error")


# Initialize worker and database manager
worker = start_worker()
db_manager = DatabaseManager()


@app.on_event("startup")
async def load_pending_tasks():
    logger.info("Loading pending tasks into the queue")
    pending_tasks = db_manager.get_pending_tasks()
    for task in pending_tasks:
        task_queue.put(task)
    logger.info("Pending tasks loaded sucwdwcessfully")


@app.get("/")
async def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the API"}


@app.get("/test")
async def test_endpoint():
    logger.info("Test endpoint accessed")
    return {"message": "This is a test endpoint"}


@app.post("/generate_data")
async def generate_data(
    request_data: ExternalRequest,
    request: Request,
    api_key: str = Security(verify_api_key),
):
    logger.info("Request authenticated with API key")
    try:
        print("Request Data -", request_data)
        lead_info = request_data.leadInfo.dict()
        email_info = request_data.emailInfo.dict()

        # Save to database
        task_id = db_manager.add_task(lead_info)
        email_info["task_id"] = task_id
        db_manager.add_email_info(email_info)

        lead_info["id"] = task_id
        task_queue.put(lead_info)

        return {
            "message": "Task added to the queue. Response will be sent as a mail within 1 minute.",
            "task_id": task_id,
        }
    except Exception as e:
        logger.exception("Error adding task to queue: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
