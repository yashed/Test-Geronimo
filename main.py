import os
from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.security.api_key import APIKeyHeader
import Helper.langchain_helper as lh
import logging
from Service.mailService import send_mail
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


# Initialize worker and database manager
worker = start_worker()
db_manager = DatabaseManager()


@app.on_event("startup")
async def load_pending_tasks():
    logger.info("Loading pending tasks into the queue")
    pending_tasks = db_manager.get_pending_tasks()
    for task in pending_tasks:
        task_queue.put(task)
    logger.info("Pending tasks loaded successfully")


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
    user: UserRequest,
    request: Request,
    api_key: str = Security(verify_api_key),
):
    logger.info("Request authenticated with API key")
    logger.info("Request URL: %s", request.url)
    logger.info("Generate data endpoint called with user: %s", user.json())

    try:
        # Save task to database
        task = {
            "name": user.name,
            "company": user.company,
            "country": user.country,
            "position": user.position,
            "interest": user.interest,
            "email": user.email,
        }
        task_id = db_manager.add_task(task)
        task["id"] = task_id

        # Add task to queue
        task_queue.put(task)
        logger.info("Task added to queue: %s", task_id)

        return {
            "message": "Task added to the queue , Response will send as a Mail within 1 Min",
            "task_id": task_id,
        }
    except Exception as e:
        logger.exception("Error adding task to queue: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
