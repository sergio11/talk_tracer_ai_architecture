from langdetect import detect
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

class LanguageDetectionOperator(BaseOperator):
    @apply_defaults
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, context):
        try:
            transcript = context['ti'].xcom_pull(task_ids='transcribe_task', key='transcript')

            # Utiliza la biblioteca langdetect para detectar el idioma
            detected_language = detect(transcript)

            # Almacena el idioma detectado en el contexto
            context['ti'].xcom_push(key='detected_language', value=detected_language)

        except Exception as e:
            self.log.error(f"Error: {str(e)}")
            raise e
