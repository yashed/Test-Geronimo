# Use an official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /apps/geronimo

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Create a new user with UID 10016 for security
RUN addgroup --gid 10016 choreo && \
    adduser --disabled-password --no-create-home --uid 10016 --ingroup choreo choreouser

# Set the user for the container
USER 10016

# Expose the FastAPI port (8000)
EXPOSE 8000

# Mount the database directory as a volume
VOLUME ["/tmp"]

# Command to run the FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]

