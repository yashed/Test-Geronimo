import os
import logging
from flask import Flask, request, jsonify, abort
import lanchain_helpr as lh

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Log to console
)
logger = logging.getLogger(__name__)

# Create Flask instance
app = Flask(__name__)

# Log base URL if available from environment
base_url = os.getenv("BASE_URL", "Base URL not set")
logger.info("Base URL of deployed application: %s", base_url)


# CORS Configuration
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# Middleware for 404 errors
@app.errorhandler(404)
def handle_404(error):
    logger.warning("Unhandled endpoint accessed: %s %s", request.method, request.path)
    return (
        jsonify(
            {
                "code": "404",
                "description": "The requested resource is not available.",
                "message": "Not Found",
            }
        ),
        404,
    )


# Define the request body schema
class UserRequest:
    def __init__(self, name, company, country, position, interest):
        self.name = name
        self.company = company
        self.country = country
        self.position = position
        self.interest = interest

    @classmethod
    def from_request(cls, data):
        try:
            return cls(
                name=data["name"],
                company=data["company"],
                country=data["country"],
                position=data["position"],
                interest=data["interest"],
            )
        except KeyError as e:
            logger.error("Missing key in request body: %s", e)
            abort(400, description=f"Missing key: {e}")


logger.info("UserRequest schema defined")


# Define root endpoint
@app.route("/", methods=["GET"])
def read_root():
    logger.info("Root endpoint accessed")
    return jsonify({"message": "Welcome to the API"})


# Define a test endpoint
@app.route("/test", methods=["GET"])
def test_endpoint():
    logger.info("Test endpoint accessed")
    return jsonify({"message": "This is a test endpoint"})


# Define the generate_data endpoint
@app.route("/generate_data/", methods=["POST"])
def generate_data():
    logger.info("Request URL: %s", request.url)

    try:
        data = request.get_json()
        logger.info("Generate data endpoint called with user data: %s", data)
        user = UserRequest.from_request(data)

        # Extract parameters
        name = user.name
        company = user.company
        position = user.position
        country = user.country

        # Generate the data using the existing helper function
        logger.debug("Calling generate_data helper function with inputs")
        response = lh.generate_data(name, company, position, country)

        if not response:
            logger.error("Data generation failed for user: %s", data)
            abort(404, description="Data generation failed")

        logger.info("Data generation successful for user: %s", data)
        return jsonify(
            {
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
        )
    except Exception as e:
        logger.exception("An error occurred while processing the request")
        abort(500, description="Internal server error")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
