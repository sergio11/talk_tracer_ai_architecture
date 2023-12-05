from bson import ObjectId
from operators.base_custom_operator import BaseCustomOperator
from googletrans import Translator
from airflow.utils.decorators import apply_defaults

class TranslationOperator(BaseCustomOperator):
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
        language_code = target_language.split('-')[0]
        translator = Translator()
        translation = translator.translate(text, dest=language_code)
        return translation.text
    
    def _update_translations_in_mongodb(self, context, meeting_id, transcription_translations, summary_translations):
        """
        Updates the translations in the MongoDB document corresponding to the meeting_id.

        Args:
        - context (dict): The execution context.
        - meeting_id (str): The ID of the meeting/document in MongoDB.
        - transcription_translations (dict): A dictionary containing translations for different languages.
        - summary_translations(dict): A dictionary containing translations for different languages.

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
            {
                "$set": {
                    "transcription_translations": transcription_translations,
                    "summary_translations": summary_translations
                }
            }
        )

        if update_result.modified_count == 1:
            self._log_to_mongodb(f"Updated translations for document with meeting_id {meeting_id} in MongoDB", context, "INFO")
        else:
            error_message = f"Document with meeting_id {meeting_id} not updated with translations in MongoDB"
            self._log_to_mongodb(error_message, context, "WARNING")
            raise Exception(error_message)

    def execute(self, context):
        self._log_to_mongodb(f"Starting execution of TranscriptionTranslationOperator", context, "INFO")

        # Get the meeting_id from the configuration
        meeting_id = context['dag_run'].conf.get('meeting_id')
        self._log_to_mongodb(f"Received meeting_id: {meeting_id}", context, "INFO")

        meeting_info = self._get_meeting_info(context, meeting_id)
        transcribed_text = self._get_transcribed_text_from_meeting_info(context, meeting_info)
        original_language = self._get_language_from_meeting_info(context, meeting_info)
        summary = self._get_summary_from_meeting_info(context, meeting_info)

        # Translate the transcribed text and summary for each target language except the original language
        translated_texts = {}
        translated_summaries = {}
        for language in self.target_languages:
            if language != original_language:
                translated_text = self._translate_text(transcribed_text, language)
                translated_texts[language] = translated_text
                self._log_to_mongodb(f"Translated text to {language} completed", context, "INFO")

                translated_summary = self._translate_text(summary, language)
                translated_summaries[language] = translated_summary
                self._log_to_mongodb(f"Translated summary to {language} completed", context, "INFO")

        # Update the translations in the MongoDB document
        self._update_translations_in_mongodb(context, meeting_id, translated_texts, translated_summaries)
        self._log_to_mongodb(f"Updated translations in MongoDB for meeting_id: {meeting_id}", context, "INFO")

        return {"meeting_id": str(meeting_id)}
        
