from operators.base_custom_operator import BaseCustomOperator
#from googletrans import Translator
from airflow.utils.decorators import apply_defaults

class TranscriptionTranslationOperator(BaseCustomOperator):
    
    @apply_defaults
    def __init__(self, target_languages, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_languages = target_languages

    def execute(self, context):
        self._log_to_mongodb(f"Starting execution of TranscriptionTranslationOperator", context, "INFO")
