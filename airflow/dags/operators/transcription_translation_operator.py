from bson import ObjectId
from operators.base_custom_operator import BaseCustomOperator
from googletrans import Translator
from airflow.utils.decorators import apply_defaults

class TranscriptionTranslationOperator(BaseCustomOperator):
    """
    Custom Airflow Operator for translating transcribed text into multiple target languages.

    This operator translates transcribed text into different target languages using the Google Translate API 
    and updates the MongoDB document with the translated text for each target language.
    """
    @apply_defaults
    def __init__(self, target_languages, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_languages = target_languages

    def _translate_text(self, text, target_language):
        """
        Translates the given text to the specified target language.

        Args:
        - text (str): The text to be translated.
        - target_language (str): The language code for the target language.

        Returns:
        A string containing the translated text.
        """
        translator = Translator()
        translation = translator.translate(text, dest=target_language)
        return translation.text
    
    def _update_translations_in_mongodb(self, context, meeting_id, translations):
        """
        Updates the translations in the MongoDB document corresponding to the meeting_id.

        Args:
        - context (dict): The execution context.
        - meeting_id (str): The ID of the meeting/document in MongoDB.
        - translations (dict): A dictionary containing translations for different languages.

        The 'translations' dictionary should have the structure:
        {
            'language_code_1': 'translated_text_1',
            'language_code_2': 'translated_text_2',
            ...
        }
        """
        collection = self._get_mongodb_collection()
        update_result = collection.update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"translations": translations}}
        )

        if update_result.modified_count == 1:
            self._log_to_mongodb(f"Updated translations for document with meeting_id {meeting_id} in MongoDB", context, "INFO")
        else:
            self._log_to_mongodb(f"Document with meeting_id {meeting_id} not updated with translations in MongoDB", context, "WARNING")

    def execute(self, context):
        self._log_to_mongodb(f"Starting execution of TranscriptionTranslationOperator", context, "INFO")

        # Get the meeting_id from the configuration
        meeting_id = context['dag_run'].conf.get('meeting_id')
        self._log_to_mongodb(f"Received meeting_id: {meeting_id}", context, "INFO")

        transcribed_text = self._get_transcribed_text_from_context(context, meeting_id)

        # Translate the transcribed text for each target language
        translated_texts = {}
        for language in self.target_languages:
            translated_text = self._translate_text(transcribed_text, language)
            translated_texts[language] = translated_text
            self._log_to_mongodb(f"Translated text to {language} completed", context, "INFO")

        # Update the translations in the MongoDB document
        self._update_translations_in_mongodb(context, meeting_id, translated_texts)
        self._log_to_mongodb(f"Updated translations in MongoDB for meeting_id: {meeting_id}", context, "INFO")
        
        return {"meeting_id": str(meeting_id)}
