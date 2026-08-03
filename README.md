# RAG Document Q&A ("Chat with your Documents")

A full-stack **Retrieval-Augmented Generation** app: upload PDFs/DOCX/TXT,
and ask questions to get answers **with cited sources**. Retrieval uses a
**scikit-learn TF-IDF** vector store. Answers are
**extractive by default** (no API key needed) and can optionally be
**LLM-generated** when an API key is provided.
