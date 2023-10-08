from flask import Flask, request, jsonify
import requests
from pymongo import MongoClient
import os

# Configure MongoDB connection
MONGO_URI = os.environ.get("MONGO_URI")
MONGO_DB = os.environ.get("MONGO_DB")
MONGO_COLLECTION = os.environ.get("MONGO_DB_COLLECTION")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB]
mi_coleccion = db[MONGO_COLLECTION]

# Configure Airflow and Zoom variables
AIRFLOW_DAG_ID = os.environ.get("AIRFLOW_DAG_ID")
AIRFLOW_API_URL = os.environ.get("AIRFLOW_API_URL")
ZOOM_API_SECRET = os.environ.get("ZOOM_API_SECRET")

app = Flask(__name__)

@app.route('/webhook/zoom', methods=['POST'])
def zoom_webhook():
    try:
        data = request.json  # Receive data from the Zoom request
        recording_url = data['payload']['object']['recording_url']
        meeting_info = {
            'meeting_id': data['payload']['object']['id'],
            'meeting_topic': data['payload']['object']['topic'],
            'start_time': data['payload']['object']['start_time'],
            'end_time': data['payload']['object']['end_time'],
            'duration': data['payload']['object']['duration'],
            'recording_url': recording_url,
        }

        # Save meeting information to MongoDB
        mi_coleccion.insert_one(meeting_info)

        # Configure the request to initiate the DAG in Apache Airflow
        airflow_dag_url = f"{AIRFLOW_API_URL}/dags/{AIRFLOW_DAG_ID}/dagRuns"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {ZOOM_API_SECRET}'  # Replace with your Zoom authentication token
        }
        data = {
            'conf': {
                'video_url': recording_url  # Pass the video URL as configuration to the DAG
            }
        }
        
        # Start the DAG in Apache Airflow
        response = requests.post(airflow_dag_url, json=data, headers=headers)

        if response.status_code == 200:
            return jsonify({'message': 'DAG execution initiated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to initiate DAG execution'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)