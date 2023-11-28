import tempfile
from bson import ObjectId
from operators.base_custom_operator import BaseCustomOperator
from airflow.utils.decorators import apply_defaults
from moviepy.editor import AudioFileClip
import speech_recognition as sr
import spacy

class VideoTranscriptionOperator(BaseCustomOperator):
    """
    An operator that performs audio transcription for video meetings.

    This operator retrieves meeting information from MongoDB, downloads the corresponding audio file from MinIO,
    transcribes the audio content, and updates the MongoDB document with the transcribed text.

    Inherits from BaseCustomOperator.
    """
    @apply_defaults
    def __init__(
        self,
        *args, **kwargs
    ):
        super().__init__(*args, **kwargs)


    def _initialize_recognizer(self):
        """
        Initializes and returns a Recognizer object from the speech_recognition library.

        Returns:
        Recognizer: Initialized Recognizer object.
        """
        return sr.Recognizer()

    def _get_audio_duration(self, audio_file_path):
        """
        Obtains the duration of the audio file in seconds.

        Args:
        audio_file_path (str): Path to the audio file.

        Returns:
        float: Duration of the audio in seconds.
        """
        audio = AudioFileClip(audio_file_path)
        return audio.duration

    def _download_file_from_minio(self, context, minio_client, file_path):
        """
        Downloads a file from MinIO to a temporary file.

        Args:
        context (dict): The execution context.
        minio_client: MinIO client instance.
        file_path (str): Path to the file in MinIO.

        Returns:
        str: Path to the downloaded temporary file.
        """
        with tempfile.NamedTemporaryFile(suffix='.mp4') as temp_file:
            temp_file_path = temp_file.name
            minio_client.fget_object(
                bucket_name=self.minio_bucket_name,
                object_name=file_path,
                file_path=temp_file_path
            )
            self._log_to_mongodb(f"Downloaded file '{file_path}' from MinIO to temporary file", context, "INFO")
            return temp_file_path
        
    def _update_transcribed_text(self, context, meeting_id, combined_text):
        """
        Updates the 'transcribed_text' field in MongoDB for a given meeting ID.

        Args:
        context (dict): The execution context.
        meeting_id (str): The ID of the meeting.
        combined_text (str): The transcribed text to update.

        Returns:
        None
        """
        collection = self._get_mongodb_collection()
        update_result = collection.update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"transcribed_text": combined_text}}
        )

        if update_result.modified_count == 1:
            self._log_to_mongodb(f"Updated document with meeting_id {meeting_id} in MongoDB", context, "INFO")
        else:
            self._log_to_mongodb(f"Document with meeting_id {meeting_id} not updated in MongoDB", context, "WARNING")

    def _transcribe_segment(self, context, recognizer, audio_segment):
        """
        Transcribes an audio segment using the provided recognizer.

        Args:
        context (dict): The execution context.
        recognizer: Speech recognizer instance.
        audio_segment: Audio segment to transcribe.

        Returns:
        str: Transcribed text.
        """
        try:
            text = recognizer.recognize_google(audio_segment, language='en-US')
            return text
        except sr.UnknownValueError as e:
            self._log_to_mongodb(f"This segment could not be trascripted #{e}", context, "ERROR")
        except sr.RequestError as e:
            self._log_to_mongodb(f"An error ocurred when trying to transcript the segment #{e}", context, "ERROR")

    def _transcribe_audio(self, context, audio_file_path):
        """
        Transcribes the entire audio file.

        Args:
        context (dict): The execution context.
        audio_file_path (str): Path to the audio file.

        Returns:
        str: Combined transcribed text from all segments.
        """
        recognizer = self._initialize_recognizer()
        segment_duration = 120
        audio_duration = self._get_audio_duration(audio_file_path)
        num_segments = int(audio_duration / segment_duration) + 1
        transcribed_texts = []
        with sr.AudioFile(audio_file_path) as source:
            for i in range(num_segments):
                start_time = i * segment_duration
                end_time = min((i + 1) * segment_duration, audio_duration)
                audio_segment = recognizer.record(source, offset=start_time, duration=end_time - start_time)
                self._log_to_mongodb(f"Transcribing segment {i + 1} of {num_segments}...", context, "INFO")
                text = self._transcribe_segment(context, recognizer, audio_segment)
                if text:
                    transcribed_texts.append(text)

        combined_text = ' '.join(transcribed_texts)
        return combined_text
    
    def _correct_punctuation_with_spacy(self, transcript):
        """
        Corrects punctuation in the transcription using spaCy.

        Args:
        - transcript (str): The transcript text to be corrected.

        Returns:
        - str: The corrected transcript with appropriate punctuation.
        """
        nlp = spacy.load("en_core_web_sm")
        # Process the text with spaCy
        doc = nlp(transcript)

        # Iterate through the text to find sentences without punctuation and correct them
        corrected_transcript = ''
        for i, token in enumerate(doc[:-1]):
            # Concatenate each word or space to the corrected text
            if token.is_space:
                corrected_transcript += token.text
                continue

            corrected_transcript += token.text

            # Check if the next token is an entity and should be preceded by a period
            if doc[i+1].ent_iob == 2 and doc[i+1].text[0].isupper() and doc[i+1].text not in {'.', ',', '!', '?', ';', ':', '-', '/'}:
                # Add a period at the end of the sentence
                corrected_transcript += '.'

            # Add a space between words, except when the next token is punctuation
            if doc[i+1].text not in {'.', ',', '!', '?', ';', ':', '-', '/'}:
                corrected_transcript += ' '

        # Add the last word or space
        corrected_transcript += doc[-1].text

        return corrected_transcript


    def execute(self, context):
        """
        Executes the VideoTranscriptionOperator.

        Args:
        context (dict): The execution context.

        Returns:
        dict: A dictionary containing the meeting_id.
        """
        # Log the start of the execution
        self._log_to_mongodb(f"Starting execution of VideoTranscriptionOperator", context, "INFO")

        # Get the configuration passed to the DAG from the execution context
        dag_run_conf = context['dag_run'].conf

        # Get the meeting_id from the configuration
        meeting_id = dag_run_conf['meeting_id']
        self._log_to_mongodb(f"Received meeting_id: {meeting_id}", context, "INFO")

        meeting_info = self._get_meeting_info(context, meeting_id)

        self._log_to_mongodb(f"Retrieved meeting from MongoDB: {meeting_id}", context, "INFO")

        # Extract video_id from meeting information
        video_id = meeting_info.get('video_id')
        if not video_id:
            error_message = f"No 'video_id' found in the meeting information."
            self._log_to_mongodb(error_message, context, "ERROR")
            raise Exception(error_message)

        self._log_to_mongodb(f"Received video_id: {video_id}", context, "INFO")

        # Get MinIO client
        minio_client = self._get_minio_client(context)

        try:
            file_path = f"{video_id}.mp4"
            self._log_to_mongodb(f"Attempting to download file '{file_path}' from MinIO...", context, "INFO")
            
            # Download the audio file from MinIO and get the file path
            audio_file_path = self._download_file_from_minio(context, minio_client, file_path)

            # Transcribe the audio file and combine transcribed texts
            combined_text = self._transcribe_audio(context, audio_file_path)

            # Correct punctuation in the combined text using spaCy
            corrected_text = self._correct_punctuation_with_spacy(combined_text)

            # Update the transcribed_text field in MongoDB for the meeting_id document
            self._update_transcribed_text(context, meeting_id, corrected_text)

            return {"meeting_id": str(meeting_id)}

        except Exception as e:
            # Handle exceptions and log errors
            error_message = f"Error downloading file '{file_path}' from MinIO: {e}"
            self._log_to_mongodb(error_message, context, "ERROR")
            raise Exception(error_message)

