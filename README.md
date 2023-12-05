# TalkTracerAI - 🌟 Empowering Productivity Through Meeting Insight. 📈💡

<img width="300px" align="left" src="./doc/logo.PNG" />

Welcome to TalkTracerAI, an innovative solution aimed at enhancing productivity by providing comprehensive insights from meeting conversations. With TalkTracerAI, gain a deeper understanding of your discussions, extract meaningful information, and unlock valuable data-driven insights from meetings. 🚀🔍

At TalkTracerAI, we take your meeting words and turn them into powerful insights. We help you see what's really going on behind the scenes. It's like having a magic decoder for meetings that shows you the important bits. From knowing how people feel to finding the 'aha!' moments, TalkTracerAI helps you get the most out of every meeting.

With TalkTracerAI, your meetings turn into smart resources that drive better decisions and fuel growth!

<p align="center">
  <img src="https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/Apache%20Airflow-017CEE?style=for-the-badge&logo=Apache%20Airflow&logoColor=white" />
  <img src="https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white" />
  <img src="https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" />
  <img src="https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white" />
  <img src="https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Elastic_Search-005571?style=for-the-badge&logo=elasticsearch&logoColor=white" />
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" />
  <img src="https://tinyurl.com/2p9ft7xf" />
</p>

## What is TalkTracerAI? 🌐

TalkTracerAI is an intelligent tool designed to transcribe, analyze, and summarize meeting conversations using cutting-edge Natural Language Processing (NLP) techniques. It empowers users to effortlessly extract key phrases, identify crucial entities, translate discussions into multiple languages, and generate concise summaries, offering a clear and comprehensive view of meeting outcomes. 💬📊

## Key Features: 🎯

- **Transcription:** Seamlessly transcribe audio recordings into textual data for further analysis. 🎤🔤
- **Natural Language Processing (NLP):** Extract key phrases and named entities to derive deeper insights from the conversation content. 🧠📝
- **Translation:** Translate meeting transcripts into various languages, facilitating global collaboration and understanding. 🌎🌐
- **Summarization:** Generate concise summaries to capture the essence of discussions efficiently. 📝✨

## Technologies Used

- **Python 🐍:** Used as the primary programming language for the development of various components, including backend services, data processing, and machine learning implementations.
- **Elasticsearch 🔍:** Utilized to index the text of processed meetings with NLP (Natural Language Processing), enabling precise searches by key terms.
- **Apache Airflow 🛠️:** Implemented to orchestrate the ETL DAG (Directed Acyclic Graph) that processes meetings. This DAG handles transcription, NLP, obtaining summaries of the transcription, translations, and indexing through automated workflows. It uses PostgreSQL as the database engine to store DAG metadata and other necessary information for its proper functioning.
- **Flask 📡:** Chosen as the web microframework to build the backend server and RESTful APIs for TalkTrackerAI, ensuring lightweight and efficient development. HAProxy is used to implement load balancing patterns between multiple MinIO instances and the Flask services of the API.
- **MongoDB 📊:** Used to store and model meetings as BSON documents, providing flexibility in data structure and storage.
- **MinIO 🗄️:** Employed to store meeting audio files, offering high-performance and scalable object storage. HAProxy is also responsible for implementing load balancing patterns for multiple MinIO instances.
- **HAProxy 🔄:** Used both to implement load balancing patterns between multiple MinIO instances and for the Flask services of the TalkTrackerAI API, ensuring system availability and performance.
- **Redis 📦:** Employed as an in-memory data structure store for caching, optimizing data retrieval, and improving system performance.
- **Celery Flower 🌸:** Utilized as a real-time monitoring tool for Celery, providing a web-based user interface to monitor and manage Celery clusters.
- **PostgreSQL 🐘:** Used as the primary relational database for structured data storage and management, ensuring robustness and reliability in Apache Airflow.
- **Fine-Tuned T5 Small for Text Summarization (Hugging Face Model) 🤖:** Leveraged for text summarization tasks, the "t5-small" model, fine-tuned for generating concise and coherent summaries of input text using PyTorch.
- **PyTorch 🧠:** Employed as the deep learning framework to fine-tune the "t5-small" model for text summarization tasks.
- **scikit-learn 🧬:** Utilized for machine learning tasks such as classification, regression, and clustering, offering a wide array of algorithms and tools.
- **spaCy 🛠️:** Employed for advanced NLP tasks such as entity recognition, tokenization, and linguistic annotations, providing a streamlined and efficient framework.
- **vaderSentiment 📈:** Utilized for sentiment analysis tasks, offering a pre-trained model for evaluating the sentiment of text data, especially useful for social media analysis and opinion mining.

## How TalkTracerAI Works: ⚙️

TalkTracerAI leverages state-of-the-art NLP models and cloud-based storage to efficiently process audio recordings, extract crucial information, and deliver insightful summaries. It seamlessly integrates with MongoDB for data storage and retrieval and employs MinIO for cloud-based file storage, ensuring secure and scalable handling of meeting data.

**Empower your meetings with TalkTracerAI and transform the way you derive insights from discussions!** 🌟✨
