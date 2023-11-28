from bson import ObjectId
from operators.base_custom_operator import BaseCustomOperator
from airflow.utils.decorators import apply_defaults
from transformers import pipeline

class GenerateSummaryOperator(BaseCustomOperator):
    
    @apply_defaults
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, context):
        self._log_to_mongodb(f"Starting execution of GenerateSummaryOperator", context, "INFO")
        # Get the configuration passed to the DAG from the execution context
        dag_run_conf = context['dag_run'].conf

        # Get the meeting_id from the configuration
        meeting_id = dag_run_conf['meeting_id']
        self._log_to_mongodb(f"Received meeting_id: {meeting_id}", context, "INFO")

        meeting_info = self._get_meeting_info(context, meeting_id)

        # Extract transcribed_text from meeting information
        transcribed_text = meeting_info.get('transcribed_text')
        if not transcribed_text:
            error_message = f"No 'transcribed_text' found in the meeting information."
            self._log_to_mongodb(error_message, context, "ERROR")
            raise Exception(error_message)

        summarizer = pipeline("summarization", model="Falconsai/text_summarization")

        # Set the maximum length of the summary based on the length of the input text
        max_summary_length = max(30, min(230, int(len(transcribed_text) * 0.5)))

        # Generate the summary using the Hugging Face summary model with the maximum length set dynamically
        summary = summarizer(transcribed_text, max_length=max_summary_length, min_length=30, do_sample=False)[0]['summary_text']

        collection = self._get_mongodb_collection()
        update_result = collection.update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"summary": summary}}
        )

        if update_result.modified_count == 1:
            self._log_to_mongodb(f"Updated document with meeting_id {meeting_id} in MongoDB", context, "INFO")
        else:
            self._log_to_mongodb(f"Document with meeting_id {meeting_id} not updated in MongoDB", context, "WARNING")

        return {"meeting_id": str(meeting_id)}
