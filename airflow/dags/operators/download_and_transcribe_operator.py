import os
import speech_recognition as sr
from pytube import YouTube
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
import logging

class DownloadAndTranscribeOperator(BaseOperator):
    @apply_defaults
    def __init__(self, video_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.video_url = video_url

    def execute(self, context):
        try:
            # Download audio from YouTube video
            yt = YouTube(self.video_url)
            audio_stream = yt.streams.filter(only_audio=True).first()
            audio_file = f"{yt.title}.mp3"
            audio_stream.download(filename=audio_file)

            # Convert audio to text
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)

            # Store the text in a context variable for later use
            context['ti'].xcom_push(key='transcript', value=text)

            # Remove the downloaded audio file
            os.remove(audio_file)
        except Exception as e:
            # Log any errors that occur during execution
            logging.error(f"Error: {str(e)}")
            raise e
