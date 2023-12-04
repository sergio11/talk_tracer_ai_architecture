from bson import ObjectId
from operators.base_custom_operator import BaseCustomOperator
from airflow.utils.decorators import apply_defaults
from transformers import pipeline

class GenerateSummaryOperator(BaseCustomOperator):
    
    """
    Operator responsible for generating a summary based on meeting transcribed text
    using a summarization model and storing it in the BSON document in MongoDB.
    """
    @apply_defaults
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    
    def _save_summary_to_bson(self, context, meeting_id, summary):
        """
        Saves the generated summary to the BSON document in MongoDB.

        Args:
        - context: The execution context.
        - meeting_id: The ID of the meeting.
        - summary: The summary text to be saved.
        """
        collection = self._get_mongodb_collection()
        update_result = collection.update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"summary": summary}}
        )

        if update_result.modified_count == 1:
            self._log_to_mongodb(f"Updated document with meeting_id {meeting_id} in MongoDB", context, "INFO")
        else:
            error_message = f"Document with meeting_id {meeting_id} not updated in MongoDB"
            self._log_to_mongodb(error_message, context, "WARNING")
            raise Exception(error_message)

    def execute(self, context):
        """
        The main execution method for generating a summary.

        Retrieves the meeting information, generates a summary using a summarization model,
        and saves the summary to the BSON document in MongoDB.
        """
        self._log_to_mongodb(f"Starting execution of GenerateSummaryOperator", context, "INFO")
        # Get the configuration passed to the DAG from the execution context
        dag_run_conf = context['dag_run'].conf
        
        # Get the meeting_id from the configuration
        meeting_id = dag_run_conf['meeting_id']
        self._log_to_mongodb(f"Received meeting_id: {meeting_id}", context, "INFO")

        meeting_info = self._get_meeting_info(context, meeting_id)
        self._log_to_mongodb(f"Retrieved meeting from MongoDB: {meeting_id}", context, "INFO")

        transcribed_text = self._get_transcribed_text_from_meeting_info(context, meeting_info)

        summarizer = pipeline("summarization", model="Falconsai/text_summarization")

        # Set the maximum length of the summary based on the length of the input text
        max_summary_length = max(30, min(230, int(len(transcribed_text) * 0.5)))

        self._log_to_mongodb(f"Generating summary using the summarization model...", context, "INFO")
        # Generate the summary using the Hugging Face summary model with the maximum length set dynamically
        summary = summarizer(transcribed_text, max_length=max_summary_length, min_length=30, do_sample=False)[0]['summary_text']

        self._log_to_mongodb(f"Saving the summary to the BSON document...", context, "INFO")
        # Save the summary to the BSON document
        self._save_summary_to_bson(context, meeting_id, summary)

        self._log_to_mongodb(f"Execution of GenerateSummaryOperator completed.", context, "INFO")

        return {"meeting_id": str(meeting_id)}

