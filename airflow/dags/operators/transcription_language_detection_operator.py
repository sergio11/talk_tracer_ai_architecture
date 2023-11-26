#from langdetect import detect
from operators.base_custom_operator import BaseCustomOperator
from airflow.utils.decorators import apply_defaults

class TranscriptionLanguageDetectionOperator(BaseCustomOperator):

    @apply_defaults
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, context):
        self._log_to_mongodb(f"Starting execution of TranscriptionLanguageDetectionOperator", context, "INFO")
