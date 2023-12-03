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
import locale

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base prefix for application routes
BASE_URL_PREFIX = "/meetings"

ALLOWED_EXTENSIONS = {'wav'}

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

# Check if the filename has a valid extension present in the ALLOWED_EXTENSIONS set
def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to save the uploaded file locally
def _save_file_locally(video_file):
    # Create a temporary file to store the uploaded video
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file_path = temp_file.name
    # Save the uploaded video to the temporary file
    video_file.save(temp_file_path)
    logger.info(f"File saved locally: {temp_file_path}")
    return temp_file_path

# Function to handle MinIO storage for the file
def _handle_minio_storage(file, temp_file_path):
    # Get the file extension from the uploaded file
    file_extension = os.path.splitext(file.filename)[1]
    # Generate a unique name for the file in MinIO using UUID and the file extension
    unique_filename = f"{str(uuid.uuid4())}{file_extension}"
    logger.info(f"Storing file in MinIO with name: {unique_filename}")
    # Store the video file in MinIO
    store_file_in_minio(
        minio_endpoint=MINIO_ENDPOINT,
        minio_access_key=MINIO_ACCESS_KEY,
        minio_secret_key=MINIO_SECRET_KEY,
        minio_bucket_name=MINIO_BUCKET_NAME,
        local_file_path=temp_file_path,
        minio_object_name=unique_filename
    )
    logger.info("File stored in MinIO successfully")
    return unique_filename

# Function to save metadata about the video in MongoDB
def _save_metadata(title, description, language, minio_object_name):
    # Generate a timestamp for the video upload
    timestamp = datetime.now()
    # Create metadata to be stored in MongoDB
    metadata = {
        "title": title,
        "description": description,
        "language": language,
        "file_id": minio_object_name,
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


# Function to validate the language format
def _validate_language_format(language):
    """
    Validates the format of the language parameter.

    Args:
    - language (str): The language parameter to be validated.

    Returns:
    - is_valid (bool): Indicates if the language format is valid.
    - error_message (str or None): Error message if the format is invalid, else None.
    """
    language_parts = language.split('-')
    if len(language_parts) != 2:
        return False, "Invalid language format. Should be in the format 'en-US'"

    language_code, country_code = language_parts

    try:
        # Try to set the locale configuration to validate language and country code
        locale.setlocale(locale.LC_ALL, (language_code, country_code))
    except locale.Error:
        return False, "Invalid language or country code"

    return True, None

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

# Endpoint to receive the audio file, title, and description
@app.route(f"{BASE_URL_PREFIX}/create", methods=['POST'])
def create_meeting():
    try:
        # Check if the audio_file part is in the request
        if 'audio_file' not in request.files:
            logger.error("No audio file part received")
            return _create_response("Error", 400, "No audio file part")

        audio_file = request.files['audio_file']
        title = request.form.get('title')
        description = request.form.get('description')
        language = request.form.get('language')

        if audio_file.filename == '':
            logger.error("No audio file selected")
            return _create_response("Error", 400, "No audio file file")
        
        if not _allowed_file(audio_file.filename):
            logger.error("Invalid audio file format. Only WAV files are allowed.")
            return _create_response("Error", 400, "Invalid audio file format. Only WAV files are allowed.")
        
        if not all([title, description, language]):
            logger.error("Missing parameters")
            return _create_response("Error", 400, "Missing parameters: title, description, or language")

        # Validate the language format
        is_valid_language, error_message = _validate_language_format(language)
        if not is_valid_language:
            logger.error(error_message)
            return _create_response("Error", 400, error_message)

        logger.info(f"Received file: {audio_file.filename}")
        logger.info(f"Title: {title}, Description: {description}")

        # Save the file locally
        temp_file_path = _save_file_locally(audio_file)

        # Store the file in MinIO
        minio_object_name = _handle_minio_storage(audio_file, temp_file_path)

        # Save metadata about the video in MongoDB
        meeting_id = _save_metadata(title, description, language, minio_object_name)

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