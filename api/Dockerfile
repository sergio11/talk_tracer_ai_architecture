# Use the official Python image as a base image
FROM python:3.11.6-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt requirements.txt
# Copy the API code into the container
COPY app.py app.py
COPY minio_helpers.py minio_helpers.py

# Install dependencies
RUN pip install -r requirements.txt

# Expose the port where the API will run
EXPOSE 5000

# Run the API with Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]