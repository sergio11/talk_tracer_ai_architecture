from googletrans import Translator
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

class TranslationOperator(BaseOperator):
    @apply_defaults
    def __init__(self, target_languages, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_languages = target_languages

    def execute(self, context):
        try:
            transcript = context['ti'].xcom_pull(task_ids='transcribe_task', key='transcript')
            detected_language = context['ti'].xcom_pull(task_ids='language_detection_task', key='detected_language')

            # Inicializa el traductor de Google
            translator = Translator()

            translations = {}
            for target_language in self.target_languages:
                # Solo realiza traducciones para idiomas diferentes al idioma detectado
                if target_language.lower() != detected_language.lower():
                    translation = translator.translate(transcript, src=detected_language, dest=target_language)
                    translations[target_language] = translation.text

            # Almacena las traducciones en el contexto
            context['ti'].xcom_push(key='translations', value=translations)

            # Almacena las traducciones en el documento BSON de MongoDB
            meeting_info_id = context['ti'].xcom_pull(task_ids='mongodb_store_task', key='meeting_info_id')
            db[MONGO_COLLECTION].update_one({"_id": ObjectId(meeting_info_id)},
                                            {"$set": {"translations": translations}})

        except Exception as e:
            self.log.error(f"Error: {str(e)}")
            raise e
