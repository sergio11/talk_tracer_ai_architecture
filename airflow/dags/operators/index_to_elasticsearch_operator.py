from elasticsearch import Elasticsearch
from airflow.utils.decorators import apply_defaults
from operators.base_custom_operator import BaseCustomOperator
from bson import ObjectId
from datetime import datetime

class IndexToElasticsearchOperator(BaseCustomOperator):

    """
    Custom operator to index meeting information to Elasticsearch and update MongoDB.

    Args:
    - elasticsearch_host (str): The Elasticsearch server's host.
    - elasticsearch_index (str): The name of the Elasticsearch index.
    """
    @apply_defaults
    def __init__(
        self, 
        elasticsearch_host,
        elasticsearch_index,
        *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.elasticsearch_host = elasticsearch_host
        self.elasticsearch_index = elasticsearch_index


    def _update_meeting_in_mongodb(self, context, meeting_id):
        """
        Updates a meeting document in MongoDB with the current timestamp.

        Args:
        - context: Contextual information or metadata about the update operation.
        - meeting_id (str): The ID of the meeting document to be updated in MongoDB.

        Raises:
        - Exception: If the document update fails in MongoDB.
        """
        collection = self._get_mongodb_collection()
        update_result = collection.update_one(
            {"_id": ObjectId(meeting_id)},
            {
                "$set": {
                    "indexed_at": datetime.now()
                }
            }
        )
        if update_result.modified_count == 1:
            self._log_to_mongodb(f"Updated document with meeting_id {meeting_id} in MongoDB", context, "INFO")
        else:
            error_message = f"Document with meeting_id {meeting_id} not updated in MongoDB"
            self._log_to_mongodb(error_message, context, "WARNING")
            raise Exception(error_message)
        
    def _index_meeting_info_to_elasticsearch(self, meeting_info):
        """
        Indexes meeting information to Elasticsearch.

        Args:
        - meeting_info (dict): A dictionary containing meeting information.
            Expected keys:
            - 'transcribed_text' (str): The transcribed text from the meeting.
            - 'summary' (str): Summary of the meeting.

        Raises:
        - Exception: If there's an issue indexing meeting information to Elasticsearch.
        """
        es = Elasticsearch(self.elasticsearch_host)
        document = {
            'transcribed_text': meeting_info.get('transcribed_text', ''),
            'summary': meeting_info.get('summary', ''),
        }
        es.index(index=self.elasticsearch_index, doc_type='_doc', body=document)

    def execute(self, context):
        self._log_to_mongodb(f"Starting execution of IndexToElasticsearchOperator", context, "INFO")

       # Get the configuration passed to the DAG from the execution context
        dag_run_conf = context['dag_run'].conf

        # Get the meeting_id from the configuration
        meeting_id = dag_run_conf['meeting_id']
        self._log_to_mongodb(f"Received meeting_id: {meeting_id}", context, "INFO")

        meeting_info = self._get_meeting_info(context, meeting_id)
        self._log_to_mongodb(f"Retrieved meeting from MongoDB: {meeting_id}", context, "INFO")

        # Index the meeting info in Elasticsearch
        self._index_meeting_info_to_elasticsearch(meeting_info)

        # Update the document in MongoDB
        self._update_meeting_in_mongodb(meeting_id)

        return {"meeting_id": str(meeting_id)}

    