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
    operators_module = importlib.import_module('operators.transcription_operator')
    TranscriptionOperator = operators_module.TranscriptionOperator
    operators_module = importlib.import_module('operators.natural_language_proccessing_operator')
    NaturalLanguageProccessingOperator = operators_module.NaturalLanguageProccessingOperator
    operators_module = importlib.import_module('operators.generate_summary_operator')
    GenerateSummaryOperator = operators_module.GenerateSummaryOperator
    operators_module = importlib.import_module('operators.translation_operator')
    TranslationOperator = operators_module.TranslationOperator
    operators_module = importlib.import_module('operators.index_to_elasticsearch_operator')
    IndexToElasticsearchOperator = operators_module.IndexToElasticsearchOperator

    # Define the task instances for each operator

    # Task to transcribe the audio and store the transcription
    transcription_task = TranscriptionOperator(
        task_id='transcription_task',
        audio_segment_duration=os.environ.get("AUDIO_SEGMENT_DURATION"),
        mongo_uri=os.environ.get("MONGO_URI"),
        mongo_db=os.environ.get("MONGO_DB"),
        mongo_db_collection=os.environ.get("MONGO_DB_COLLECTION"),
        minio_endpoint=os.environ.get("MINIO_ENDPOINT"),
        minio_access_key=os.environ.get("MINIO_ACCESS_KEY"),
        minio_secret_key=os.environ.get("MINIO_SECRET_KEY"),
        minio_bucket_name=os.environ.get("MINIO_BUCKET_NAME")
    )

    # Task to proccess the text using NLP techniques
    nlp_task = NaturalLanguageProccessingOperator(
        task_id='nlp_task',
        mongo_uri=os.environ.get("MONGO_URI"),
        mongo_db=os.environ.get("MONGO_DB"),
        mongo_db_collection=os.environ.get("MONGO_DB_COLLECTION"),
        minio_endpoint=os.environ.get("MINIO_ENDPOINT"),
        minio_access_key=os.environ.get("MINIO_ACCESS_KEY"),
        minio_secret_key=os.environ.get("MINIO_SECRET_KEY"),
        minio_bucket_name=os.environ.get("MINIO_BUCKET_NAME")
    )

    # Task to generate a summary of the transcription and store it
    summary_task = GenerateSummaryOperator(
        task_id='summary_task',
        mongo_uri=os.environ.get("MONGO_URI"),
        mongo_db=os.environ.get("MONGO_DB"),
        mongo_db_collection=os.environ.get("MONGO_DB_COLLECTION"),
        minio_endpoint=os.environ.get("MINIO_ENDPOINT"),
        minio_access_key=os.environ.get("MINIO_ACCESS_KEY"),
        minio_secret_key=os.environ.get("MINIO_SECRET_KEY"),
        minio_bucket_name=os.environ.get("MINIO_BUCKET_NAME")
    )

    # Task to translate the transcription and summary into another language and store the translation
    translation_task = TranslationOperator(
        task_id='translation_task',
        mongo_uri=os.environ.get("MONGO_URI"),
        mongo_db=os.environ.get("MONGO_DB"),
        mongo_db_collection=os.environ.get("MONGO_DB_COLLECTION"),
        minio_endpoint=os.environ.get("MINIO_ENDPOINT"),
        minio_access_key=os.environ.get("MINIO_ACCESS_KEY"),
        minio_secret_key=os.environ.get("MINIO_SECRET_KEY"),
        minio_bucket_name=os.environ.get("MINIO_BUCKET_NAME"),
        target_languages=os.environ.get("TRANSLATION_TARGET_LANGUAGE").split(",")
    )

    index_to_elasticsearch_operator = IndexToElasticsearchOperator(
        task_id='index_to_elasticsearch_operator',
        mongo_uri=os.environ.get("MONGO_URI"),
        mongo_db=os.environ.get("MONGO_DB"),
        mongo_db_collection=os.environ.get("MONGO_DB_COLLECTION"),
        minio_endpoint=os.environ.get("MINIO_ENDPOINT"),
        minio_access_key=os.environ.get("MINIO_ACCESS_KEY"),
        minio_secret_key=os.environ.get("MINIO_SECRET_KEY"),
        minio_bucket_name=os.environ.get("MINIO_BUCKET_NAME"),
        elasticsearch_host=os.environ.get("ELASTICSEARCH_HOST"),
        elasticsearch_index=os.environ.get("ELASTICSEARCH_INDEX")
    )

    # Define task dependencies by chaining the tasks in sequence
    transcription_task >> nlp_task >> summary_task >> translation_task >> index_to_elasticsearch_operator
