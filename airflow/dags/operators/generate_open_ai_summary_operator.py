from operators.base_custom_operator import BaseCustomOperator
import openai
from airflow.utils.decorators import apply_defaults

class GenerateOpenAISummaryOperator(BaseCustomOperator):
    
    @apply_defaults
    def __init__(self, api_key, engine, max_tokens, prompt, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = api_key
        self.engine = engine
        self.max_tokens = max_tokens
        self.prompt = prompt

    def execute(self, context):
        self._log_to_mongodb(f"Starting execution of GenerateOpenAISummaryOperator", context, "INFO")
