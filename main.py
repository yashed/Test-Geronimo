from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import lanchain_helpr as lh

app = FastAPI()


# Enable CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define the request body schema using Pydantic
class UserRequest(BaseModel):
    name: str
    company: str
    country: str
    position: str
    interest: str


# Define root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to the API"}


# Define a test endpoint
@app.get("/test")
def test_endpoint():
    return {"message": "This is a test endpoint"}


# Define an endpoint
@app.post("/generate_data/")
async def generate_data(user: UserRequest):
    name = user.name
    company = user.company
    position = user.position
    country = user.country

    # Generate the data using the existing helper function
    response = lh.generate_data(name, company, position, country)

    if not response:
        raise HTTPException(status_code=404, detail="Data generation failed")
    else:

        return {
            "professional_summary": response.get(
                "professional_summary", "No summary available"
            ),
            "social_media_links": response.get(
                "social_media_links", "No social media links found."
            ),
            "company_summary": response.get(
                "company_summary", "No company summary available"
            ),
            "company_competitors": response.get(
                "company_competitors", "No competitors found"
            ),
            "additional_insights": response.get(
                "additional_insights", "No additional insights available."
            ),
        }
