import openai
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

class GenerateOpenAISummaryOperator(BaseOperator):
    @apply_defaults
    def __init__(self, api_key, engine, max_tokens, prompt, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = api_key
        self.engine = engine
        self.max_tokens = max_tokens
        self.prompt = prompt

    def execute(self, context):
        try:
            # Set up OpenAI API key
            openai.api_key = self.api_key
            # Generate a summary using OpenAI
            response = openai.Completion.create(
                engine=self.engine,
                prompt=self.prompt,
                max_tokens=self.max_tokens
            )
            summary = response.choices[0].text
            # Store the summary in a context variable for later use
            context['ti'].xcom_push(key='summary', value=summary)
        except Exception as e:
            # Log any errors that occur during execution
            self.log.error(f"Error: {str(e)}")
            raise e
