from collections import Counter
from bson import ObjectId
from operators.base_custom_operator import BaseCustomOperator
from airflow.utils.decorators import apply_defaults
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class NaturalLanguageProccessingOperator(BaseCustomOperator):
    """
        This operator executes Natural Language Processing tasks including the extraction of key phrases,
        named entities, and frequent expressions from meeting transcriptions.
    """
    @apply_defaults
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _analyze_sentiment(self, text):
        """
        Analyzes sentiment using VADER SentimentIntensityAnalyzer.

        Args:
        - text: The text to analyze sentiment for.

        Returns:
        A dictionary containing sentiment scores.
        """
        analyzer = SentimentIntensityAnalyzer()
        sentiment_scores = analyzer.polarity_scores(text)
        return sentiment_scores

    def _extract_sentiment_phrases(self, nlp, text, num_phrases):
        """
        Extracts the most positive and most negative phrases from the text.

        Args:
        - nlp: The spaCy natural language processing pipeline.
        - text: The input text to extract sentiment phrases from.
        - num_phrases: The number of positive/negative phrases to extract.

        Returns:
        A tuple containing lists of the most positive and most negative phrases.
        """
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        sentiment_scores = [self._analyze_sentiment(sentence)['compound'] for sentence in sentences]
        sorted_indices = np.argsort(sentiment_scores)

        most_positive_phrases = [sentences[i] for i in sorted_indices[-num_phrases:]]
        most_negative_phrases = [sentences[i] for i in sorted_indices[:num_phrases]]

        return most_positive_phrases, most_negative_phrases

    def _extract_most_frequent_expressions(self, nlp, text):
        """
        Extracts most frequent expressions using CountVectorizer.

        Args:
        - nlp: The spaCy natural language processing pipeline.
        - text: The input text to extract frequent expressions from.

        Returns:
        A list of most frequent expressions extracted using CountVectorizer.
        """
        # Process the text
        doc = nlp(text)
        # Get the nouns and adjectives from the document
        nouns_adjs = [token.text for token in doc if token.pos_ in ('NOUN', 'PROPN', 'ADJ')]
        # Use CountVectorizer to find the most frequent expressions
        vectorizer = CountVectorizer(ngram_range=(1, 2))
        X = vectorizer.fit_transform(nouns_adjs)
        vocab = vectorizer.get_feature_names_out()
        word_freq = Counter(dict(zip(vocab, np.asarray(X.sum(axis=0)).ravel())))
        most_common_words = word_freq.most_common(5)

        return [word[0] for word in most_common_words]


    def _extract_key_phrases(self, nlp, text):
        """
        Extracts key phrases from the provided text using TF-IDF scoring.

        Args:
        - nlp: The spaCy natural language processing pipeline.
        - text: The input text to extract key phrases from.

        Returns:
        A list of key phrases extracted based on TF-IDF scoring.
        """
        # Process the text
        doc = nlp(text)

        # Get the sentences from the document
        sentences = [sent.text for sent in doc.sents]

        # Calculate TF-IDF for the sentences
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(sentences)

        # Calculate TF-IDF scores per sentence
        sentence_scores = tfidf_matrix.sum(axis=1).A1

        # Get the indices of sentences ordered by their TF-IDF score
        top_sentence_indices = sentence_scores.argsort()[::-1][:5]  # Get only the top 3 most important sentences

        # Get the most important key phrases (highest TF-IDF score sentences)
        key_phrases = [sentences[i] for i in top_sentence_indices]

        return key_phrases
    
    def _extract_named_entities(self, nlp, text):
        """
        Extracts Named Entities Recognition (NER) from the provided text.

        Args:
        - nlp: The spaCy natural language processing pipeline.
        - text: The input text to extract NER from.

        Returns:
        A list of dictionaries containing information about recognized entities.
        """
        # Process the text
        doc = nlp(text)

        # Extract named entities
        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
                "label": ent.label_
            })

        return entities


    def _update_nlp_results_in_mongodb(self, context, meeting_id, key_phrases, named_entities, frequent_expressions, most_positive, most_negative):
        """
        Updates the MongoDB document with extracted Named Entities, Key Phrases, Frequent Expressions,
        Most Positive Phrases, and Most Negative Phrases.

        Args:
        - context: The execution context.
        - meeting_id: The ID of the meeting/document in MongoDB.
        - key_phrases: List of key phrases to be updated in the MongoDB document.
        - named_entities: List of named entities to be updated in the MongoDB document.
        - frequent_expressions: List of frequent expressions to be updated in the MongoDB document.
        - most_positive: List of most positive phrases to be updated in the MongoDB document.
        - most_negative: List of most negative phrases to be updated in the MongoDB document.
        """
        collection = self._get_mongodb_collection()
        update_result = collection.update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {
                "key_phrases": key_phrases,
                "named_entities": named_entities,
                "frequent_expressions": frequent_expressions,
                "most_positive_phrases": most_positive,
                "most_negative_phrases": most_negative
            }}
        )

        if update_result.modified_count == 1:
            self._log_to_mongodb(f"Updated document with meeting_id {meeting_id} in MongoDB", context, "INFO")
        else:
            error_message = f"Document with meeting_id {meeting_id} not updated in MongoDB"
            self._log_to_mongodb(error_message, context, "WARNING")
            raise Exception(error_message)

    def execute(self, context):
        self._log_to_mongodb(f"Starting execution of NaturalLanguageProccessingOperator", context, "INFO")
        
        # Get the meeting_id from the configuration
        meeting_id = context['dag_run'].conf.get('meeting_id')
        self._log_to_mongodb(f"Received meeting_id: {meeting_id}", context, "INFO")

        meeting_info = self._get_meeting_info(context, meeting_id)
        self._log_to_mongodb(f"Retrieved meeting from MongoDB: {meeting_id}", context, "INFO")

        transcribed_text = self._get_transcribed_text_from_meeting_info(context, meeting_info)

        nlp = self._load_spacy_model()
        
        # Extract key phrases using TF-IDF
        self._log_to_mongodb("Extracting key phrases using TF-IDF...", context, "INFO")
        key_phrases = self._extract_key_phrases(nlp, transcribed_text)

        # Extract Named Entities using spaCy
        self._log_to_mongodb("Extracting Named Entities using spaCy...", context, "INFO")
        named_entities = self._extract_named_entities(nlp, transcribed_text)

        # Extract most frequent expressions using CountVectorizer
        self._log_to_mongodb("Extracting most frequent expressions...", context, "INFO")
        frequent_expressions = self._extract_most_frequent_expressions(nlp, transcribed_text)

          # Extract sentiment phrases using VADER Sentiment
        self._log_to_mongodb("Extracting sentiment phrases...", context, "INFO")
        most_positive, most_negative = self._extract_sentiment_phrases(nlp, transcribed_text, num_phrases=3)

        # Update Named Entities and Key Phrases in MongoDB document
        self._log_to_mongodb("Updating NLP results in MongoDB document...", context, "INFO")
        self._update_nlp_results_in_mongodb(context, meeting_id, key_phrases, named_entities, frequent_expressions, most_positive, most_negative)

        self._log_to_mongodb("Execution of NaturalLanguageProccessingOperator completed.", context, "INFO")

        return {"meeting_id": str(meeting_id)}
