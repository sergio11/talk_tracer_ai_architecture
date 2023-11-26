from datetime import datetime
from airflow import DAG
import importlib
import os

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'logging_level': 'INFO'
}

# Create the DAG with the specified default arguments
with DAG('talk_tracer_dag', default_args=default_args, default_view="graph", schedule_interval=None, catchup=False) as dag:
    # Import the necessary operators from external modules
    operators_module = importlib.import_module('operators.video_transcription_operator')
    VideoTranscriptionOperator = operators_module.VideoTranscriptionOperator
    operators_module = importlib.import_module('operators.transcription_language_detection_operator')
    TranscriptionLanguageDetectionOperator = operators_module.TranscriptionLanguageDetectionOperator
    operators_module = importlib.import_module('operators.transcription_translation_operator')
    TranscriptionTranslationOperator = operators_module.TranscriptionTranslationOperator
    operators_module = importlib.import_module('operators.generate_open_ai_summary_operator')
    GenerateOpenAISummaryOperator = operators_module.GenerateOpenAISummaryOperator

    # Define the task instances for each operator

    # Task to transcribe the video and store the transcription
    video_transcription_task = VideoTranscriptionOperator(
        task_id='video_transcription_task',
        mongo_uri=os.environ.get("MONGO_URI"),
        mongo_db=os.environ.get("MONGO_DB"),
        mongo_db_collection=os.environ.get("MONGO_DB_COLLECTION"),
        minio_endpoint=os.environ.get("MINIO_ENDPOINT"),
        minio_access_key=os.environ.get("MINIO_ACCESS_KEY"),
        minio_secret_key=os.environ.get("MINIO_SECRET_KEY"),
        minio_bucket_name=os.environ.get("MINIO_BUCKET_NAME")
    )

    # Task to detect language from the transcription and store the result
    language_detection_task = TranscriptionLanguageDetectionOperator(
        task_id='language_detection_task',
        mongo_uri=os.environ.get("MONGO_URI"),
        mongo_db=os.environ.get("MONGO_DB"),
        mongo_db_collection=os.environ.get("MONGO_DB_COLLECTION"),
        minio_endpoint=os.environ.get("MINIO_ENDPOINT"),
        minio_access_key=os.environ.get("MINIO_ACCESS_KEY"),
        minio_secret_key=os.environ.get("MINIO_SECRET_KEY"),
        minio_bucket_name=os.environ.get("MINIO_BUCKET_NAME")
    )

    # Task to translate the transcription into another language and store the translation
    translation_task = TranscriptionTranslationOperator(
        task_id='translation_task',
        mongo_uri=os.environ.get("MONGO_URI"),
        mongo_db=os.environ.get("MONGO_DB"),
        mongo_db_collection=os.environ.get("MONGO_DB_COLLECTION"),
        minio_endpoint=os.environ.get("MINIO_ENDPOINT"),
        minio_access_key=os.environ.get("MINIO_ACCESS_KEY"),
        minio_secret_key=os.environ.get("MINIO_SECRET_KEY"),
        minio_bucket_name=os.environ.get("MINIO_BUCKET_NAME")
    )

    # Task to generate a summary of the transcription using OpenAI and store the summary
    openai_summary_task = GenerateOpenAISummaryOperator(
        task_id='openai_summary_task',
        mongo_uri=os.environ.get("MONGO_URI"),
        mongo_db=os.environ.get("MONGO_DB"),
        mongo_db_collection=os.environ.get("MONGO_DB_COLLECTION"),
        minio_endpoint=os.environ.get("MINIO_ENDPOINT"),
        minio_access_key=os.environ.get("MINIO_ACCESS_KEY"),
        minio_secret_key=os.environ.get("MINIO_SECRET_KEY"),
        minio_bucket_name=os.environ.get("MINIO_BUCKET_NAME")
    )

    # Define task dependencies by chaining the tasks in sequence
    video_transcription_task >> language_detection_task >> translation_task >> openai_summary_task
