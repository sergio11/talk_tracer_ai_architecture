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
with DAG('meeting_video_summarization_dag', default_args=default_args, default_view="graph", schedule_interval=None, catchup=False) as dag:
    # Import the necessary operators from external modules
    operators_module = importlib.import_module('operators.download_and_transcribe_operator')
    DownloadAndTranscribeOperator = operators_module.DownloadAndTranscribeOperator
    operators_module = importlib.import_module('operators.generate_open_ai_summary_operator')
    GenerateOpenAISummaryOperator = operators_module.GenerateOpenAISummaryOperator

    # Define the tasks for each operator
    # Download and Transcribe Task
    download_and_transcribe = DownloadAndTranscribeOperator(
        task_id='download_and_transcribe',
        video_url="URL_DEL_VIDEO_DE_YOUTUBE",
        provide_context=True,
    )

    # Generate OpenAI Summary Task
    generate_openai_summary = GenerateOpenAISummaryOperator(
        task_id='generate_openai_summary',
        api_key='YOUR_OPENAI_API_KEY',
        engine='text-davinci-002',
        max_tokens=50,
        prompt="Prompt here",
        provide_context=True,
    )

    # Define task dependencies by chaining the tasks in sequence
    download_and_transcribe >> generate_openai_summary
