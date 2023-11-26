import base64
import datetime
import logging
import tempfile
import uuid
from bson import ObjectId
from flask import Flask, request, jsonify
from pymongo import MongoClient
import os
import requests
from minio_helpers import store_file_in_minio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get MongoDB connection details from environment variables
MONGO_URI = os.environ.get("MONGO_URI")
MONGO_DB = os.environ.get("MONGO_DB")
MONGO_COLLECTION = os.environ.get("MONGO_DB_COLLECTION")

# Get Airflow DAG ID and API URL from environment variables
AIRFLOW_DAG_ID = os.environ.get("AIRFLOW_DAG_ID")
AIRFLOW_API_URL = os.environ.get("AIRFLOW_API_URL")

# MinIO configuration
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT"),
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY"),
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY"),
MINIO_BUCKET_NAME = os.environ.get("MINIO_BUCKET_NAME")

# Get API Executor username and password from environment variables
API_EXECUTOR_USERNAME = os.environ.get("API_EXECUTOR_USERNAME")
API_EXECUTOR_PASSWORD = os.environ.get("API_EXECUTOR_PASSWORD")

# Connect to MongoDB using the provided URI
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB]
db_collection = db[MONGO_COLLECTION]

# Create a Flask application
app = Flask(__name__)

def _create_response(status, code, message, data=None):
    response_data = {
        "status": status,
        "code": code,
        "message": message,
        "data": data
    }
    return jsonify(response_data), code

# Function to save the uploaded file locally
def _save_file_locally(video_file):
    # Create a temporary file to store the uploaded video
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file_path = temp_file.name
    # Save the uploaded video to the temporary file
    video_file.save(temp_file_path)
    logger.info(f"File saved locally: {temp_file_path}")
    return temp_file_path

# Function to handle MinIO storage for the video file
def _handle_minio_storage(title, video_file, temp_file_path):
    # Generate a unique name for the file in MinIO
    minio_object_name = f"{title}_{video_file.filename}"
    logger.info(f"Storing file in MinIO with name: {minio_object_name}")
    # Store the video file in MinIO
    store_file_in_minio(
        minio_endpoint=MINIO_ENDPOINT,
        minio_access_key=MINIO_ACCESS_KEY,
        minio_secret_key=MINIO_SECRET_KEY,
        minio_bucket_name=MINIO_BUCKET_NAME,
        local_file_path=temp_file_path,
        minio_object_name=minio_object_name
    )
    logger.info("File stored in MinIO successfully")
    return minio_object_name

# Function to save metadata about the video in MongoDB
def _save_metadata(title, description, minio_object_name):
    # Generate a timestamp for the video upload
    timestamp = datetime.now()
    # Create metadata to be stored in MongoDB
    metadata = {
        "title": title,
        "description": description,
        "video_id": minio_object_name,
        "timestamp": timestamp,
        "planned": False  # Initial status, not yet planned
    }
    logger.info("Saving metadata in MongoDB")
    # Insert the metadata into the MongoDB collection and retrieve the meeting ID
    meeting_id = db_collection.insert_one(metadata).inserted_id
    logger.info(f"Inserted meeting information into MongoDB with ID: {meeting_id}")
    return meeting_id

# Function to clean up the temporary file
def _cleanup_temp_file(temp_file_path):
    # Delete the temporary file
    os.unlink(temp_file_path)
    logger.info("Temporary file deleted")

# Function to trigger an Airflow DAG execution
def _trigger_airflow_dag(dag_run_conf):
    # Encode API executor's username and password in Base64
    credentials = f"{API_EXECUTOR_USERNAME}:{API_EXECUTOR_PASSWORD}"
    credentials_base64 = base64.b64encode(credentials.encode()).decode()

    # Create headers for the request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {credentials_base64}"
    }

    # Build the URL to trigger the Airflow DAG execution
    airflow_dag_url = f"{AIRFLOW_API_URL}/dags/{AIRFLOW_DAG_ID}/dagRuns"

    # Trigger the Airflow DAG execution by sending a POST request
    response = requests.post(
        airflow_dag_url,
        json=dag_run_conf,
        headers=headers
    )
    return response

# Endpoint to receive the video file, title, and description
@app.route('/upload_video', methods=['POST'])
def upload_video():
    try:
        # Check if the file part is in the request
        if 'file' not in request.files:
            logger.error("No file part received")
            return _create_response("Error", 400, "No file part")

        video_file = request.files['file']
        title = request.form.get('title')
        description = request.form.get('description')

        if video_file.filename == '':
            logger.error("No file selected")
            return _create_response("Error", 400, "No selected file")

        logger.info(f"Received file: {video_file.filename}")
        logger.info(f"Title: {title}, Description: {description}")

        # Save the video file locally
        temp_file_path = _save_file_locally(video_file)

        # Store the video file in MinIO
        minio_object_name = _handle_minio_storage(title, video_file, temp_file_path)

        # Save metadata about the video in MongoDB
        meeting_id = _save_metadata(title, description, minio_object_name)

        # Clean up the temporary file
        _cleanup_temp_file(temp_file_path)

        # Generate a unique DAG run ID
        dag_run_id = str(uuid.uuid4())
        # Calculate the logical date 2 minutes from now
        logical_date = datetime.utcnow() + datetime.timedelta(minutes=2)
        logical_date_str = logical_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        dag_run_conf = {
            "conf": {
                "meeting_id": str(meeting_id),
            },
            "dag_run_id": dag_run_id,  
            "logical_date": logical_date_str,
            "note": f"DAG run ID: {dag_run_id}"
        }

        # Trigger the Airflow DAG execution
        response = _trigger_airflow_dag(dag_run_conf)

        if response.status_code == 200:
            # Update the MongoDB document with "planned" flag and date
            db_collection.update_one(
                {"_id": ObjectId(meeting_id)},
                {"$set": {"planned": True, "planned_date": logical_date_str}}
            )
            logger.info("DAG execution triggered successfully")
            response_data = _create_response("Success", 200, "Meeting generated and scheduled successfully.")
            return response_data
        else:
            # If DAG execution fails, remove the document from MongoDB
            db_collection.delete_one({"_id": ObjectId(meeting_id)})
            logger.error(f"Error triggering DAG execution: {response.text}")
            logger.error(f"HTTP Request Body: {dag_run_conf}")
            response_data = _create_response("Error", response.status_code, "Error triggering DAG execution.")
            return response_data
    except Exception as e:
        logger.error(f"An error occurred while uploading file: {str(e)}")
        return _create_response("Error", 500, "An error occurred during file upload")

@app.errorhandler(Exception)
def handle_error(e):
    logger.error(f"An error occurred: {str(e)}")
    return _create_response("Error", 500, "An internal server error occurred")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)