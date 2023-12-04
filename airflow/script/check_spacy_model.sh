#!/bin/bash

echo "Checking spaCy model..."
python -c "import spacy; nlp = spacy.load('en_core_web_sm')" || { echo "Failed to load spaCy model"; exit 1; }
echo "spaCy model loaded successfully"
